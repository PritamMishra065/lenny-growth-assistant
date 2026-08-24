# Architecture Document — The Lenny Growth Assistant

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                          │
│                                                                 │
│  ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐  │
│  │   Frontend    │   │     Backend      │   │  PostgreSQL   │  │
│  │  React/Vite   │──▶│    FastAPI       │──▶│    Database    │  │
│  │   (nginx)     │   │   (uvicorn)      │   │               │  │
│  │   Port 3000   │   │   Port 8000      │   │   Port 5432   │  │
│  └──────────────┘   └──────┬───────────┘   └───────────────┘  │
│                            │                                    │
│                     ┌──────┴───────────┐                       │
│                     │   Agent Layer    │                        │
│                     │  ┌────────────┐  │                       │
│                     │  │  RAG Skill │  │                       │
│                     │  │  S30 Skill │  │                       │
│                     │  │ Artifact   │  │                       │
│                     │  └──────┬─────┘  │                       │
│                     └─────┬──┴────────┘                        │
│                           │                                     │
│                    ┌──────┴──────┐                              │
│                    │ LLM Router  │                              │
│                    └──┬──────┬──┘                               │
│                       │      │                                  │
│              ┌────────┴┐  ┌──┴────────┐                        │
│              │ Ollama  │  │Cloud APIs │                         │
│              │ (host)  │  │Claude/OAI │                         │
│              └─────────┘  └───────────┘                        │
│                                                                 │
│         ┌─────────────────────────┐                            │
│         │  ChromaDB (embedded)    │                             │
│         │  Vector Store           │                             │
│         └─────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Database Schema

### PostgreSQL Tables

```sql
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_provider VARCHAR(50) DEFAULT 'ollama',
    model_name VARCHAR(100) DEFAULT 'llama3.1:8b',
    metadata JSONB DEFAULT '{}'
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    artifact JSONB DEFAULT NULL,  -- {type: 'markdown'|'html', content: '...'}
    skill_used VARCHAR(50),       -- 'rag', 'ship30', 'artifact', NULL
    model_provider VARCHAR(50),
    model_name VARCHAR(100),
    tokens_used INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_sessions_updated_at ON sessions(updated_at);
```

### ChromaDB (Vector Store)
- **Collection:** `lenny_transcripts`
- **Document:** Individual transcript chunks (~500 tokens each)
- **Metadata:** `{episode_title, guest, date, url, chunk_index}`
- **Embedding model:** `nomic-embed-text` via Ollama (local) or `text-embedding-3-small` via OpenAI (cloud)

## 3. API Endpoints

### Health & Config
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns DB, vector store, and LLM status |
| `GET` | `/api/config/model` | Returns current active model provider and name |
| `PUT` | `/api/config/model` | Switch model provider (`ollama`, `anthropic`, `openai`) |

### Sessions
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions` | List all sessions, ordered by `updated_at` desc |
| `POST` | `/api/sessions` | Create a new session |
| `GET` | `/api/sessions/{id}` | Get session details |
| `DELETE` | `/api/sessions/{id}` | Delete a session and its messages |

### Messages / Chat
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions/{id}/messages` | Get all messages in a session |
| `POST` | `/api/sessions/{id}/messages` | Send a message and get assistant response (streaming SSE) |

### Request/Response Contracts

#### POST `/api/sessions/{id}/messages`
**Request:**
```json
{
  "content": "What does Lenny say about product-market fit?",
  "model_override": null  // optional: override session default
}
```

**Response (SSE stream):**
```
event: chunk
data: {"type": "text", "content": "Based on "}

event: chunk
data: {"type": "text", "content": "several episodes..."}

event: sources
data: {"sources": [{"episode": "...", "guest": "...", "url": "...", "excerpt": "..."}]}

event: artifact
data: {"type": "markdown", "content": "# Essay Title\n..."}

event: done
data: {"message_id": "uuid", "skill_used": "rag", "latency_ms": 2340}
```

#### Error Response
```json
{
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "Ollama is not running. Start it with `ollama serve` or switch to a cloud provider.",
    "details": {}
  }
}
```

## 4. Component Boundaries

### Backend Components

```
backend/app/
├── main.py              # FastAPI app factory, middleware, startup/shutdown
├── config.py            # Settings via pydantic-settings (env vars)
├── api/
│   ├── __init__.py
│   ├── health.py        # Health endpoint
│   ├── sessions.py      # Session CRUD
│   ├── messages.py      # Chat endpoint with streaming
│   └── config_routes.py # Model config endpoints
├── agents/
│   ├── __init__.py
│   ├── router.py        # Intent detection → skill routing
│   ├── rag_skill.py     # RAG conversational skill
│   ├── ship30_skill.py  # Ship 30 for 30 essay skill
│   └── artifact_skill.py# Artifact generation skill
├── services/
│   ├── __init__.py
│   ├── llm.py           # LLM provider abstraction (Ollama, Claude, OpenAI)
│   ├── retrieval.py     # Vector search + reranking
│   ├── ingestion.py     # Transcript loading, chunking, embedding
│   └── sanitizer.py     # HTML sanitization for artifacts
└── db/
    ├── __init__.py
    ├── database.py       # Async connection pool (asyncpg)
    ├── models.py         # Pydantic models
    └── queries.py        # SQL query functions
```

### Frontend Components

```
frontend/src/
├── App.jsx              # Root app with layout
├── main.jsx             # Entry point
├── components/
│   ├── ChatSidebar.jsx  # Session list + new chat
│   ├── ChatWindow.jsx   # Message thread
│   ├── MessageBubble.jsx# Individual message display
│   ├── InputBar.jsx     # User input with send
│   ├── ModelToggle.jsx  # LLM provider switcher
│   ├── ArtifactViewer.jsx # Side panel artifact renderer
│   ├── SourceCitation.jsx # Expandable source references
│   └── LoadingIndicator.jsx
├── pages/
│   └── ChatPage.jsx     # Main page layout
├── services/
│   ├── api.js           # Backend API client
│   └── stream.js        # SSE stream parser
└── styles/
    └── index.css         # Global styles + design tokens
```

## 5. Ingestion & Retrieval Flow

```
Transcripts (Markdown files)
    │
    ▼
  Loader (reads .md files from data/transcripts/)
    │
    ▼
  Chunker (split by ~500 tokens, overlap 50 tokens)
    │  Preserves metadata: episode, guest, date, URL
    ▼
  Embedder (nomic-embed-text via Ollama or text-embedding-3-small via OpenAI)
    │
    ▼
  ChromaDB (persist to data/chroma/)
    │
    ▼
  [At query time]
    │
  Query Embedding → Similarity Search (top-k=5) → Rerank → Context Assembly
    │
    ▼
  LLM generates answer with source attribution
```

### Chunking Strategy
- **Method:** Recursive character splitting with Markdown-aware boundaries
- **Chunk size:** ~500 tokens (~2000 characters)
- **Overlap:** 50 tokens (~200 characters)
- **Metadata preserved:** Episode title, guest name, publish date, source URL, chunk index

## 6. Agent Routing

```
User Message
    │
    ▼
  Intent Classifier (keyword + LLM-based)
    │
    ├─── "ship 30" / "essay" / "write an article" ──▶ Ship30Skill
    │
    ├─── "create artifact" / "generate html" / "make a document" ──▶ ArtifactSkill
    │
    └─── default (questions, follow-ups) ──▶ RAGSkill
```

### Skill Details

| Skill | Input | Output | System Prompt Focus |
|-------|-------|--------|-------------------|
| **RAGSkill** | User question + retrieved chunks + session history | Grounded answer with source citations | Answer only from provided context; cite sources; say "I don't know" when unsure |
| **Ship30Skill** | Topic + retrieved chunks | ~1,250-word essay | Hook, narrative arc, headings, bold, bullets, actionable takeaway |
| **ArtifactSkill** | User request + conversation context | Markdown or HTML/CSS document | Generate complete, self-contained artifact; no external dependencies |

## 7. LLM Provider Configuration

```python
# config.py
class Settings(BaseSettings):
    # LLM Provider: "ollama", "anthropic", "openai"
    LLM_PROVIDER: str = "ollama"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Embeddings
    EMBEDDING_PROVIDER: str = "ollama"  # "ollama" or "openai"
    EMBEDDING_MODEL: str = "nomic-embed-text"
```

### Fallback Behavior
1. If selected provider fails → return error with suggestion to switch
2. If Ollama not running → clear error message with `ollama serve` instructions
3. If API key missing → error on startup with specific guidance

## 8. Security

### Artifact Rendering
- **Strategy:** Defense in depth
  1. **DOMPurify** on backend: Strip `<script>`, event handlers, `javascript:` URLs
  2. **Sandboxed iframe** on frontend: `sandbox="allow-styles"` — no scripts, no forms, no popups
  3. **CSP header** on iframe: `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'`
- **Allowed:** HTML tags, CSS styles, images (data: URIs only)
- **Blocked:** JavaScript execution, external resource loading, form submissions, navigation

### Data Security
- No secrets in repository
- `.env.example` with placeholder values
- API keys validated at startup
- No user PII collected or stored

## 9. Deployment Topology

```yaml
# docker-compose.yml services
services:
  postgres:     # PostgreSQL 16, port 5432, persistent volume
  backend:      # FastAPI + uvicorn, port 8000, depends on postgres
  frontend:     # Vite build + nginx, port 3000, depends on backend

# External (host machine):
  # Ollama — runs on host, backend connects via OLLAMA_BASE_URL
```

### Startup Order
1. PostgreSQL starts, runs init scripts
2. Backend starts, runs DB migrations, ingests transcripts on first run
3. Frontend starts, proxies API requests to backend
4. Ollama must be running on host (documented in README)

## 10. Observability

### Structured Logging
```python
# All logs in JSON format via structlog
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "chat_response",
  "session_id": "uuid",
  "skill": "rag",
  "model": "llama3.1:8b",
  "provider": "ollama",
  "retrieval_count": 5,
  "latency_ms": 2340,
  "tokens_used": 512
}
```

### Key Metrics Logged
- Request latency per endpoint
- LLM response time and token usage
- Retrieval hit count and relevance
- Error rates by category (model, DB, retrieval)
- Session and message counts
