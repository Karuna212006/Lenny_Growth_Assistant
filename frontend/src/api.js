/**
 * Lenny Growth Assistant - API Client
 *
 * Handles anonymous user identity (X-Anon-Key header), REST calls, and SSE streaming.
 * Communicates strictly with the backend API.
 * Never produces, caches, or fakes assistant text or citations.
 */

const STORAGE_KEY = 'lenny_growth_anon_key';

export function getAnonKey() {
  let key = localStorage.getItem(STORAGE_KEY);
  if (!key) {
    key = 'anon-' + (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2));
    localStorage.setItem(STORAGE_KEY, key);
  }
  return key;
}

const getHeaders = () => ({
  'Content-Type': 'application/json',
  'X-Anon-Key': getAnonKey(),
});

export async function fetchConfig() {
  const res = await fetch('/config/providers');
  if (!res.ok) {
    let errorData = null;
    try {
      errorData = await res.json();
    } catch (_) {}
    const err = new Error(errorData?.error?.message || `Failed to fetch provider config: HTTP ${res.status}`);
    err.error = errorData?.error || {
      code: 'HTTP_ERROR',
      message: err.message,
    };
    throw err;
  }
  return await res.json();
}

export async function fetchSessions() {
  const res = await fetch('/sessions', { headers: getHeaders() });
  if (!res.ok) {
    let errorData = null;
    try {
      errorData = await res.json();
    } catch (_) {}
    const err = new Error(errorData?.error?.message || `Failed to fetch sessions: HTTP ${res.status}`);
    err.error = errorData?.error || {
      code: 'HTTP_ERROR',
      message: err.message,
    };
    throw err;
  }
  return await res.json();
}

export async function createSession(title = 'New chat') {
  const res = await fetch('/sessions', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ title }),
  });
  if (!res.ok) {
    let errorData = null;
    try {
      errorData = await res.json();
    } catch (_) {}
    const err = new Error(errorData?.error?.message || `Failed to create session: HTTP ${res.status}`);
    err.error = errorData?.error || {
      code: 'HTTP_ERROR',
      message: err.message,
    };
    throw err;
  }
  return await res.json();
}

export async function fetchSession(sessionId) {
  const res = await fetch(`/sessions/${sessionId}`, { headers: getHeaders() });
  if (!res.ok) {
    let errorData = null;
    try {
      errorData = await res.json();
    } catch (_) {}
    const err = new Error(errorData?.error?.message || `Failed to fetch session detail: HTTP ${res.status}`);
    err.error = errorData?.error || {
      code: 'HTTP_ERROR',
      message: err.message,
    };
    throw err;
  }
  return await res.json();
}

export async function fetchArtifact(artifactId) {
  const res = await fetch(`/artifacts/${artifactId}`, { headers: getHeaders() });
  if (!res.ok) {
    let errorData = null;
    try {
      errorData = await res.json();
    } catch (_) {}
    const err = new Error(errorData?.error?.message || `Failed to fetch artifact: HTTP ${res.status}`);
    err.error = errorData?.error || {
      code: 'HTTP_ERROR',
      message: err.message,
    };
    throw err;
  }
  return await res.json();
}

/**
 * Stream chat message via SSE.
 * Client timeout is set to 180 seconds.
 * Yields server events to callbacks. If an error occurs, invokes onError with
 * the structured error shape { code, message, request_id }.
 */
export async function streamMessage(sessionId, content, callbacks) {
  const { onToken, onStatus, onCitations, onArtifact, onDone, onError } = callbacks;

  try {
    const response = await fetch(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ content }),
      signal: AbortSignal.timeout(180000), // 180s timeout
    });

    if (!response.ok) {
      let errShape = null;
      try {
        const json = await response.json();
        errShape = json.error || json;
      } catch (_) {
        errShape = {
          code: response.status === 503 ? 'DB_UNAVAILABLE' : (response.status === 504 ? 'MODEL_TIMEOUT' : 'HTTP_ERROR'),
          message: `Server returned HTTP ${response.status}`,
        };
      }
      onError && onError(errShape);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let currentEvent = 'message';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.substring(6).trim();
          continue;
        }

        if (trimmed.startsWith('data:')) {
          const rawData = trimmed.substring(5).trim();
          try {
            const data = JSON.parse(rawData);
            if (currentEvent === 'token') {
              const tokenStr = typeof data === 'string' ? data : (data?.text ?? data?.token ?? '');
              if (tokenStr) onToken && onToken(tokenStr);
            } else if (currentEvent === 'status') {
              const statusStr = typeof data === 'string' ? data : (data?.message || data?.step || data?.status || '');
              onStatus && onStatus(statusStr);
            } else if (currentEvent === 'citations') {
              onCitations && onCitations(Array.isArray(data) ? data : data.citations || []);
            } else if (currentEvent === 'artifact') {
              onArtifact && onArtifact(data);
            } else if (currentEvent === 'done') {
              onDone && onDone(data);
            } else if (currentEvent === 'error') {
              const errObj = typeof data === 'object' ? data : { code: 'MODEL_UNAVAILABLE', message: String(data) };
              onError && onError(errObj);
            }
          } catch (e) {
            console.error('SSE JSON parse error:', e);
          }
        }
      }
    }
  } catch (err) {
    const isTimeout = err.name === 'TimeoutError';
    const errShape = {
      code: isTimeout ? 'MODEL_TIMEOUT' : 'NETWORK_ERROR',
      message: isTimeout
        ? 'Request timed out after 180 seconds'
        : (err.message || 'Network error communicating with server'),
    };
    onError && onError(errShape);
  }
}
