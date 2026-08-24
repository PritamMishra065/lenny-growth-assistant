"""
Retrieval service — vector search over ingested transcripts.
"""

import structlog
from app.services.ingestion import get_collection, get_embeddings_batch

logger = structlog.get_logger()


async def search_transcripts(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the transcript collection for relevant chunks.
    
    Args:
        query: The user's question
        top_k: Number of results to return
    
    Returns:
        List of dicts with content, metadata, and relevance score.
    """
    collection = get_collection()
    
    if collection.count() == 0:
        logger.warning("search_on_empty_collection")
        return []

    try:
        # Get embedding for the query
        embeddings = await get_embeddings_batch([query])
        if not embeddings:
            logger.error("query_embedding_failed")
            return []

        # Search ChromaDB
        results = collection.query(
            query_embeddings=[embeddings[0]],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score (1 = identical, 0 = orthogonal)
            similarity = 1 - (distance / 2)

            formatted.append({
                "content": results["documents"][0][i],
                "episode": meta.get("episode", ""),
                "guest": meta.get("guest", ""),
                "date": meta.get("date", ""),
                "url": meta.get("url", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "source_file": meta.get("source_file", ""),
                "similarity": round(similarity, 4),
            })

        logger.info(
            "retrieval_complete",
            query_preview=query[:80],
            results=len(formatted),
            top_similarity=formatted[0]["similarity"] if formatted else 0,
        )

        return formatted

    except Exception as e:
        logger.error("retrieval_failed", error=str(e), query=query[:80])
        return []


def format_sources_for_response(results: list[dict]) -> list[dict]:
    """Format retrieval results as source citations for the API response."""
    sources = []
    seen = set()

    for r in results:
        # Deduplicate by episode
        episode_key = r["episode"]
        if episode_key in seen:
            continue
        seen.add(episode_key)

        sources.append({
            "episode": r["episode"],
            "guest": r["guest"],
            "url": r["url"],
            "excerpt": r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
        })

    return sources


def format_context_for_llm(results: list[dict]) -> str:
    """Format retrieval results as context for the LLM prompt."""
    if not results:
        return "No relevant transcript excerpts found."

    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(
            f"[Source {i}] Episode: \"{r['episode']}\" | Guest: {r['guest']} | Date: {r['date']}\n"
            f"{r['content']}"
        )

    return "\n\n---\n\n".join(context_parts)
