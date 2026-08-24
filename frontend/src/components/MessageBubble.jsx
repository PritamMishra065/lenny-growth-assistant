import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Sparkles, FileText, Code } from 'lucide-react';
import SourceCitation from './SourceCitation';

export default function MessageBubble({ message, onOpenArtifact }) {
  const isUser = message.role === 'user';

  return (
    <div className="message-wrapper">
      <div className={`message-avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? <User size={18} /> : <Sparkles size={18} />}
      </div>

      <div className="message-bubble">
        <div className="message-header">
          <span className="message-author">
            {isUser ? 'You' : 'Lenny Growth Assistant'}
          </span>
          {message.model_name && !isUser && (
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              • {message.model_name}
            </span>
          )}
          {message.latency_ms && !isUser && (
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              • {(message.latency_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>

        <div className="message-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Artifact Trigger Button */}
        {message.artifact && (
          <div>
            <button 
              className="artifact-badge"
              onClick={() => onOpenArtifact(message.artifact)}
            >
              {message.artifact.type === 'html' ? <Code size={14} /> : <FileText size={14} />}
              <span>Open Artifact: {message.artifact.title || 'Generated Document'}</span>
            </button>
          </div>
        )}

        {/* Grounding Source Citations */}
        {message.sources && message.sources.length > 0 && (
          <SourceCitation sources={message.sources} />
        )}
      </div>
    </div>
  );
}
