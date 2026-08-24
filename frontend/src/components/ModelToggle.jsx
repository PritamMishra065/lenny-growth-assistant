import React, { useState, useEffect, useRef } from 'react';
import { Cpu, ChevronDown, Check, Sparkles } from 'lucide-react';
import { fetchModelConfig, updateModelConfig } from '../services/api';

export default function ModelToggle() {
  const [config, setConfig] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
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

  async function handleSelectProvider(providerId) {
    setLoading(true);
    try {
      const updated = await updateModelConfig(providerId);
      setConfig(updated);
      setIsOpen(false);
    } catch (err) {
      alert(`Could not switch model: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!config) return null;

  const activeProviderObj = config.available_providers.find(p => p.id === config.provider) || {
    name: config.provider,
    model: config.model
  };

  return (
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
              <button
                key={p.id}
                className={`provider-option ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectProvider(p.id)}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {p.name}
                    {p.id === 'ollama' && (
                      <span style={{ fontSize: '10px', background: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '1px 5px', borderRadius: 4 }}>
                        Local
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.model}</div>
                </div>
                {isSelected && <Check size={14} />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
