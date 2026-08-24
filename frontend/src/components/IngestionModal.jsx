import React, { useState, useEffect } from 'react';
import { Database, X, Search, CheckSquare, Square, RefreshCw, Trash2, CheckCircle2 } from 'lucide-react';
import { fetchAvailableEpisodes, fetchIngestionStatus, ingestEpisodes, clearVectorStore } from '../services/api';

export default function IngestionModal({ isOpen, onClose }) {
  const [episodes, setEpisodes] = useState([]);
  const [status, setStatus] = useState(null);
  const [selectedSlugs, setSelectedSlugs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  async function loadData() {
    try {
      const [epData, stData] = await Promise.all([
        fetchAvailableEpisodes(),
        fetchIngestionStatus(),
      ]);
      setEpisodes(epData.episodes || []);
      setStatus(stData);
    } catch (err) {
      console.error('Failed to load episodes:', err);
    }
  }

  function toggleSlug(slug) {
    if (selectedSlugs.includes(slug)) {
      setSelectedSlugs(selectedSlugs.filter(s => s !== slug));
    } else {
      setSelectedSlugs([...selectedSlugs, slug]);
    }
  }

  function handleSelectAllVisible() {
    const visibleSlugs = filteredEpisodes.map(e => e.slug);
    const allSelected = visibleSlugs.every(s => selectedSlugs.includes(s));
    if (allSelected) {
      setSelectedSlugs(selectedSlugs.filter(s => !visibleSlugs.includes(s)));
    } else {
      const merged = Array.from(new Set([...selectedSlugs, ...visibleSlugs]));
      setSelectedSlugs(merged);
    }
  }

  async function handleIngestSelected() {
    if (selectedSlugs.length === 0) return;
    setLoading(true);
    setMessage('Embedding and indexing selected episodes via Ollama nomic-embed-text...');
    try {
      const res = await ingestEpisodes(selectedSlugs);
      setMessage(`Done! Ingested ${res.episodes} episodes (${res.chunks} chunks).`);
      await loadData();
      setSelectedSlugs([]);
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    if (!window.confirm('Clear all indexed vector transcripts?')) return;
    setLoading(true);
    try {
      await clearVectorStore();
      setMessage('Vector store cleared.');
      await loadData();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  const filteredEpisodes = episodes.filter(e => 
    e.guest.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Database size={18} color="var(--accent-primary)" />
            <span style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>
              Lenny's Transcript Knowledge Base
            </span>
          </div>
          <button className="artifact-close-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Status card */}
          <div style={{ 
            padding: '12px 16px', 
            backgroundColor: 'var(--bg-tertiary)', 
            borderRadius: 'var(--radius-md)', 
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>
                Indexed Vector Store Status
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {status?.chunks || 0} chunks indexed across {status?.episodes || 0} episodes
              </div>
            </div>
            {status?.chunks > 0 && (
              <button 
                onClick={handleClear} 
                disabled={loading}
                style={{ 
                  background: 'transparent', 
                  border: '1px solid rgba(239, 68, 68, 0.3)', 
                  color: '#ef4444', 
                  padding: '4px 10px', 
                  borderRadius: 6,
                  fontSize: '11px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}
              >
                <Trash2 size={11} />
                <span>Clear DB</span>
              </button>
            )}
          </div>

          {message && (
            <div style={{ padding: '8px 12px', background: 'var(--accent-muted)', color: 'var(--accent-hover)', borderRadius: 6, fontSize: '12px', marginBottom: 12 }}>
              {message}
            </div>
          )}

          {/* Search & Bulk Select */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
            <div style={{ 
              flex: 1, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8, 
              backgroundColor: 'var(--bg-tertiary)', 
              border: '1px solid var(--border-default)', 
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px'
            }}>
              <Search size={13} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search guest or episode..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{ background: 'transparent', border: 'none', outline: 'none', color: '#fff', fontSize: '13px', width: '100%' }}
              />
            </div>
            <button 
              onClick={handleSelectAllVisible}
              style={{ 
                padding: '6px 12px', 
                backgroundColor: 'var(--bg-elevated)', 
                border: '1px solid var(--border-subtle)', 
                borderRadius: 6,
                color: 'var(--text-secondary)',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Select Visible
            </button>
          </div>

          {/* Episode List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: '320px', overflowY: 'auto' }}>
            {filteredEpisodes.map(ep => {
              const isSelected = selectedSlugs.includes(ep.slug);
              const isIndexed = status?.episode_slugs?.includes(ep.slug);

              return (
                <div
                  key={ep.slug}
                  onClick={() => toggleSlug(ep.slug)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    backgroundColor: isSelected ? 'var(--accent-muted)' : 'var(--bg-tertiary)',
                    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    fontSize: '13px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {isSelected ? <CheckSquare size={14} color="var(--accent-primary)" /> : <Square size={14} color="var(--text-muted)" />}
                    <div>
                      <span style={{ fontWeight: 600, color: '#fff' }}>{ep.guest}</span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>— {ep.title}</span>
                    </div>
                  </div>
                  {isIndexed && (
                    <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: 3 }}>
                      <CheckCircle2 size={12} /> Indexed
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button 
            onClick={onClose}
            style={{ padding: '8px 14px', background: 'transparent', border: '1px solid var(--border-default)', color: 'var(--text-secondary)', borderRadius: 6, cursor: 'pointer', fontSize: '13px' }}
          >
            Close
          </button>
          <button 
            onClick={handleIngestSelected}
            disabled={loading || selectedSlugs.length === 0}
            style={{ 
              padding: '8px 16px', 
              backgroundColor: 'var(--accent-primary)', 
              color: 'var(--text-inverse)', 
              border: 'none', 
              borderRadius: 6, 
              fontWeight: 600, 
              cursor: selectedSlugs.length > 0 && !loading ? 'pointer' : 'not-allowed', 
              fontSize: '13px',
              opacity: selectedSlugs.length > 0 && !loading ? 1 : 0.5
            }}
          >
            {loading ? 'Ingesting...' : `Ingest Selected (${selectedSlugs.length})`}
          </button>
        </div>
      </div>
    </div>
  );
}
