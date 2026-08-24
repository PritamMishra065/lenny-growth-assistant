import asyncio
import sys
import os
import io
import httpx

# Fix Windows encoding and pythonpath
sys.path.insert(0, os.path.abspath("."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as client:
        print("=== 1. Testing Available Episodes ===")
        r = await client.get("/api/ingestion/episodes")
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        total_episodes = data["total"]
        print(f"[OK] Total available episodes found: {total_episodes}")
        first_few = [f"{e['guest']} ({e['slug']})" for e in data["episodes"][:5]]
        print(f"     Sample episodes: {', '.join(first_few)}")

        print("\n=== 2. Testing Selective Ingestion (2 episodes: brian-chesky, marty-cagan) ===")
        r = await client.post("/api/ingestion/ingest", json={"slugs": ["brian-chesky", "marty-cagan"]})
        assert r.status_code == 200, f"Failed: {r.text}"
        ingest_res = r.json()
        print(f"[OK] Ingestion result: {ingest_res}")

        print("\n=== 3. Testing Ingestion Status ===")
        r = await client.get("/api/ingestion/status")
        assert r.status_code == 200
        status_data = r.json()
        print(f"[OK] Ingestion status: {status_data}")

        print("\n=== 4. Testing Retrieval Service ===")
        from app.services.retrieval import search_transcripts, format_sources_for_response

        query = "What does Brian Chesky say about being in the details and micromanagement?"
        print(f"Query: '{query}'")
        results = await search_transcripts(query, top_k=3)
        print(f"[OK] Retrieved {len(results)} chunks.")
        for i, res in enumerate(results, 1):
            print(f"\n--- Result {i} (Similarity: {res['similarity']}, Guest: {res['guest']}, Episode: {res['episode']}) ---")
            print(f"Excerpt: {res['content'][:250]}...")

        sources = format_sources_for_response(results)
        print(f"\n[OK] Formatted sources count: {len(sources)}")
        for s in sources:
            print(f"     * Episode: {s['episode']} | Guest: {s['guest']} | URL: {s['url']}")

        print("\n=== All Phase 3 tests passed successfully! ===")


if __name__ == "__main__":
    asyncio.run(test())
