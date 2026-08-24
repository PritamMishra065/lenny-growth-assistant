"""
LLM abstraction service.
Unified streaming interface across Ollama (local), Google Gemini, Anthropic Claude, and OpenAI.
"""

from typing import AsyncGenerator, Optional
import json
import httpx
import structlog
from app.config import settings

logger = structlog.get_logger()


async def stream_ollama(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response from local Ollama instance."""
    model_name = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})

    for m in messages:
        formatted_messages.append({"role": m["role"], "content": m["content"]})

    payload = {
        "model": model_name,
        "messages": formatted_messages,
        "stream": True,
        "options": {
            "temperature": 0.3,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error("ollama_error_status", status=response.status_code, body=error_body.decode())
                    yield f"Error: Ollama returned status {response.status_code}. Is model '{model_name}' downloaded?"
                    return

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
    except httpx.ConnectError:
        logger.error("ollama_connection_failed", url=url)
        yield "Error: Could not connect to Ollama. Please make sure Ollama is running (`ollama serve`)."
    except Exception as e:
        logger.error("ollama_stream_exception", error=str(e))
        yield f"Error during Ollama inference: {str(e)}"


async def stream_gemini(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response from Google Gemini API."""
    if not settings.GEMINI_API_KEY:
        yield "Error: Gemini API key is not configured. Add GEMINI_API_KEY to your .env file."
        return

    model_name = model or settings.GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={settings.GEMINI_API_KEY}"

    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": m["content"]}],
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.3,
        },
    }

    if system_prompt:
        payload["systemInstruction"] = {
            "parts": [{"text": system_prompt}]
        }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error("gemini_error_status", status=response.status_code, body=error_body.decode())
                    yield f"Error from Gemini API ({response.status_code}): {error_body.decode()}"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    json_str = line[6:].strip()
                    if not json_str:
                        continue
                    try:
                        data = json.loads(json_str)
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            for p in parts:
                                if "text" in p:
                                    yield p["text"]
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error("gemini_stream_exception", error=str(e))
        yield f"Error during Gemini inference: {str(e)}"


async def stream_anthropic(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response from Anthropic Claude API."""
    if not settings.ANTHROPIC_API_KEY:
        yield "Error: Anthropic API key is not configured. Add ANTHROPIC_API_KEY to your .env file."
        return

    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        model_name = model or settings.ANTHROPIC_MODEL

        anthropic_messages = []
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                anthropic_messages.append({"role": m["role"], "content": m["content"]})

        async with client.messages.stream(
            model=model_name,
            max_tokens=4096,
            system=system_prompt or "",
            messages=anthropic_messages,
            temperature=0.3,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as e:
        logger.error("anthropic_stream_exception", error=str(e))
        yield f"Error during Claude inference: {str(e)}"


async def stream_openai(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response from OpenAI API."""
    if not settings.OPENAI_API_KEY:
        yield "Error: OpenAI API key is not configured. Add OPENAI_API_KEY to your .env file."
        return

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        model_name = model or settings.OPENAI_MODEL

        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            openai_messages.append({"role": m["role"], "content": m["content"]})

        stream = await client.chat.completions.create(
            model=model_name,
            messages=openai_messages,
            stream=True,
            temperature=0.3,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error("openai_stream_exception", error=str(e))
        yield f"Error during OpenAI inference: {str(e)}"


async def stream_completion(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Unified router to stream completions based on configured provider."""
    selected_provider = (provider or settings.LLM_PROVIDER).lower()

    logger.info("llm_stream_start", provider=selected_provider, model=model)

    if selected_provider == "gemini":
        async for chunk in stream_gemini(messages, system_prompt, model):
            yield chunk
    elif selected_provider == "anthropic":
        async for chunk in stream_anthropic(messages, system_prompt, model):
            yield chunk
    elif selected_provider == "openai":
        async for chunk in stream_openai(messages, system_prompt, model):
            yield chunk
    else:
        # Default to Ollama
        async for chunk in stream_ollama(messages, system_prompt, model):
            yield chunk
