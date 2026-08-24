# AI Coding Agent Development Log & Transcripts

**Project:** The Lenny Growth Assistant  
**Engagement Role:** Forward Deployed AI Engineer  
**Stack:** FastAPI, PostgreSQL, ChromaDB, React + Vite, Ollama (`llama3:8b`, `nomic-embed-text`), Google Gemini / Claude / OpenAI

---

## 1. Engineering Process Overview

The solution was developed systematically across 8 distinct phases using autonomous AI coding agent workflows:

1. **Phase 1: Project Scaffolding & Discovery Brief**
   - Initialized Git repository and environment configuration templates (`.env.example`).
   - Authored formal PRD, Architecture, and Design documents.

2. **Phase 2: Database Schema & API Foundation**
   - Implemented async PostgreSQL persistence with SQLAlchemy (`asyncpg`) and table schemas for `sessions` and `messages`.
   - Built FastAPI application with SSE streaming endpoints, health checks, and runtime model configuration.

3. **Phase 3: Knowledge Base & Vector Retrieval**
   - Downloaded and parsed 303 episodes from Lenny's Podcast repository with YAML frontmatter metadata.
   - Built chunking pipeline with paragraph boundary preservation and overlap.
   - Generated vector embeddings via local Ollama `nomic-embed-text` and indexed them into persistent ChromaDB.
   - Implemented selective episode ingestion API to allow evaluators to index specific episodes on demand.

4. **Phase 4: Agent Routing & Multi-Skill Implementation**
   - Built unified LLM abstraction supporting local Ollama (`llama3:8b`) as well as cloud providers (Gemini, Claude, OpenAI).
   - Created **RAG Conversational Skill** with transcript grounding and citation extraction.
   - Created **Ship 30 for 30 Skill** applying digital writing principles (~1,250 words, hook, visual cadence, actionable takeaway).
   - Created **Artifact Skill** generating production-grade Markdown documents and self-contained HTML/CSS components.

5. **Phase 5 & 6: React Frontend & Sandboxed Artifact Viewer**
   - Built modern dark-themed React + Vite interface with warm amber accents, glassmorphism, responsive sidebar, and starter prompts.
   - Built Claude-style **Artifact Viewer** side panel with Preview/Code tabs, DOMPurify sanitization, and sandboxed `<iframe>` isolation.
   - Built **Transcript Management Modal** for interactive browsing and indexing of the 303 episodes.

6. **Phase 7: Containerization & Orchestration**
   - Created multi-stage Dockerfiles for backend (FastAPI) and frontend (Nginx).
   - Authored `docker-compose.yml` with health checks, volumes, and `host.docker.internal` host networking for Ollama connectivity.

7. **Phase 8: Test Suite & Documentation**
   - Authored end-to-end automated tests and evaluator verification guide.

---

## 2. Technical Challenges Encountered & Resolutions

### Challenge 1: Windows Encoding Issues (`cp1252`) in Automated Test Scripts
- **Problem**: When running test scripts in Windows PowerShell, Unicode checkmark emojis (`\u2705`) caused `UnicodeEncodeError: 'charmap' codec can't encode character`.
- **Correction**: Configured UTF-8 stream wrapping (`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`) and standardized test logs to clean ASCII status tags (`[OK]`).

### Challenge 2: Async DB Session Lifecycle in Streaming Responses
- **Problem**: In FastAPI, the `db: AsyncSession` dependency was closed immediately upon returning `StreamingResponse`, causing errors when the SSE generator attempted to query context or persist the completed assistant message.
- **Correction**: Refactored the SSE generator to open dedicated `async with async_session() as db_session:` context blocks inside the background generator, decoupling stream persistence from the initial HTTP handler lifecycle.

### Challenge 3: Intent Classification Keyword Precision
- **Problem**: Initial strict phrase matching for "generate html" missed natural queries like "generate an interactive HTML calculator widget".
- **Correction**: Upgraded `classify_intent` in `backend/app/agents/router.py` to flexible token matching across key skill domains (`ship30`, `artifact`, `rag`).

### Challenge 4: Zero-Cost Local Inference with Ollama
- **Problem**: Downloading a new 5GB model over the network during test runs introduces variable latency.
- **Correction**: Designed the system to leverage existing local Ollama models (`llama3:8b` / `llama3.1:8b` / `mistral`) and local embeddings (`nomic-embed-text`), with cloud model toggling (Gemini, Claude, OpenAI) available instantaneously via UI toggle.
