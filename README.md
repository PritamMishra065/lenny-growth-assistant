# 🎙️ The Lenny Growth Assistant

An enterprise-grade, full-stack conversational AI assistant grounded in **300+ transcripts from Lenny's Podcast**. Built for product managers, growth practitioners, and founders to extract battle-tested frameworks, generate publication-ready **Ship 30 for 30 essays**, and render interactive in-app **Artifacts** (like Claude Artifacts) with zero prompt engineering required.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-19-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black)

---

## 📑 Table of Contents
- [✨ Core Capabilities](#-core-capabilities)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Quick Start (One-Command Run)](#-quick-start-one-command-run)
- [🤖 LLM & Provider Configuration](#-llm--provider-configuration)
- [📦 Transcript Ingestion & Knowledge Base](#-transcript-ingestion--knowledge-base)
- [🔒 Security & Artifact Sanitization](#-security--artifact-sanitization)
- [🧪 Running Automated Tests](#-running-automated-tests)
- [📚 Documentation & Deliverables](#-documentation--deliverables)
- [📹 Demo Video](#-demo-video)

---

## ✨ Core Capabilities

1. **Grounded Conversational Q&A (RAG Skill)**
   - Answers product, growth, and leadership questions strictly grounded in transcript excerpts.
   - Preserves multi-turn session context with independent history.
   - Transparent source citations with guest names, episode titles, and direct links.
   - Graceful *"I don't know"* fallback when context is missing.

2. **Ship 30 for 30 Content Engine**
   - Dedicated skill turning podcast frameworks into structured ~1,250-word Atomic Essays.
   - Follows Ship 30 for 30 digital writing principles: provocative 3-line hook, visual cadence, bold emphasis, and actionable checklists.

3. **In-App Artifact Viewer (Claude Artifacts-style)**
   - Side-by-side split screen viewer that automatically opens when artifacts are created.
   - Supports Markdown documents (PRDs, memos) and interactive HTML/CSS widgets (calculators, mockups).
   - **Preview** and **Code** tabs with one-click **Copy** and **Download**.

4. **Multi-Model Runtime Switcher**
   - Seamlessly toggle between **Local Ollama (`llama3:8b` / `llama3.1:8b`)** and cloud providers (**Google Gemini**, **Anthropic Claude**, **OpenAI**) without restarting.

5. **PostgreSQL Persistence**
   - Independent chat sessions, messages, latency tracking, and token metadata stored asynchronously.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Stack                          │
│                                                                        │
│   ┌─────────────────────┐    ┌───────────────────────────────────┐    │
│   │   Frontend (React)  │    │         Backend (FastAPI)         │    │
│   │    • Vite + Nginx   │───▶│   • Asynchronous REST & SSE       │    │
│   │    • Artifact Viewer│    │   • Intent Classifier & Router    │    │
│   │    • Port 3000      │    │   • Port 8000                     │    │
│   └─────────────────────┘    └───────────────┬───────────────────┘    │
│                                              │                         │
│                    ┌─────────────────────────┼──────────────────┐      │
│                    ▼                         ▼                  ▼      │
│          ┌──────────────────┐      ┌──────────────────┐  ┌───────────┐ │
│          │    PostgreSQL    │      │  ChromaDB Vector │  │LLM Router │ │
│          │  Sessions & Chat │      │  Local Embeddings│  │• Ollama   │ │
│          │  Port 5432       │      │  303 Episodes    │  │• Gemini   │ │
│          └──────────────────┘      └──────────────────┘  │• Claude   │ │
│                                                          │• OpenAI   │ │
│                                                          └───────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for database schemas, API contracts, and component boundaries.

---

## 🚀 Quick Start (One-Command Run)

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Ollama](https://ollama.ai/) installed on your host machine

### 2. Pull local Ollama models
```bash
ollama pull llama3:8b
ollama pull nomic-embed-text
```

### 3. Clone and configure
```bash
git clone https://github.com/YOUR_USERNAME/lenny-growth-assistant.git
cd lenny-growth-assistant
cp .env.example .env
```

### 4. Start the application
```bash
docker compose up --build -d
```

### 5. Access the application
- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🤖 LLM & Provider Configuration

The application includes a zero-friction model toggle in the header:

| Provider | Model Default | Requirements |
|---|---|---|
| **Ollama (Local)** | `llama3:8b` (or `llama3.1:8b`) | Free, runs 100% locally via `ollama serve` |
| **Google Gemini** | `gemini-3.5-flash` | `GEMINI_API_KEY` in `.env` |
| **Anthropic Claude** | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` in `.env` |
| **OpenAI** | `gpt-4o-mini` | `OPENAI_API_KEY` in `.env` |

---

## 📦 Transcript Ingestion & Knowledge Base

The repository includes **303 pre-parsed episodes** from Lenny's Podcast with rich metadata (guest, title, publication date, YouTube URL, keywords).

### Managing Transcripts from the UI
Click **"Manage Transcripts"** in the sidebar footer to:
- View how many chunks are currently indexed.
- Search across all 303 episodes.
- Selectively ingest individual episodes on demand with progress updates.
- Clear and re-index the vector store at any time.

---

## 🔒 Security & Artifact Sanitization

1. **DOMPurify Sanitization**: All HTML generated by the model is sanitized before rendering to strip malicious attributes and unsafe scripts.
2. **Sandboxed `<iframe>` Isolation**: Interactive HTML artifacts are rendered inside an isolated `<iframe>` with strict sandbox permissions.
3. **No Secrets in Repo**: Environment configurations use standard `.env` management with `.gitignore` exclusion.

---

## 🧪 Running Automated Tests

```bash
# Backend Automated Test Suite
cd backend
python tests/test_phase2.py   # Database CRUD, SSE streaming, Config endpoints
python tests/test_phase3.py   # Transcript ingestion, vector indexing, semantic retrieval
python tests/test_phase4.py   # RAG Skill, Ship 30 Skill, Artifact generation
```

See [docs/test_plan.md](docs/test_plan.md) for the manual UI evaluation checklist.

---

## 📚 Documentation & Deliverables

| Deliverable | Document Link | Description |
|---|---|---|
| **PRD** | [docs/PRD.md](docs/PRD.md) | Discovery brief, JTBD, success metrics, assumptions, scope choices, and risk mitigations |
| **Architecture** | [docs/architecture.md](docs/architecture.md) | Database schema, API endpoints, agent routing topology, and security model |
| **Design** | [docs/design.md](docs/design.md) | Design tokens, component specs, accessibility (WCAG AA), and micro-animations |
| **Test Plan** | [docs/test_plan.md](docs/test_plan.md) | Automated test suite and manual verification checklist |
| **Agent Log** | [agent-transcripts/agent_development_log.md](agent-transcripts/agent_development_log.md) | AI coding agent engineering logs, iteration history, and technical corrections |
| **Demo Script** | [docs/demo_script.md](docs/demo_script.md) | 2–3 minute video presentation script with camera guidance |

---

## 📹 Demo Video

- **YouTube Demo Video:** [Link to Demo Video](https://youtube.com) *(Record using [docs/demo_script.md](docs/demo_script.md))*
