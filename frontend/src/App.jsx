import React, { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, BookOpen, Compass, Flame, Layout } from 'lucide-react';
import ChatSidebar from './components/ChatSidebar';
import ModelToggle from './components/ModelToggle';
import MessageBubble from './components/MessageBubble';
import ArtifactViewer from './components/ArtifactViewer';
import IngestionModal from './components/IngestionModal';
import { fetchSessions, createSession, deleteSession, fetchMessages } from './services/api';

const STARTER_PROMPTS = [
  {
    title: "Founder Mode & Being in the Details",
    desc: "What does Brian Chesky say about micromanagement vs. being in the details?",
    icon: Compass,
    query: "What did Brian Chesky say about micromanagement and why founders must be in the details?",
  },
  {
    title: "Ship 30 for 30 Essay on Growth",
    desc: "Generate a formatted ~1,250-word essay about retention and product strategy.",
    icon: Flame,
    query: "Write a Ship 30 for 30 essay about why retention is the silent killer of growth companies based on Lenny's podcast insights.",
  },
  {
    title: "Product-Market Fit Interactive Calculator",
    desc: "Create an interactive HTML/CSS calculator widget for PMF score.",
    icon: Layout,
    query: "Generate an interactive HTML/CSS calculator widget for estimating Product Market Fit score based on Rahul Vohra and Brian Chesky's benchmarks.",
  },
  {
    title: "Marty Cagan on Empowered Teams",
    desc: "How do the best product teams operate compared to feature factories?",
    icon: BookOpen,
    query: "What does Marty Cagan say about empowered product teams vs feature factories?",
  },
];

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeArtifact, setActiveArtifact] = useState(null);
  const [isIngestionModalOpen, setIsIngestionModalOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  async function loadSessions() {
    try {
      const data = await fetchSessions();
      setSessions(data.sessions || []);
      if (data.sessions && data.sessions.length > 0 && !activeSessionId) {
        setActiveSessionId(data.sessions[0].id);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }

  async function loadMessages(sessionId) {
    try {
      const data = await fetchMessages(sessionId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  }

  async function handleNewChat() {
    try {
      const newSession = await createSession('New Chat');
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.id);
      setMessages([]);
      setActiveArtifact(null);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  }

  async function handleDeleteSession(sessionId) {
    try {
      await deleteSession(sessionId);
      const remaining = sessions.filter(s => s.id !== sessionId);
      setSessions(remaining);
      if (activeSessionId === sessionId) {
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
        setActiveArtifact(null);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  }

  async function handleSendMessage(textToSend = null) {
    const text = textToSend || inputValue.trim();
    if (!text || isStreaming) return;

    let currentSessionId = activeSessionId;

    // If no active session, create one
    if (!currentSessionId) {
      try {
        const newSession = await createSession(text.slice(0, 50));
        currentSessionId = newSession.id;
        setSessions([newSession, ...sessions]);
        setActiveSessionId(currentSessionId);
      } catch (err) {
        console.error('Failed to auto-create session:', err);
        return;
      }
    }

    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Optimistically add user message
    const userMsg = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    // Placeholder assistant message for streaming
    const assistantMsgId = `temp-assistant-${Date.now()}`;
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      artifact: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    try {
      const response = await fetch(`/api/sessions/${currentSessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;

          const match = line.match(/^event:\s*(\w+)\ndata:\s*(.+)$/s);
          if (!match) continue;

          const [, eventType, rawData] = match;
          let parsed;
          try {
            parsed = JSON.parse(rawData);
          } catch {
            continue;
          }

          if (eventType === 'chunk') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, content: msg.content + (parsed.content || '') }
                  : msg
              )
            );
          } else if (eventType === 'sources') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, sources: parsed.sources || [] }
                  : msg
              )
            );
          } else if (eventType === 'artifact') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, artifact: parsed }
                  : msg
              )
            );
            // Automatically open artifact in side panel
            setActiveArtifact(parsed);
          } else if (eventType === 'done') {
            loadSessions(); // refresh session titles and counts
          }
        }
      }
    } catch (err) {
      console.error('Streaming error:', err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? { ...msg, content: msg.content + `\n\n*(Error during generation: ${err.message})*` }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }

  function handleTextareaInput(e) {
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        onOpenIngestionModal={() => setIsIngestionModalOpen(true)}
      />

      {/* Main Chat Workspace */}
      <main className="main-chat-area">
        {/* App Header */}
        <header className="app-header">
          <div className="header-title-group">
            <span style={{ fontWeight: 600, fontSize: '15px', color: '#fff' }}>
              Lenny's Knowledge Assistant
            </span>
          </div>

          <ModelToggle />
        </header>

        {/* Message Thread */}
        <div className="messages-container">
          {messages.length === 0 ? (
            /* Welcome / Empty State */
            <div className="welcome-container">
              <div className="welcome-badge">
                <Sparkles size={13} />
                <span>Grounded in 300+ Lenny's Podcast Transcripts</span>
              </div>
              <h1 className="welcome-title">What would you like to build or grow?</h1>
              <p className="welcome-subtitle">
                Ask deep product & growth questions, generate Ship 30 for 30 essays, or create interactive artifacts — all grounded in advice from the world's best product leaders.
              </p>

              <div className="prompt-grid">
                {STARTER_PROMPTS.map((p, idx) => {
                  const Icon = p.icon;
                  return (
                    <div
                      key={idx}
                      className="prompt-card"
                      onClick={() => handleSendMessage(p.query)}
                    >
                      <div className="prompt-card-title">
                        <Icon size={14} color="var(--accent-primary)" />
                        <span>{p.title}</span>
                      </div>
                      <div className="prompt-card-desc">{p.desc}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <MessageBubble
                key={m.id}
                message={m}
                onOpenArtifact={(art) => setActiveArtifact(art)}
              />
            ))
          )}

          {isStreaming && (
            <div style={{ display: 'flex', gap: 14, maxWidth: 820, margin: '0 auto', width: '100%' }}>
              <div className="message-avatar assistant">
                <Sparkles size={18} />
              </div>
              <div className="typing-dots">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="input-container-wrapper">
          <div className="input-container">
            <textarea
              ref={textareaRef}
              className="chat-textarea"
              placeholder="Ask a product/growth question, or request 'Write a Ship 30 essay'..."
              rows={1}
              value={inputValue}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
            />
            <button
              className="send-btn"
              onClick={() => handleSendMessage()}
              disabled={isStreaming || !inputValue.trim()}
              title="Send message (Enter)"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      </main>

      {/* Artifact Viewer Side Panel (Claude-style) */}
      {activeArtifact && (
        <ArtifactViewer
          artifact={activeArtifact}
          onClose={() => setActiveArtifact(null)}
        />
      )}

      {/* Knowledge Base Ingestion Drawer */}
      <IngestionModal
        isOpen={isIngestionModalOpen}
        onClose={() => setIsIngestionModalOpen(false)}
      />
    </div>
  );
}
