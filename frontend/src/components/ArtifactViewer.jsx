import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';
import { X, Copy, Download, Check, ShieldCheck, Eye, Code2 } from 'lucide-react';

export default function ArtifactViewer({ artifact, onClose }) {
  const [activeTab, setActiveTab] = useState('preview');
  const [copied, setCopied] = useState(false);

  if (!artifact) return null;

  const isHtml = artifact.type === 'html';

  function handleCopy() {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const ext = isHtml ? 'html' : 'md';
    const blob = new Blob([artifact.content], { type: isHtml ? 'text/html' : 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(artifact.title || 'artifact').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Sanitize HTML with DOMPurify
  const sanitizedHtml = isHtml ? DOMPurify.sanitize(artifact.content, {
    ADD_TAGS: ['style', 'iframe'],
    ADD_ATTR: ['target', 'style', 'class'],
  }) : '';

  return (
    <div className="artifact-panel">
      {/* Header */}
      <div className="artifact-header">
        <div className="artifact-title-group">
          <span className="artifact-type-badge">
            {isHtml ? 'HTML / CSS' : 'MARKDOWN'}
          </span>
          <span className="artifact-title-text" title={artifact.title}>
            {artifact.title || 'Generated Artifact'}
          </span>
        </div>

        <div className="artifact-actions">
          <button className="artifact-action-btn" onClick={handleCopy}>
            {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button className="artifact-action-btn" onClick={handleDownload}>
            <Download size={13} />
            <span>Download</span>
          </button>
          <button className="artifact-close-btn" onClick={onClose} title="Close Artifact Viewer">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Security Status Banner */}
      <div className="security-notice">
        <ShieldCheck size={13} />
        <span>Sandboxed environment • DOMPurify sanitization active</span>
      </div>

      {/* Tab Switcher */}
      <div className="artifact-tab-bar">
        <button 
          className={`artifact-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Eye size={13} />
            <span>Preview</span>
          </div>
        </button>
        <button 
          className={`artifact-tab ${activeTab === 'code' ? 'active' : ''}`}
          onClick={() => setActiveTab('code')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Code2 size={13} />
            <span>Code</span>
          </div>
        </button>
      </div>

      {/* Body */}
      <div className="artifact-body">
        {activeTab === 'preview' ? (
          isHtml ? (
            <iframe
              title="Artifact Preview"
              className="artifact-iframe"
              sandbox="allow-scripts"
              srcDoc={sanitizedHtml}
            />
          ) : (
            <div className="artifact-markdown-view">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {artifact.content}
              </ReactMarkdown>
            </div>
          )
        ) : (
          <pre className="artifact-code-view">
            <code>{artifact.content}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
