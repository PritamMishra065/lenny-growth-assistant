"""
Ship 30 for 30 Content Skill.
Generates structured, ~1,250-word essays following Ship 30 for 30 digital writing principles:
- Strong, irresistible hook
- Clear narrative progression
- High-contrast, skimmable formatting (headers, bullet points, bolding)
- Specific, actionable takeaways
- Grounded strictly in Lenny's Podcast transcripts
"""

from typing import AsyncGenerator
from app.services.retrieval import search_transcripts, format_context_for_llm, format_sources_for_response
from app.services.llm import stream_completion
import structlog

logger = structlog.get_logger()

SHIP30_SYSTEM_PROMPT = """You are an expert digital writer trained in the "Ship 30 for 30" writing methodology by Nicolas Cole and Dickie Bush.

Your mission is to turn product, growth, and leadership insights from Lenny's Podcast transcripts into a world-class, ~1,250-word Atomic Essay / Long-form Guide.

Core Ship 30 for 30 Writing Principles to apply:
1. **The Hook (First 3 Lines)**: Start with a provocative, high-intrigue opening line that grabs attention immediately. Challenge conventional wisdom or state a surprising truth.
2. **Clear Narrative Arc**:
   - Problem / Tension (Why the old way fails)
   - Core Epiphany / Mental Model
   - 3 to 4 Deep-Dive Pillars / Frameworks (with real examples from the podcast guests)
   - Actionable Implementation Checklist
   - Inspiring Conclusion / Golden Rule
3. **Skimmable Formatting (Visual Cadence)**:
   - Use punchy one-sentence paragraphs for rhythm.
   - Use bold emphasis on key phrases and takeaways.
   - Use clear H2 and H3 markdown headers.
   - Use bullet points and numbered lists for rapid comprehension.
   - Avoid walls of text (never more than 3 sentences per paragraph).
4. **Deep Grounding**: Attribute specific frameworks and stories to the podcast guests (e.g. Brian Chesky, Marty Cagan, Elena Verna, etc.) using the provided transcript excerpts.
5. **Length**: Deliver a comprehensive, deeply practical piece of approximately 1,200 to 1,300 words.
"""


async def execute_ship30_skill(
    user_query: str,
    history: list[dict],
) -> AsyncGenerator[dict, None]:
    """
    Execute the Ship 30 for 30 essay skill:
    1. Retrieve relevant transcript knowledge.
    2. Stream essay content.
    3. Package complete essay as an artifact.
    """
    retrieved_chunks = await search_transcripts(user_query, top_k=6)
    sources = format_sources_for_response(retrieved_chunks)
    context_text = format_context_for_llm(retrieved_chunks)

    yield {"type": "sources", "sources": sources}

    prompt = (
        f"Transcript Knowledge Base:\n"
        f"========================\n"
        f"{context_text}\n"
        f"========================\n\n"
        f"User Topic / Request: {user_query}\n\n"
        f"Write a comprehensive ~1,250-word Ship 30 for 30 style essay that transforms these transcript insights into an actionable, beautifully structured guide."
    )

    full_essay = ""
    async for token in stream_completion(
        [{"role": "user", "content": prompt}],
        system_prompt=SHIP30_SYSTEM_PROMPT,
    ):
        full_essay += token
        yield {"type": "text", "content": token}

    # Extract title or default
    first_line = full_essay.strip().split("\n")[0].replace("#", "").strip()
    title = first_line if len(first_line) < 80 else "Ship 30 for 30 Essay"

    # Emit artifact event so frontend renders it in the Artifact Viewer
    yield {
        "type": "artifact",
        "artifact": {
            "type": "markdown",
            "title": title,
            "content": full_essay,
        },
    }
