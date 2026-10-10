import React, { useState } from 'react';
import {
  MessageSquarePlus,
  MessageSquare,
  Sparkles,
  Search,
  Trash2,
  Database,
  Radio,
  BookOpen
} from 'lucide-react';

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  providerConfig,
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const activeProvider = providerConfig?.active?.provider || 'ollama';
  const activeModel = providerConfig?.active?.model || 'qwen2.5:7b-instruct';

  const filteredSessions = (sessions || []).filter((s) =>
    (s.title || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="sidebar-inner-content">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-title">
          <div className="brand-icon">
            <Sparkles size={16} />
          </div>
          <div className="brand-text-container">
            <span className="brand-name">Lenny Assistant</span>
            <span className="brand-tag">Growth & PM Copilot</span>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="sidebar-action-container">
        <button className="btn-new-chat" onClick={onNewSession} id="btn-new-chat">
          <MessageSquarePlus size={16} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Search Sessions */}
      {sessions.length > 3 && (
        <div className="sidebar-search-box">
          <Search size={13} className="search-icon" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="sidebar-search-input"
          />
        </div>
      )}

      {/* Sessions List */}
      <div className="session-list-section">
        <div className="session-list-header">
          <span>Conversations</span>
          <span className="session-count-badge">{filteredSessions.length}</span>
        </div>

        <div className="session-list">
          {filteredSessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${s.id === activeSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(s.id)}
              title={s.title}
            >
              <div className="session-item-left">
                <MessageSquare size={14} className="session-icon" />
                <span className="session-item-title">
                  {s.title || 'Untitled Conversation'}
                </span>
              </div>
            </div>
          ))}

          {filteredSessions.length === 0 && (
            <div className="empty-sessions-notice">
              {searchTerm ? 'No matches found' : 'No conversations yet.'}
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <div className="footer-status-card">
          <div className="footer-status-header">
            <div className="status-label-group">
              <span className="status-dot-pulse"></span>
              <span className="footer-status-title">RAG Engine Active</span>
            </div>
            <span className="rag-badge">300+ eps</span>
          </div>

          <div className="provider-pill">
            <Radio size={12} className="provider-icon" />
            <span className="provider-name">{activeProvider}</span>
            <span className="model-chip">{activeModel.split(':')[0]}</span>
          </div>
        </div>

        <div className="footer-links">
          <div className="footer-link-item">
            <BookOpen size={12} />
            <span>Lenny's Newsletter & Podcast Archives</span>
          </div>
        </div>
      </div>
    </div>
  );
}
