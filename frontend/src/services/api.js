/**
 * API client for interacting with The Lenny Growth Assistant backend.
 */

const API_BASE = '';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchModelConfig() {
  const res = await fetch(`${API_BASE}/api/config/model`);
  return res.json();
}

export async function updateModelConfig(provider, model = null) {
  const res = await fetch(`${API_BASE}/api/config/model`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, model }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to update model config');
  }
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`);
  return res.json();
}

export async function createSession(title = 'New Chat') {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  return res.ok;
}

export async function fetchMessages(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`);
  return res.json();
}

export async function fetchAvailableEpisodes() {
  const res = await fetch(`${API_BASE}/api/ingestion/episodes`);
  return res.json();
}

export async function fetchIngestionStatus() {
  const res = await fetch(`${API_BASE}/api/ingestion/status`);
  return res.json();
}

export async function ingestEpisodes(slugs = null, ingestAll = false) {
  const res = await fetch(`${API_BASE}/api/ingestion/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slugs, ingest_all: ingestAll }),
  });
  return res.json();
}

export async function clearVectorStore() {
  const res = await fetch(`${API_BASE}/api/ingestion/clear`, {
    method: 'DELETE',
  });
  return res.json();
}
