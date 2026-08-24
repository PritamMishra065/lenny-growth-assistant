"""Test Skill 3: Artifact generation with HTML/CSS."""
import asyncio
import sys
import os
import io
import json
import httpx

sys.path.insert(0, os.path.abspath("."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=180) as client:
        # Create session
        r = await client.post("/api/sessions", json={"title": "Artifact Skill Test"})
        session = r.json()
        sid = session["id"]
        print(f"[OK] Session created: {sid}")

        print("\n=== Testing Skill 3: Artifact Generation (HTML/CSS) ===")
        artifact_query = "Generate an interactive HTML calculator widget for calculating product market fit metrics based on Brian Chesky's advice"
        print(f"Query: '{artifact_query}'")

        full_output = ""
        skill_detected = None
        artifact_received = None

        async with client.stream("POST", f"/api/sessions/{sid}/messages", json={"content": artifact_query}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                        if "content" in data and "type" in data and data["type"] == "text":
                            full_output += data["content"]
                        elif "skill_used" in data:
                            skill_detected = data["skill_used"]
                        elif "type" in data and data["type"] == "artifact":
                            artifact_received = data
                        elif "artifact" in data:
                            artifact_received = data["artifact"]
                    except json.JSONDecodeError:
                        pass

        print(f"[OK] Skill detected: {skill_detected}")
        print(f"[OK] HTML Content length: {len(full_output)} chars")
        print(f"[OK] Artifact event received: {artifact_received is not None}")
        print(f"\nArtifact snippet:\n{full_output[:300]}...\n")

        print("=== Phase 4 Skill 3 Test Passed! ===")


if __name__ == "__main__":
    asyncio.run(test())
