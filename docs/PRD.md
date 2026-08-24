# Product Requirements Document — The Lenny Growth Assistant

## 1. Forward Deployment Discovery Brief

### 1.1 User and Problem

**Primary User:** Product managers, growth practitioners, and startup founders who consume Lenny Rachitsky's podcast and newsletter for product and growth guidance.

**Job to Be Done:** Quickly extract actionable product and growth insights from hundreds of hours of Lenny's Podcast transcripts — without manually searching, re-listening, or reading full episodes.

**Pain Removed:**
- **Time waste:** Users spend hours scrubbing through episodes to find a specific framework or quote. The assistant surfaces grounded answers in seconds.
- **Knowledge fragmentation:** Insights are scattered across 200+ episodes. The assistant synthesizes cross-episode knowledge into coherent answers.
- **Content creation friction:** Turning podcast insights into publishable written content (e.g., LinkedIn posts, internal memos) requires significant effort. The Ship 30 for 30 skill automates this.
- **Prompt engineering burden:** Users shouldn't need to understand prompting, models, or RAG infrastructure. The assistant abstracts all complexity behind a chat interface.

### 1.2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Answer Grounding Rate** | ≥ 90% of answers cite a specific transcript source | Automated check: every assistant response includes a `sources` array |
| **Retrieval Relevance** | Top-3 retrieved chunks rated relevant by user ≥ 80% of the time | Manual spot-check during evaluation |
| **Session Continuity** | Follow-up questions maintain context within a session | Functional test: multi-turn conversation preserves state |
| **Time to First Answer** | < 10s on local Ollama, < 5s on cloud LLM | Latency logging on each request |
| **One-Command Startup** | Evaluator can run the full stack with a single command | Verified by fresh-clone test |

### 1.3 Assumptions

1. **Transcript availability:** Lenny's Podcast transcripts are publicly accessible or can be ethically sourced. We will use publicly available transcripts from the newsletter/podcast repository.
2. **Local model quality:** An 8B-parameter local model (e.g., Llama 3.1 8B via Ollama) can produce coherent answers when given good retrieved context, though quality will be lower than Claude/GPT-4.
3. **Single-user demo:** The evaluator will test the app as a single user. We do not need authentication, rate limiting, or multi-tenant isolation for the demo.
4. **English only:** All transcripts and interactions are in English.
5. **No real-time ingestion:** Transcripts are pre-ingested at startup. There is no need for a live feed or webhook-based ingestion during the demo.
6. **Evaluator has Docker & Ollama:** The evaluator's machine has Docker, Docker Compose, and Ollama installed (or can install them following our README).

### 1.4 Scope Choices

#### Included ✅
- Conversational RAG assistant grounded in Lenny's transcripts
- Ship 30 for 30 essay generation skill
- Markdown and HTML/CSS artifact generation with in-app viewer
- Session management with independent context per session
- Flexible LLM toggle (Ollama local ↔ Cloud Claude/OpenAI)
- PostgreSQL persistence for sessions, messages, metadata
- Docker Compose one-command startup
- Structured logging and error handling
- Sandboxed artifact rendering with sanitization
- Source citations on every answer

#### Excluded ❌ (with rationale)
- **User authentication:** Out of scope for a single-evaluator demo. Would add complexity without demonstrating core value.
- **Real-time transcript ingestion:** Pre-ingested data is sufficient. A webhook/RSS pipeline would be a Phase 2 feature.
- **Multi-modal support:** No audio/video playback or image generation. Text-only interaction.
- **Fine-tuning:** We use RAG over a general-purpose model. Fine-tuning would require significant compute and is unnecessary for grounded answers.
- **Production deployment (cloud hosting):** The deliverable runs locally. Cloud deployment (AWS/GCP/Vercel) is documented but not implemented.
- **Analytics dashboard:** No usage analytics UI. Structured logs provide operational visibility.

### 1.5 Risks and Trade-offs

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Hallucination** | High | RAG grounding with source citations; system prompt instructs model to say "I don't have enough information" when retrieval is empty or low-confidence |
| **Local model quality** | Medium | Ollama is mandatory for demo but cloud toggle is available; UI clearly labels which model is active |
| **Latency on local models** | Medium | Streaming responses to show progressive output; reasonable chunk sizes |
| **Transcript data gaps** | Medium | Acknowledge coverage limitations in the UI; log retrieval misses |
| **Unsafe artifact rendering** | High | Sandboxed iframe with restrictive `sandbox` attribute + DOMPurify sanitization; no script execution |
| **Data leakage** | Low | No secrets in repo; `.env.example` with placeholders; `.gitignore` excludes `.env` |
| **Cost (cloud LLMs)** | Low | Local Ollama is the default; cloud is opt-in |

---

## 2. User Flows

### 2.1 Conversational Q&A Flow
```
User opens app → Clicks "New Chat" → Types a product/growth question
→ Backend retrieves relevant transcript chunks → LLM generates grounded answer with citations
→ User sees answer with source links → User asks follow-up → Context is maintained
```

### 2.2 Ship 30 for 30 Essay Flow
```
User asks a question or has ongoing conversation → Requests "Write a Ship 30 for 30 essay about this"
→ Agent routes to Ship 30 skill → Skill generates ~1,250-word essay with hook, headings, bold, takeaway
→ Essay renders in Artifact Viewer panel alongside chat
```

### 2.3 Artifact Generation Flow
```
User requests a Markdown doc or HTML artifact → Agent routes to artifact skill
→ Generates Markdown or HTML/CSS → Artifact Viewer panel opens → Content rendered in sandboxed iframe
→ User can copy raw code or download the artifact
```

### 2.4 Model Toggle Flow
```
User clicks model toggle in header → Selects Ollama / Claude / OpenAI
→ Subsequent messages use selected provider → If provider unavailable, shows error with fallback suggestion
```

---

## 3. Acceptance Criteria

### P0 — Must Have
- [ ] Conversational RAG answers grounded in Lenny's transcripts with source citations
- [ ] Follow-up questions maintain session context
- [ ] Ship 30 for 30 essay generation with proper formatting
- [ ] Artifact viewer renders Markdown and HTML/CSS alongside chat
- [ ] Artifact HTML is sandboxed and sanitized
- [ ] LLM toggle between Ollama (local) and at least one cloud provider
- [ ] PostgreSQL persistence for sessions and messages
- [ ] One-command startup via Docker Compose
- [ ] `.env.example` with documented variables
- [ ] Structured logging
- [ ] Graceful error handling (missing keys, model timeouts, empty retrieval)

### P1 — Should Have
- [ ] Streaming responses for better UX
- [ ] Responsive layout (mobile + desktop)
- [ ] Dark mode
- [ ] Copy/download buttons on artifacts
- [ ] Health endpoint

### P2 — Nice to Have
- [ ] Keyboard shortcuts
- [ ] Message search within sessions
- [ ] Export conversation as Markdown

---

## 4. Implementation Plan

See [architecture.md](./architecture.md) for technical details and [design.md](./design.md) for UI/UX decisions.

### Timeline
| Phase | Duration | Description |
|-------|----------|-------------|
| 1 | 2h | Scaffolding, Git, documentation |
| 2 | 3h | Database schema, FastAPI skeleton, core APIs |
| 3 | 3h | Transcript ingestion, embeddings, retrieval |
| 4 | 4h | LLM config, agent layer, skill routing |
| 5 | 4h | Frontend chat UI (React + Vite) |
| 6 | 2h | Artifact viewer with security |
| 7 | 2h | Docker Compose, deployment |
| 8 | 3h | Tests, README, polish |
