import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

export default function SourceCitation({ sources }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-container">
      <button 
        className="sources-toggle-btn"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <BookOpen size={13} />
        <span>Grounded in {sources.length} transcript source{sources.length > 1 ? 's' : ''}</span>
        {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>

      {isExpanded && (
        <div className="sources-list">
          {sources.map((s, idx) => (
            <div key={idx} className="source-card">
              <div className="source-card-header">
                <div className="source-title">
                  {s.guest ? `🎙️ ${s.guest}` : 'Episode'} — {s.episode || 'Lenny\'s Podcast'}
                </div>
                {s.url && (
                  <a 
                    href={s.url} 
                    target="_blank" 
                    rel="noreferrer noopener" 
                    className="source-link"
                    style={{ display: 'flex', alignItems: 'center', gap: 3 }}
                  >
                    <span>Watch</span>
                    <ExternalLink size={10} />
                  </a>
                )}
              </div>
              {s.excerpt && (
                <div className="source-excerpt">
                  "{s.excerpt}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
