"""
Artifact Generation Skill.
Generates complete Markdown documents or HTML/CSS snippets grounded in podcast insights.
Emits artifact events for the frontend Artifact Viewer.
"""

from typing import AsyncGenerator
import re
from app.services.retrieval import search_transcripts, format_context_for_llm, format_sources_for_response
from app.services.llm import stream_completion
import structlog

logger = structlog.get_logger()

ARTIFACT_SYSTEM_PROMPT = """You are an expert product artifact architect and designer.
Your mission is to generate comprehensive, production-grade artifacts grounded in Lenny's Podcast insights.

Types of artifacts you can produce:
1. **Markdown Documents**: Comprehensive PRDs, Strategy Memos, Growth Framework Playbooks, Onboarding Teardown Checklists, KPI Scorecards, or Job Descriptions.
2. **HTML/CSS Components**: Interactive calculators (e.g., CAC/LTV calculator, North Star metric tree), interactive dashboard mockups, or clean UI components styled with modern, responsive CSS.

Guidelines:
- Return the full, complete document or component without placeholders.
- If generating HTML, include embedded `<style>` tags with modern dark/light styling, clean typography, and zero external script dependencies.
- Ground all metrics, benchmarks, and advice in the provided podcast transcript excerpts.
"""


async def execute_artifact_skill(
    user_query: str,
    history: list[dict],
) -> AsyncGenerator[dict, None]:
    """
    Execute artifact generation skill:
    1. Retrieve transcript context.
    2. Determine if user wants HTML/CSS or Markdown.
    3. Stream generation.
    4. Package final artifact for the viewer.
    """
    retrieved_chunks = await search_transcripts(user_query, top_k=5)
    sources = format_sources_for_response(retrieved_chunks)
    context_text = format_context_for_llm(retrieved_chunks)

    yield {"type": "sources", "sources": sources}

    is_html_requested = any(kw in user_query.lower() for kw in ["html", "css", "interactive", "calculator", "widget", "web component"])
    artifact_type = "html" if is_html_requested else "markdown"

    prompt = (
        f"Transcript Knowledge:\n"
        f"===================\n"
        f"{context_text}\n"
        f"===================\n\n"
        f"User Request: {user_query}\n\n"
        f"Generate a complete, high-quality {artifact_type.upper()} artifact based on the above transcript insights. "
    )

    if artifact_type == "html":
        prompt += "Provide complete, self-contained HTML with embedded <style> styling. Do not include external JS scripts."

    full_output = ""
    async for token in stream_completion(
        [{"role": "user", "content": prompt}],
        system_prompt=ARTIFACT_SYSTEM_PROMPT,
    ):
        full_output += token
        yield {"type": "text", "content": token}

    # Clean up artifact content (strip markdown code fences if wrapped in ```html ... ```)
    clean_content = full_output.strip()
    if artifact_type == "html" and "```html" in clean_content:
        match = re.search(r"```html\s*(.*?)\s*```", clean_content, re.DOTALL)
        if match:
            clean_content = match.group(1)

    title_match = re.search(r"^#\s+(.+)$", full_output, re.MULTILINE)
    title = title_match.group(1) if title_match else f"{'Interactive ' if is_html_requested else ''}Product Artifact"

    yield {
        "type": "artifact",
        "artifact": {
            "type": artifact_type,
            "title": title,
            "content": clean_content,
        },
    }
