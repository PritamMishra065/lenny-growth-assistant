"""
RAG Conversational Skill.
Answers product and growth questions strictly grounded in Lenny's Podcast transcripts.
"""

from typing import AsyncGenerator
from app.services.retrieval import search_transcripts, format_context_for_llm, format_sources_for_response
from app.services.llm import stream_completion
import structlog

logger = structlog.get_logger()

RAG_SYSTEM_PROMPT = """You are "The Lenny Growth Assistant," an expert product and growth advisor with deep knowledge of product management, growth loops, go-to-market strategies, leadership, and startup building.

Your responses MUST be strictly grounded in the provided excerpts from Lenny's Podcast transcripts.

Guidelines:
1. **Source Grounding**: Base all claims, frameworks, metrics, and advice strictly on the provided transcript context. Quote or reference the guest (e.g. "According to Brian Chesky...", "As Marty Cagan pointed out...").
2. **Clear & Actionable**: Provide structured, high-value, skimmable answers using headings, bullet points, and bold text.
3. **Honesty & Fallback**: If the provided transcript excerpts do not contain enough information to answer the question accurately, explicitly state: "Based on the available Lenny's Podcast transcripts, I don't have enough specific information to answer that question comprehensively," and summarize what related insights (if any) are present.
4. **Follow-ups & Continuity**: Maintain awareness of the conversation history to answer follow-up questions smoothly.
5. **No Hallucination**: Do NOT fabricate guest names, episodes, company stories, or frameworks not supported by the context.
"""


async def execute_rag_skill(
    user_query: str,
    history: list[dict],
) -> AsyncGenerator[dict, None]:
    """
    Execute the RAG skill:
    1. Retrieve relevant transcript chunks.
    2. Yield the sources immediately.
    3. Construct grounded prompt with conversation history.
    4. Stream generated response tokens.
    """
    # 1. Retrieve relevant context
    retrieved_chunks = await search_transcripts(user_query, top_k=5)
    sources = format_sources_for_response(retrieved_chunks)
    context_text = format_context_for_llm(retrieved_chunks)

    # Yield sources event so UI can display citations
    yield {"type": "sources", "sources": sources}

    # 2. Build conversation context for LLM
    llm_messages = []

    # Include recent history (excluding system messages)
    for msg in history[-6:]:  # Last 3 turns
        if msg["role"] in ["user", "assistant"]:
            llm_messages.append({"role": msg["role"], "content": msg["content"]})

    # Add the current prompt with augmented context
    current_prompt = (
        f"Relevant Transcript Excerpts:\n"
        f"============================\n"
        f"{context_text}\n"
        f"============================\n\n"
        f"User Question: {user_query}\n\n"
        f"Provide a thorough, grounded answer referencing the guests and insights from the transcripts."
    )
    llm_messages.append({"role": "user", "content": current_prompt})

    # 3. Stream completion tokens
    async for token in stream_completion(llm_messages, system_prompt=RAG_SYSTEM_PROMPT):
        yield {"type": "text", "content": token}
