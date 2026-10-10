import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  PanelRight,
  Loader2,
  FileText,
  AlertCircle,
  Menu,
  Copy,
  Check,
  PlusCircle,
  Compass,
  Briefcase,
  Users,
  Repeat,
  PenTool,
  CheckCircle2,
  Radio,
  RotateCcw
} from 'lucide-react';
import Sidebar from './components/Sidebar';
import Citations from './components/Citations';
import ArtifactViewer from './components/ArtifactViewer';
import { PromptInput } from './components/ui/ai-chat-input';
import {
  fetchConfig,
  fetchSessions,
  createSession,
  fetchSession,
  streamMessage,
  fetchArtifact,
} from './api';

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [providerConfig, setProviderConfig] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [activeArtifact, setActiveArtifact] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [streamError, setStreamError] = useState(null);
  const [copiedMsgId, setCopiedMsgId] = useState(null);

  const messagesEndRef = useRef(null);

  // Initial load: config and sessions
  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const config = await fetchConfig();
        if (isMounted) setProviderConfig(config);
      } catch (e) {
        console.warn('Could not load provider config:', e);
      }

      try {
        const sessionList = await fetchSessions();
        if (isMounted) {
          setSessions(sessionList);
          if (sessionList && sessionList.length > 0) {
            selectSession(sessionList[0].id);
          } else {
            handleNewSession();
          }
        }
      } catch (e) {
        console.error('Failed to load sessions:', e);
        if (isMounted) {
          setStreamError({
            code: e.error?.code || 'NETWORK_ERROR',
            message: e.error?.message || e.message || 'Cannot connect to backend server. Make sure the API service is running.',
            request_id: e.error?.request_id || null,
            onRetry: init,
          });
        }
      }
    }
    init();

    return () => {
      isMounted = false;
    };
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, statusMessage, streamError]);

  const selectSession = async (sessionId) => {
    if (!sessionId) return;
    setActiveSessionId(sessionId);
    setStreamError(null);
    try {
      const detail = await fetchSession(sessionId);
      setMessages(detail.messages || []);
      if (detail.artifacts && detail.artifacts.length > 0) {
        const lastArt = detail.artifacts[detail.artifacts.length - 1];
        const art = await fetchArtifact(lastArt.id || lastArt.artifact_id);
        setActiveArtifact(art);
      } else {
        setActiveArtifact(null);
      }
    } catch (err) {
      console.error('Error fetching session detail:', err);
      setStreamError({
        code: err.error?.code || 'NETWORK_ERROR',
        message: err.error?.message || err.message || 'Failed to load conversation messages.',
        request_id: err.error?.request_id || null,
        onRetry: () => selectSession(sessionId),
      });
    }
  };

  const handleNewSession = async () => {
    try {
      const newSess = await createSession('Product & Growth Strategy');
      setSessions((prev) => [newSess, ...prev.filter((s) => s.id !== newSess.id)]);
      setActiveSessionId(newSess.id);
      setMessages([]);
      setActiveArtifact(null);
      setStreamError(null);
    } catch (err) {
      console.error('Error creating new session:', err);
      setStreamError({
        code: err.error?.code || 'NETWORK_ERROR',
        message: err.error?.message || err.message || 'Failed to create new session on server.',
        request_id: err.error?.request_id || null,
        onRetry: handleNewSession,
      });
    }
  };

  const handleCopyMessage = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const handleSendMessage = async (textToSend, meta) => {
    const prompt = (textToSend || inputPrompt).trim();
    if (!prompt || isStreaming) return;

    setStreamError(null);

    // Guarantee that an active session exists
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      try {
        const newSess = await createSession(prompt.slice(0, 36) + '...');
        setSessions((prev) => [newSess, ...prev]);
        setActiveSessionId(newSess.id);
        currentSessionId = newSess.id;
      } catch (e) {
        setStreamError({
          code: e.error?.code || 'NETWORK_ERROR',
          message: e.error?.message || e.message || 'Failed to initialize session on backend.',
          request_id: e.error?.request_id || null,
          retryPrompt: prompt,
          onRetry: () => handleSendMessage(textToSend, meta),
        });
        return;
      }
    }

    setInputPrompt('');
    setIsStreaming(true);
    setStatusMessage('Searching transcripts...');

    // Optimistically append user message
    const tempUserMsg = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: prompt,
      created_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    // Prepare placeholder assistant message
    const assistantMsgId = 'asst-' + Date.now();
    let currentAssistantText = '';
    let currentCitations = [];

    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        citations: [],
        created_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);

    await streamMessage(currentSessionId, prompt, {
      onStatus: (status) => {
        setStatusMessage(status);
      },
      onToken: (token) => {
        if (!token || typeof token !== 'string') return;
        setStatusMessage(null);
        currentAssistantText += token;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: currentAssistantText } : m
          )
        );
      },
      onCitations: (cites) => {
        currentCitations = cites;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, citations: currentCitations } : m
          )
        );
      },
      onArtifact: async (artData) => {
        if (artData?.artifact_id || artData?.id) {
          try {
            const artId = artData.artifact_id || artData.id;
            const fullArt = await fetchArtifact(artId);
            setActiveArtifact(fullArt || artData);
          } catch (e) {
            setActiveArtifact(artData);
          }
        }
      },
      onDone: (doneData) => {
        setIsStreaming(false);
        setStatusMessage(null);
        fetchSessions().then(setSessions).catch(() => {});
      },
      onError: (errShape) => {
        setIsStreaming(false);
        setStatusMessage(null);
        // Remove empty assistant placeholder so we never display fake or broken assistant text
        if (!currentAssistantText) {
          setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId));
        }
        setStreamError({
          code: errShape?.code || 'ERROR',
          message: errShape?.message || 'Error communicating with Lenny Growth Assistant.',
          request_id: errShape?.request_id || null,
          retryPrompt: prompt,
        });
      },
    });
  };

  const suggestions = [
    {
      icon: <Briefcase size={16} className="text-amber-500" />,
      title: "When to leave your job",
      guest: "Ada Chen Rekhi",
      tag: "Career Inflection",
      query: "What does Ada Chen Rekhi advise about knowing when it's time to leave your job?",
    },
    {
      icon: <Users size={16} className="text-blue-400" />,
      title: "Building high-velocity growth teams",
      guest: "Adam Fishman",
      tag: "Hiring & Structure",
      query: "How do you structure and hire for a high-performing growth team according to Adam Fishman?",
    },
    {
      icon: <Repeat size={16} className="text-emerald-400" />,
      title: "Growth loops over marketing funnels",
      guest: "Elena Verna & Brian Balfour",
      tag: "Retention & PLG",
      query: "Explain why growth loops defeat marketing funnels based on Elena Verna and Brian Balfour's insights.",
    },
    {
      icon: <PenTool size={16} className="text-orange-400" />,
      title: "Write a Ship 30 essay on retention",
      guest: "Framework Deep Dive",
      tag: "Artifact Generator",
      query: "Write a Ship 30 for 30 essay on customer retention loops grounded in Lenny's podcasts.",
    },
  ];

  const currentSession = sessions.find((s) => s.id === activeSessionId);
  const activeModel = providerConfig?.active?.model || 'qwen2.5:7b-instruct';

  return (
    <div className="app-layout dark">
      {/* Sessions Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={(id) => {
            selectSession(id);
            setSidebarOpen(false);
          }}
          onNewSession={() => {
            handleNewSession();
            setSidebarOpen(false);
          }}
          providerConfig={providerConfig}
        />
      </div>

      {/* Main Chat Area */}
      <main className="chat-main">
        {/* Ambient Top Glow */}
        <div className="ambient-glow"></div>

        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-info">
            <button
              className="btn-header-action mobile-menu-btn"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title="Toggle Sidebar"
              id="btn-sidebar-toggle"
            >
              <Menu size={16} />
            </button>
            <div className="chat-header-title-container">
              <span className="chat-header-title">
                {currentSession?.title || 'Lenny Growth Assistant'}
              </span>
              <div className="status-pill-header">
                <span className="status-dot"></span>
                <span>{activeModel.split(':')[0]}</span>
              </div>
            </div>
          </div>

          <div className="chat-header-actions">
            <button
              className="btn-header-action"
              onClick={handleNewSession}
              title="Start a new chat"
            >
              <PlusCircle size={14} />
              <span>New Chat</span>
            </button>

            {activeArtifact && (
              <button
                className="btn-header-action active"
                onClick={() => setActiveArtifact(activeArtifact ? null : activeArtifact)}
                title="Toggle Artifact Panel"
              >
                <FileText size={14} />
                <span>Artifact</span>
                <span className="artifact-active-dot"></span>
              </button>
            )}
          </div>
        </header>

        {/* Message Feed */}
        <div className="messages-container">
          <div className="messages-inner">
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-badge">
                  <Sparkles size={12} className="text-amber-400" />
                  <span>GROUNDED IN 300+ PODCASTS & ESSAYS</span>
                </div>

                <div className="empty-logo-glow">
                  <div className="empty-logo">
                    <Sparkles size={30} color="#ffffff" />
                  </div>
                </div>

                <h1 className="empty-title">
                  Tactical Product & Growth Advice
                </h1>
                <p className="empty-subtitle">
                  Ask tactical product, career, and growth questions strictly grounded in transcripts
                  from Lenny's Podcast and Newsletter archives.
                </p>

                <div className="prompt-suggestions">
                  {suggestions.map((s, idx) => (
                    <div
                      key={idx}
                      className="suggestion-card"
                      onClick={() => handleSendMessage(s.query)}
                      tabIndex={0}
                      role="button"
                    >
                      <div className="suggestion-card-header">
                        <div className="suggestion-icon-wrap">{s.icon}</div>
                        <span className="suggestion-tag">{s.tag}</span>
                      </div>
                      <strong className="suggestion-title">{s.title}</strong>
                      <span className="suggestion-guest">{s.guest} · Click to ask</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m) => (
                <div key={m.id} className={`message-row ${m.role} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                  {m.role === 'assistant' && (
                    <div className="avatar assistant">
                      <Bot size={18} />
                    </div>
                  )}

                  <div className="message-content-wrapper">
                    <div className="message-meta-header">
                      <span className="message-sender">
                        {m.role === 'assistant' ? 'Lenny Copilot' : 'You'}
                      </span>
                      {m.created_at && (
                        <span className="message-timestamp">{m.created_at}</span>
                      )}
                    </div>

                    <div className="message-bubble">
                      <div className="message-text">
                        {m.content}
                        {isStreaming && m.role === 'assistant' && !m.content && (
                          <span className="streaming-cursor"></span>
                        )}
                        {isStreaming && m.role === 'assistant' && m.content && (
                          <span className="streaming-cursor"></span>
                        )}
                      </div>

                      {m.citations && m.citations.length > 0 && (
                        <Citations citations={m.citations} />
                      )}

                      {m.role === 'assistant' && m.content && !isStreaming && (
                        <div className="message-toolbar">
                          <button
                            className="btn-toolbar-action"
                            onClick={() => handleCopyMessage(m.content, m.id)}
                            title="Copy response"
                          >
                            {copiedMsgId === m.id ? (
                              <>
                                <Check size={12} className="text-emerald-400" />
                                <span>Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy size={12} />
                                <span>Copy</span>
                              </>
                            )}
                          </button>

                          {activeArtifact && (
                            <button
                              className="btn-toolbar-action"
                              onClick={() => setActiveArtifact(activeArtifact)}
                              title="View Generated Artifact"
                            >
                              <FileText size={12} />
                              <span>View Artifact</span>
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {m.role === 'user' && (
                    <div className="avatar user">
                      <User size={18} />
                    </div>
                  )}
                </div>
              ))
            )}

            {statusMessage && (
              <div className="status-message-wrapper">
                <div className="status-indicator">
                  <Loader2 size={13} className="spin-icon" />
                  <span>{statusMessage}</span>
                </div>
              </div>
            )}

            {streamError && (
              <div className="error-banner animate-in fade-in slide-in-from-bottom-2 duration-200" role="alert">
                <div className="error-banner-icon">
                  <AlertCircle size={18} className="text-red-400" />
                </div>
                <div className="error-banner-content">
                  <div className="error-banner-header">
                    <span className="error-banner-code">[{streamError.code}]</span>
                    {streamError.request_id && (
                      <span className="error-banner-req">req: {streamError.request_id}</span>
                    )}
                  </div>
                  <p className="error-banner-text">{streamError.message}</p>
                </div>
                <button
                  className="btn-retry"
                  onClick={() => {
                    const err = streamError;
                    setStreamError(null);
                    if (err.onRetry) {
                      err.onRetry();
                    } else if (err.retryPrompt) {
                      handleSendMessage(err.retryPrompt);
                    }
                  }}
                  id="btn-retry-action"
                >
                  <RotateCcw size={14} />
                  <span>Retry</span>
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Floating AI Chat Input */}
        <div className="input-container">
          <PromptInput
            value={inputPrompt}
            onChange={setInputPrompt}
            onSubmit={(val, meta) => handleSendMessage(val, meta)}
            placeholder="Ask a tactical growth question or request an essay / artifact..."
            models={[
              activeModel,
              "deepseek-r1",
              "llama3.1:8b",
              "Composer 2.5",
              "GPT 5.5",
            ]}
            efforts={["Standard", "Deep Analysis", "Ship 30 Essay"]}
            disabled={isStreaming}
          />
        </div>
      </main>

      {/* Side-by-Side Artifact Viewer */}
      {activeArtifact && (
        <ArtifactViewer
          artifact={activeArtifact}
          onClose={() => setActiveArtifact(null)}
        />
      )}
    </div>
  );
}
