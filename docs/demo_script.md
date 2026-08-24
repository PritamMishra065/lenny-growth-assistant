# Demo Video Script (2–3 Minutes) — The Lenny Growth Assistant

Use this structured walkthrough to record your 2–3 minute demo video with camera enabled.

---

## ⏱️ Video Structure & Script

### 0:00 – 0:30 | Introduction & Problem Context (Camera ON)
- **Face on Camera**:
  > *"Hi everyone, I'm presenting 'The Lenny Growth Assistant' — an AI-powered conversational web application built as a Forward Deployed Engineer engagement.
  > Product and growth leaders spend hundreds of hours consuming Lenny's podcast, but extracting specific frameworks, generating publishable essays, and creating actionable artifacts typically requires high manual effort. This product solves that by providing grounded answers, Ship 30 essays, and in-app interactive artifacts grounded strictly in 300+ podcast transcripts."*

### 0:30 – 1:00 | Architecture & One-Command Startup
- **Screen Share**:
  - Show the terminal: `docker compose up -d`
  - Show the UI at `http://localhost:3000`
  - Point out the **Model Switcher** in the top header (Local Ollama `llama3:8b` as the mandatory demo model, plus Google Gemini / Claude / OpenAI cloud options).

### 1:00 – 1:40 | Core Feature Walkthrough
- **Live Interaction 1: Grounded Q&A**:
  - Click on the starter prompt: *"What did Brian Chesky say about micromanagement vs being in the details?"*
  - Show the live streaming response.
  - Expand the **Source Citations** section to highlight the transcript attribution, guest name, episode title, and direct link.
- **Live Interaction 2: Ship 30 for 30 Essay Skill**:
  - Send: *"Write a Ship 30 for 30 essay about retention strategies based on Lenny's transcripts."*
  - Show the 3-line hook, visual cadence headers, bold emphasis, and actionable takeaways.
- **Live Interaction 3: Artifact Viewer**:
  - Click **"Open Artifact"** to show the side-by-side **Artifact Viewer** panel.
  - Toggle between **Preview** and **Code** tabs.
  - Show the DOMPurify sandboxed isolation banner and click **Copy / Download**.

### 1:40 – 2:20 | Key Technical Trade-Off Discussion (Camera ON + Screen)
- **Face & Screen**:
  > *"One key technical trade-off we made was **Vector Indexing Granularity vs. Inference Latency on Local Models**.
  > Rather than chunking by arbitrary token counts that fragment sentences, we implemented paragraph-boundary-aware chunking with 50-token semantic overlap. For embeddings, we chose Ollama's `nomic-embed-text` so the entire pipeline runs locally with zero API cost. To give evaluators flexibility without waiting for 300 full episodes to embed, we built a dynamic Selective Ingestion Drawer allowing any episode to be indexed in seconds."*

### 2:20 – 2:45 | Conclusion & Evaluator Handoff
- **Summary**:
  > *"The system includes full PostgreSQL session persistence, multi-provider model switching, comprehensive automated tests, and Docker Compose reproducibility. Thank you!"*
