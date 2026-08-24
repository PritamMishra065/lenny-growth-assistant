# 🎙️ The Lenny Growth Assistant

An AI-powered conversational web application that ingests Lenny's Podcast transcripts to answer product management and growth questions, generate publication-ready content, and render rich artifacts — all from a polished chat interface.

![Status](https://img.shields.io/badge/status-in_development-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ Features

- **Grounded Q&A** — RAG-powered answers strictly from Lenny's Podcast transcripts with source citations
- **Ship 30 for 30 Essays** — Generate ~1,250-word publication-ready essays with hooks, narrative arc, and actionable takeaways
- **Artifact Viewer** — Render Markdown and HTML/CSS artifacts in-app alongside the chat (Claude Artifacts-style)
- **Flexible LLM Toggle** — Switch between Ollama (local) and cloud providers (Claude, OpenAI) from the UI
- **Session Management** — Independent chat sessions with persistent history
- **Secure Rendering** — Sandboxed iframe + DOMPurify for safe artifact display

## 🏗️ Architecture

```
Frontend (React + Vite)  →  Backend (FastAPI)  →  PostgreSQL
                                    ↓
                             Agent Layer (Skills)
                             ├── RAG Skill
                             ├── Ship 30 Skill
                             └── Artifact Skill
                                    ↓
                         LLM Router (Ollama / Claude / OpenAI)
                                    ↓
                         ChromaDB (Vector Store)
```

See [docs/architecture.md](docs/architecture.md) for full details.

## 📋 Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- [Ollama](https://ollama.ai/) installed on your host machine
- (Optional) Anthropic or OpenAI API key for cloud LLM

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/lenny-growth-assistant.git
cd lenny-growth-assistant
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys (if using cloud LLMs)
```

### 3. Pull the Ollama model
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 4. Start everything
```bash
docker compose up --build
```

### 5. Open the app
Navigate to [http://localhost:3000](http://localhost:3000)

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | (in docker-compose) | PostgreSQL connection string |
| `LLM_PROVIDER` | No | `ollama` | Active LLM: `ollama`, `anthropic`, `openai` |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | No | `llama3.1:8b` | Ollama model name |
| `ANTHROPIC_API_KEY` | If using Claude | — | Anthropic API key |
| `OPENAI_API_KEY` | If using OpenAI | — | OpenAI API key |

See [.env.example](.env.example) for all variables.

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pip install -r requirements.txt
pytest

# Or via Docker
docker compose run backend pytest
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product requirements, user flows, acceptance criteria |
| [Architecture](docs/architecture.md) | System design, DB schema, API contracts |
| [Design](docs/design.md) | UI/UX principles, component specs, accessibility |

## 🛠️ Development

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

## 🔒 Security

- Generated HTML artifacts are rendered in a **sandboxed iframe** with `sandbox="allow-styles"` — no script execution
- All HTML is sanitized with **DOMPurify** before rendering
- No secrets committed to the repository
- API keys are loaded from environment variables only

## 📝 License

MIT
