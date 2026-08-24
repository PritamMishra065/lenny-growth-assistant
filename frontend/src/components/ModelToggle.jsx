import React, { useState, useEffect, useRef } from 'react';
import { Cpu, ChevronDown, Check, Key, X, Eye, EyeOff, ExternalLink, ShieldCheck } from 'lucide-react';
import { fetchModelConfig, updateModelConfig } from '../services/api';

const PROVIDER_DOCS = {
  gemini: {
    name: 'Google Gemini',
    docsUrl: 'https://aistudio.google.com/app/apikey',
    placeholder: 'AIzaSy...',
  },
  anthropic: {
    name: 'Anthropic Claude',
    docsUrl: 'https://console.anthropic.com/settings/keys',
    placeholder: 'sk-ant-api...',
  },
  openai: {
    name: 'OpenAI',
    docsUrl: 'https://platform.openai.com/api-keys',
    placeholder: 'sk-proj-...',
  },
};

export default function ModelToggle() {
  const [config, setConfig] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [keyModalProvider, setKeyModalProvider] = useState(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [modalError, setModalError] = useState('');
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadConfig();
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function loadConfig() {
    try {
      const data = await fetchModelConfig();
      setConfig(data);
    } catch (err) {
      console.error('Failed to load model config:', err);
    }
  }

  async function handleSelectProvider(providerObj) {
    // If local Ollama, switch immediately
    if (providerObj.id === 'ollama') {
      setLoading(true);
      try {
        const updated = await updateModelConfig('ollama');
        setConfig(updated);
        setIsOpen(false);
      } catch (err) {
        alert(`Could not switch model: ${err.message}`);
      } finally {
        setLoading(false);
      }
      return;
    }

    // If cloud provider is not configured, or user wants to enter key -> open modal
    if (!providerObj.configured) {
      setIsOpen(false);
      setKeyModalProvider(providerObj.id);
      setApiKeyInput('');
      setModalError('');
      return;
    }

    // Otherwise switch directly
    setLoading(true);
    try {
      const updated = await updateModelConfig(providerObj.id);
      setConfig(updated);
      setIsOpen(false);
    } catch (err) {
      // If error says key missing, prompt for key
      setIsOpen(false);
      setKeyModalProvider(providerObj.id);
      setApiKeyInput('');
      setModalError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveKey(e) {
    e?.preventDefault();
    if (!apiKeyInput.trim()) {
      setModalError('Please enter a valid API key');
      return;
    }

    setLoading(true);
    setModalError('');
    try {
      const updated = await updateModelConfig(keyModalProvider, null, apiKeyInput.trim());
      setConfig(updated);
      setKeyModalProvider(null);
      setApiKeyInput('');
    } catch (err) {
      setModalError(err.message || 'Failed to update API key');
    } finally {
      setLoading(false);
    }
  }

  if (!config) return null;

  const activeProviderObj = config.available_providers.find(p => p.id === config.provider) || {
    name: config.provider,
    model: config.model
  };

  const currentModalInfo = keyModalProvider ? PROVIDER_DOCS[keyModalProvider] : null;

  return (
    <>
      <div className="model-toggle-container" ref={dropdownRef}>
        <button 
          className="provider-select-btn" 
          onClick={() => setIsOpen(!isOpen)}
          disabled={loading}
        >
          <Cpu size={14} color="var(--accent-primary)" />
          <span>{activeProviderObj.name}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({config.model})</span>
          <ChevronDown size={12} style={{ marginLeft: 2 }} />
        </button>

        {isOpen && (
          <div className="provider-dropdown">
            <div style={{ padding: '6px 12px 4px', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Select LLM Provider
            </div>
            {config.available_providers.map((p) => {
              const isSelected = p.id === config.provider;
              return (
                <div
                  key={p.id}
                  className={`provider-option ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleSelectProvider(p)}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {p.name}
                      {p.id === 'ollama' ? (
                        <span style={{ fontSize: '10px', background: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '1px 5px', borderRadius: 4 }}>
                          Local
                        </span>
                      ) : p.configured ? (
                        <span style={{ fontSize: '10px', background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '1px 5px', borderRadius: 4 }}>
                          Ready
                        </span>
                      ) : (
                        <span style={{ fontSize: '10px', background: 'rgba(245,158,11,0.15)', color: 'var(--accent-primary)', padding: '1px 5px', borderRadius: 4 }}>
                          Needs Key
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.model}</div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {p.id !== 'ollama' && (
                      <button
                        title="Configure API Key"
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsOpen(false);
                          setKeyModalProvider(p.id);
                          setApiKeyInput('');
                          setModalError('');
                        }}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--text-muted)',
                          cursor: 'pointer',
                          padding: 4,
                          display: 'flex',
                          alignItems: 'center',
                          borderRadius: 4
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent-primary)'}
                        onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                      >
                        <Key size={12} />
                      </button>
                    )}
                    {isSelected && <Check size={14} color="var(--accent-primary)" />}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* API Key Modal Popup */}
      {keyModalProvider && (
        <div className="modal-backdrop" onClick={() => setKeyModalProvider(null)}>
          <div className="modal-content" style={{ maxWidth: '440px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Key size={18} color="var(--accent-primary)" />
                <span style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>
                  Configure {currentModalInfo?.name} API Key
                </span>
              </div>
              <button className="artifact-close-btn" onClick={() => setKeyModalProvider(null)}>
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSaveKey}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Enter your {currentModalInfo?.name} API key to switch to this cloud provider. Your key is stored securely in memory during this session.
                </p>

                {modalError && (
                  <div style={{ padding: '8px 12px', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171', borderRadius: 6, fontSize: '12px' }}>
                    {modalError}
                  </div>
                )}

                <div style={{ position: 'relative' }}>
                  <input
                    type={showKey ? 'text' : 'password'}
                    placeholder={currentModalInfo?.placeholder || 'Enter API key...'}
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    autoFocus
                    style={{
                      width: '100%',
                      padding: '10px 40px 10px 12px',
                      backgroundColor: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-default)',
                      borderRadius: 'var(--radius-md)',
                      color: '#fff',
                      fontSize: '13.5px',
                      fontFamily: 'var(--font-mono)',
                      outline: 'none',
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                    onBlur={(e) => e.target.style.borderColor = 'var(--border-default)'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    style={{
                      position: 'absolute',
                      right: 10,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                    }}
                  >
                    {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#10b981' }}>
                    <ShieldCheck size={13} />
                    <span>In-memory secure session</span>
                  </div>
                  {currentModalInfo?.docsUrl && (
                    <a
                      href={currentModalInfo.docsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--accent-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
                    >
                      <span>Get API Key</span>
                      <ExternalLink size={11} />
                    </a>
                  )}
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setKeyModalProvider(null)}
                  style={{
                    padding: '8px 14px',
                    background: 'transparent',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-secondary)',
                    borderRadius: 6,
                    cursor: 'pointer',
                    fontSize: '13px'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !apiKeyInput.trim()}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'var(--accent-primary)',
                    color: 'var(--text-inverse)',
                    border: 'none',
                    borderRadius: 6,
                    fontWeight: 600,
                    cursor: apiKeyInput.trim() && !loading ? 'pointer' : 'not-allowed',
                    fontSize: '13px',
                    opacity: apiKeyInput.trim() && !loading ? 1 : 0.5
                  }}
                >
                  {loading ? 'Validating...' : 'Save & Switch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
