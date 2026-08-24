import React from 'react';
import { Plus, MessageSquare, Trash2, Database, Sparkles } from 'lucide-react';

export default function ChatSidebar({ 
  sessions, 
  activeSessionId, 
  onSelectSession, 
  onNewChat, 
  onDeleteSession,
  onOpenIngestionModal 
}) {
  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-badge">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <div>
            <div style={{ lineHeight: 1.1 }}>Lenny Growth</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400 }}>AI Advisor</div>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={16} />
        <span>New Chat</span>
      </button>

      {/* Sessions List */}
      <div className="session-list">
        <div style={{ padding: '8px 4px 4px', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          Recent Conversations
        </div>
        {sessions.length === 0 ? (
          <div style={{ padding: '16px 8px', fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center' }}>
            No sessions yet
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                className={`session-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectSession(s.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden', flex: 1 }}>
                  <MessageSquare size={14} style={{ flexShrink: 0, opacity: isActive ? 1 : 0.6 }} />
                  <span className="session-title">{s.title || 'New Chat'}</span>
                </div>
                <button
                  className="session-delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  title="Delete Session"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Knowledge Base trigger */}
      <div className="sidebar-footer">
        <button
          onClick={onOpenIngestionModal}
          style={{
            width: '100%',
            padding: '8px 12px',
            backgroundColor: 'var(--bg-tertiary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-secondary)',
            fontSize: '12.5px',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            transition: 'all 150ms ease'
          }}
          onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
          onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-default)'}
        >
          <Database size={14} color="var(--accent-primary)" />
          <span>Manage Transcripts</span>
        </button>
      </div>
    </aside>
  );
}
