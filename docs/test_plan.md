# Test Plan & Quality Assurance — The Lenny Growth Assistant

## 1. Automated Test Suite

The automated test suite covers the critical paths across backend API contracts, database persistence, semantic retrieval grounding, and multi-skill agent routing.

### Running All Automated Tests

```bash
cd backend
python tests/test_phase2.py   # Tests Database, Session/Message CRUD, SSE streaming, Config endpoints
python tests/test_phase3.py   # Tests Transcript Ingestion, Vector Indexing, Semantic Retrieval
python tests/test_phase4.py   # Tests Agent Skills (RAG, Ship 30, Artifacts) & LLM Router
```

### Automated Test Coverage Matrix

| Test Suite | Components Tested | Key Assertions |
|---|---|---|
| **Phase 2 Suite** | FastAPI, PostgreSQL, SSE Stream | Health check status `healthy`, Session CRUD, SSE stream event sequencing (`chunk`, `done`), DB persistence |
| **Phase 3 Suite** | Ingestion Pipeline, ChromaDB, Ollama Embeddings | 303 episode discovery, selective indexing by slug, duplicate prevention, semantic similarity > 0.80 on transcript queries |
| **Phase 4 Suite** | Intent Classifier, RAG Skill, Ship 30 Skill, Artifact Skill | Skill routing accuracy, source citation extraction, hook & formatting in Ship 30 essays, self-contained HTML/CSS rendering |

---

## 2. Manual UI/UX Test Plan

For evaluators testing the application through the web interface at `http://localhost:3000`:

### Test Scenario 1: Grounded Conversational Q&A
1. Open `http://localhost:3000`.
2. Click the starter prompt: *"What did Brian Chesky say about micromanagement and why founders must be in the details?"*
3. **Expected Behavior**:
   - Typing indicator displays immediately.
   - Text streams smoothly.
   - Response quotes Brian Chesky's perspective on micromanagement vs. being in the details.
   - Expandable **"Grounded in 1 transcript source"** citation shows episode title, guest name, and direct link.

### Test Scenario 2: Ship 30 for 30 Essay Generation
1. In the chat input, type: `"Write a Ship 30 for 30 essay about retention strategies for early-stage startups based on Lenny's podcast."`
2. **Expected Behavior**:
   - Assistant generates an atomic essay with a strong 3-line hook, H2/H3 headers, bold takeaways, and actionable bullet points.
   - An **"Open Artifact"** button appears below the message.
   - Clicking it slides in the **Artifact Viewer** side panel displaying the formatted essay.

### Test Scenario 3: Interactive Artifact Generation & Security Sanitization
1. Type: `"Generate an interactive HTML/CSS calculator widget for estimating Product Market Fit score based on transcript benchmarks."`
2. **Expected Behavior**:
   - The assistant generates complete HTML/CSS.
   - The **Artifact Viewer** opens automatically with the interactive calculator rendered inside a sandboxed `<iframe>`.
   - Security banner indicates DOMPurify sanitization.
   - User can click **"Copy"** or **"Download"** to export the file.

### Test Scenario 4: LLM Provider Toggle
1. Click the model pill in the top header.
2. View available providers (Ollama Local, Google Gemini, Anthropic Claude, OpenAI).
3. Switch between local and cloud providers.
4. Subsequent messages use the newly selected provider.

### Test Scenario 5: Knowledge Base Management
1. Click **"Manage Transcripts"** in the sidebar footer.
2. In the modal, view current vector store status (indexed chunks & episodes).
3. Search for a specific guest (e.g. `elena-verna` or `marty-cagan`).
4. Click **"Ingest Selected"** to dynamically embed and add episodes to the vector database.
