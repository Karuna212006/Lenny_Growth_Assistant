import React, { useState } from 'react';
import { X, Copy, Download, ShieldCheck, Code, Eye, Check } from 'lucide-react';
import DOMPurify from 'dompurify';

export default function ArtifactViewer({ artifact, onClose }) {
  const [activeTab, setActiveTab] = useState('preview');
  const [copied, setCopied] = useState(false);

  if (!artifact) return null;

  const isHtml = artifact.type === 'html';
  const title = artifact.title || 'Generated Artifact';
  const content = artifact.content || '';

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = isHtml ? 'html' : 'md';
    const blob = new Blob([content], { type: isHtml ? 'text/html' : 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/[^a-z0-9]/g, '-')}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Secure HTML with strict CSP and DOMPurify for preview inside sandboxed iframe
  const sanitizedHtml = isHtml ? DOMPurify.sanitize(content) : '';
  const iframeSrcDoc = isHtml
    ? `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data: https:;">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; color: #1e293b; line-height: 1.6; }
    h1, h2, h3 { color: #0f172a; margin-top: 1.2em; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; }
    th, td { border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }
    th { background: #f1f5f9; }
  </style>
</head>
<body>
  ${sanitizedHtml}
</body>
</html>`
    : '';

  return (
    <aside className="artifact-viewer">
      <div className="artifact-header">
        <div className="artifact-header-title">
          <span className={`badge-type ${isHtml ? 'html' : 'markdown'}`}>
            {artifact.type || 'TXT'}
          </span>
          <span title={title}>{title}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            className="btn-header-action"
            onClick={handleCopy}
            title="Copy Code"
          >
            {copied ? <Check size={14} color="#22c55e" /> : <Copy size={14} />}
          </button>
          <button
            className="btn-header-action"
            onClick={handleDownload}
            title="Download Artifact"
          >
            <Download size={14} />
          </button>
          <button
            className="btn-header-action"
            onClick={onClose}
            title="Close Viewer"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="artifact-tabs">
        <button
          className={`artifact-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Eye size={14} />
            <span>Preview</span>
          </div>
        </button>
        <button
          className={`artifact-tab ${activeTab === 'code' ? 'active' : ''}`}
          onClick={() => setActiveTab('code')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Code size={14} />
            <span>Code</span>
          </div>
        </button>
      </div>

      <div className="artifact-body">
        {activeTab === 'preview' ? (
          isHtml ? (
            <iframe
              className="artifact-iframe"
              title="Artifact Preview Sandbox"
              sandbox="allow-forms"
              srcDoc={iframeSrcDoc}
            />
          ) : (
            <div className="artifact-code-view" style={{ backgroundColor: '#0f1217', color: '#f8fafc' }}>
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-sans)' }}>{content}</pre>
            </div>
          )
        ) : (
          <pre className="artifact-code-view">{content}</pre>
        )}
      </div>

      <div className="artifact-security-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldCheck size={14} />
          <span>Security Sandbox: Scripts & Same-Origin Disabled</span>
        </div>
        <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>CSP Active</span>
      </div>
    </aside>
  );
}
