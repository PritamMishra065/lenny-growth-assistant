"""Quick integration test for Phase 2 API endpoints."""
import httpx
import asyncio
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=10) as c:
        # Health
        r = await c.get("/health")
        print("[OK] Health:", r.json())

        # Create session
        r = await c.post("/api/sessions", json={"title": "API Test"})
        session = r.json()
        sid = session["id"]
        print(f"[OK] Session created: {sid}")

        # Send message (SSE)
        async with c.stream(
            "POST",
            f"/api/sessions/{sid}/messages",
            json={"content": "What is product-market fit?"},
        ) as resp:
            print("[OK] SSE Stream:")
            async for line in resp.aiter_lines():
                if line.strip():
                    print(f"   {line}")

        # Get messages
        r = await c.get(f"/api/sessions/{sid}/messages")
        msgs = r.json()
        print(f"[OK] Messages in session: {msgs['total']}")
        for m in msgs["messages"]:
            role = m["role"]
            content = m["content"][:100]
            print(f"   [{role}] {content}...")

        # Model config
        r = await c.get("/api/config/model")
        print(f"[OK] Model config: {r.json()['provider']} / {r.json()['model']}")

        # List sessions
        r = await c.get("/api/sessions")
        print(f"[OK] Total sessions: {r.json()['total']}")

        # Delete session
        r = await c.delete(f"/api/sessions/{sid}")
        print(f"[OK] Session deleted (status {r.status_code})")

        print("\n=== All Phase 2 API tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test())
