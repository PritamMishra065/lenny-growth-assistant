"""
Transcript ingestion service.
Loads markdown transcripts, chunks them, generates embeddings via Ollama,
and stores them in ChromaDB.
Supports selective ingestion — user chooses which episodes to ingest.
"""

import os
import re
import yaml
import hashlib
from pathlib import Path
from typing import Optional
import httpx
import chromadb
import structlog

from app.config import settings

logger = structlog.get_logger()

# Root directory of the project
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR) if os.path.basename(BACKEND_DIR) == "backend" else BACKEND_DIR

CHROMA_DIR = os.path.join(PROJECT_ROOT, "data", "chroma")
COLLECTION_NAME = "lenny_transcripts"
TRANSCRIPTS_DIR = os.path.join(PROJECT_ROOT, "data", "transcripts-repo", "episodes")


def get_chroma_client():
    """Get or create ChromaDB persistent client."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection():
    """Get or create the transcripts collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def list_available_episodes() -> list[dict]:
    """List all available episodes from the transcripts directory."""
    if not os.path.exists(TRANSCRIPTS_DIR):
        return []

    episodes = []
    for episode_dir in sorted(Path(TRANSCRIPTS_DIR).iterdir()):
        if not episode_dir.is_dir():
            continue
        md_files = list(episode_dir.glob("*.md"))
        if not md_files:
            continue

        # Quick-parse frontmatter for listing
        transcript = parse_transcript(str(md_files[0]))
        if transcript:
            episodes.append({
                "slug": episode_dir.name,
                "guest": transcript["guest"],
                "title": transcript["title"],
                "date": transcript["date"],
                "url": transcript["url"],
            })

    return episodes


def parse_transcript(file_path: str) -> Optional[dict]:
    """Parse a markdown transcript file with YAML frontmatter."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Split YAML frontmatter from content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
            else:
                frontmatter = {}
                body = content
        else:
            frontmatter = {}
            body = content

        return {
            "guest": frontmatter.get("guest", "Unknown"),
            "title": frontmatter.get("title", os.path.basename(file_path)),
            "date": str(frontmatter.get("publish_date", "")),
            "url": frontmatter.get("youtube_url", ""),
            "keywords": frontmatter.get("keywords", []),
            "description": frontmatter.get("description", ""),
            "duration": frontmatter.get("duration", ""),
            "body": body,
        }
    except Exception as e:
        logger.error("parse_transcript_failed", file=file_path, error=str(e))
        return None


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """
    Split text into chunks with overlap.
    Uses paragraph boundaries for more natural splits.
    """
    paragraphs = re.split(r'\n\n+', text)

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts in batch via Ollama."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/embed",
            json={
                "model": settings.EMBEDDING_MODEL,
                "input": texts,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embeddings", [])


async def ingest_episodes(slugs: list[str] = None, ingest_all: bool = False) -> dict:
    """
    Ingest selected episodes by slug, or all if ingest_all=True.
    
    Args:
        slugs: List of episode directory names (e.g., ["brian-chesky", "marty-cagan"])
        ingest_all: If True, ingest all available episodes
    
    Returns:
        Stats dict with episodes processed, chunks created, and errors.
    """
    if not os.path.exists(TRANSCRIPTS_DIR):
        return {"status": "error", "message": f"Directory not found: {TRANSCRIPTS_DIR}"}

    collection = get_collection()
    stats = {"episodes": 0, "chunks": 0, "errors": 0, "skipped": 0}

    # Determine which episodes to process
    if ingest_all:
        episode_dirs = [d for d in sorted(Path(TRANSCRIPTS_DIR).iterdir()) if d.is_dir()]
    elif slugs:
        episode_dirs = []
        for slug in slugs:
            ep_dir = Path(TRANSCRIPTS_DIR) / slug
            if ep_dir.exists() and ep_dir.is_dir():
                episode_dirs.append(ep_dir)
            else:
                logger.warning("episode_not_found", slug=slug)
                stats["errors"] += 1
    else:
        return {"status": "error", "message": "Provide slugs or set ingest_all=True"}

    logger.info("ingestion_starting", total_episodes=len(episode_dirs))

    batch_size = 20
    all_ids = []
    all_documents = []
    all_metadatas = []

    for episode_dir in episode_dirs:
        md_files = list(episode_dir.glob("*.md"))
        if not md_files:
            continue

        transcript = parse_transcript(str(md_files[0]))
        if not transcript:
            stats["errors"] += 1
            continue

        # Check if this episode is already ingested
        slug = episode_dir.name
        existing = collection.get(where={"source_file": slug})
        if existing and len(existing["ids"]) > 0:
            stats["skipped"] += 1
            logger.info("episode_already_ingested", slug=slug)
            continue

        chunks = chunk_text(transcript["body"])
        if not chunks:
            continue

        stats["episodes"] += 1

        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{slug}:{i}".encode()).hexdigest()

            metadata = {
                "episode": transcript["title"],
                "guest": transcript["guest"],
                "date": transcript["date"],
                "url": transcript["url"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_file": slug,
            }

            all_ids.append(chunk_id)
            all_documents.append(chunk)
            all_metadatas.append(metadata)

    if not all_documents:
        msg = "No new episodes to ingest"
        if stats["skipped"] > 0:
            msg += f" ({stats['skipped']} already ingested)"
        return {"status": "complete", "message": msg, **stats}

    # Generate embeddings in batches
    logger.info("generating_embeddings", total_chunks=len(all_documents))

    for i in range(0, len(all_documents), batch_size):
        batch_docs = all_documents[i:i + batch_size]
        batch_ids = all_ids[i:i + batch_size]
        batch_metas = all_metadatas[i:i + batch_size]

        try:
            embeddings = await get_embeddings_batch(batch_docs)

            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=embeddings,
            )

            stats["chunks"] += len(batch_docs)

            if (i // batch_size) % 5 == 0:
                logger.info(
                    "ingestion_progress",
                    chunks_done=stats["chunks"],
                    total=len(all_documents),
                    pct=round(stats["chunks"] / len(all_documents) * 100, 1),
                )
        except Exception as e:
            logger.error("embedding_batch_failed", batch_start=i, error=str(e))
            stats["errors"] += 1

    logger.info("ingestion_complete", **stats)
    return {"status": "complete", **stats}


def check_ingestion_status() -> dict:
    """Check ingestion status — how many chunks and which episodes are ingested."""
    try:
        collection = get_collection()
        count = collection.count()

        # Get unique episodes
        if count > 0:
            # Sample to get episode list
            results = collection.get(limit=count, include=["metadatas"])
            episodes = set()
            for meta in results["metadatas"]:
                episodes.add(meta.get("source_file", "unknown"))
            return {"ingested": True, "chunks": count, "episodes": len(episodes), "episode_slugs": sorted(list(episodes))}

        return {"ingested": False, "chunks": 0, "episodes": 0, "episode_slugs": []}
    except Exception:
        return {"ingested": False, "chunks": 0, "episodes": 0, "episode_slugs": []}


def clear_collection():
    """Delete all data from the collection (re-ingest from scratch)."""
    try:
        client = get_chroma_client()
        client.delete_collection(COLLECTION_NAME)
        logger.info("collection_cleared")
        return {"status": "cleared"}
    except Exception as e:
        logger.error("clear_collection_failed", error=str(e))
        return {"status": "error", "message": str(e)}
