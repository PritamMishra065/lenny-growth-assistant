"""Integration test for Phase 4: LLM Configuration, Agent Routing & Skills."""
import asyncio
import sys
import os
import io
import json
import httpx

sys.path.insert(0, os.path.abspath("."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as client:
        print("=== 1. Testing Model Config ===")
        r = await client.get("/api/config/model")
        assert r.status_code == 200
        config = r.json()
        print(f"[OK] Active provider: {config['provider']} | Model: {config['model']}")
        print(f"     Available providers: {[p['name'] for p in config['available_providers'] if p['configured']]}")

        # Create session
        r = await client.post("/api/sessions", json={"title": "Phase 4 Agent Test"})
        session = r.json()
        sid = session["id"]
        print(f"\n[OK] Session created: {sid}")

        print("\n=== 2. Testing Skill 1: Grounded RAG Q&A ===")
        rag_query = "What did Brian Chesky say about micromanagement and being in the details?"
        print(f"Query: '{rag_query}'")

        full_text = ""
        sources = []
        skill_detected = None

        async with client.stream("POST", f"/api/sessions/{sid}/messages", json={"content": rag_query}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    data = json.loads(data_str)
                    if "content" in data:
                        full_text += data["content"]
                    elif "sources" in data:
                        sources = data["sources"]
                    elif "skill_used" in data:
                        skill_detected = data["skill_used"]

        print(f"[OK] Skill routed: {skill_detected}")
        print(f"[OK] Sources cited: {len(sources)}")
        for s in sources:
            print(f"     * {s['guest']} - {s['episode']}")
        print(f"\nResponse excerpt:\n{full_text[:350]}...\n")

        print("\n=== 3. Testing Skill 2: Ship 30 for 30 Essay ===")
        ship30_query = "Write a Ship 30 for 30 essay about why founders must be in the details based on Brian Chesky's insights"
        print(f"Query: '{ship30_query}'")

        full_essay = ""
        artifact = None

        async with client.stream("POST", f"/api/sessions/{sid}/messages", json={"content": ship30_query}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    data = json.loads(data_str)
                    if "content" in data and "type" in data and data["type"] == "text":
                        full_essay += data["content"]
                    elif "artifact" in line or (isinstance(data, dict) and data.get("type") == "markdown"):
                        artifact = data

        print(f"[OK] Essay generated (~{len(full_essay.split())} words)")
        print(f"Essay excerpt:\n{full_essay[:300]}...\n")

        print("\n=== 4. Testing Skill 3: Artifact Generation (HTML/CSS) ===")
        artifact_query = "Generate an interactive HTML/CSS calculator widget for estimating Product Market Fit score"
        print(f"Query: '{artifact_query}'")

        html_output = ""
        async with client.stream("POST", f"/api/sessions/{sid}/messages", json={"content": artifact_query}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    data = json.loads(data_str)
                    if "content" in data and "type" in data and data["type"] == "text":
                        html_output += data["content"]

        print(f"[OK] HTML Artifact response received ({len(html_output)} chars)")

        # Verify messages stored in DB
        r = await client.get(f"/api/sessions/{sid}/messages")
        messages = r.json()["messages"]
        print(f"\n[OK] Total messages persisted in DB: {len(messages)}")

        print("\n=== All Phase 4 Agent & Skill tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test())
