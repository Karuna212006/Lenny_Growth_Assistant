# Design ? Lenny Growth Assistant

> UI/UX design specifications, information architecture, interaction states, and accessibility guidelines.

---

## 1. UI/UX Principles

The interface follows the **Impeccable** design standard, focusing on speed, trustworthy source visibility, and clear separation between conversation and generated artifacts:

1. **Grounded Transparency**: Every piece of tactical advice surfaces its origin immediately with guest name, episode title, and relevance score chip.
2. **Side-by-Side Focus**: Artifacts (checklists, code, essays) open alongside the conversation rather than replacing or cluttering the message stream.
3. **Live Streaming Feedback**: Progressive token streaming with unambiguous visual states (retrieving sources -> synthesizing -> complete).
4. **Resilient Simplicity**: Dark-mode-first aesthetic with crisp typography, balanced contrast, and subtle border hierarchy.

---

## 2. Information Architecture

The application adopts a **3-Pane Desktop Layout**:

```
+------------------+----------------------------------+----------------------------------+
|  Sessions        |  Chat & Conversation Stream      |  Artifact Viewer (Collapsible)   |
|  Sidebar (260px) |  (Center Feed, Flex-1)           |  (Side-by-Side Pane, 450-600px)  |
|                  |                                  |                                  |
|  [+ New Chat]    |  [Provider Badge: Ollama Qwen]   |  [Tabs: Preview | Code]          |
|                  |                                  |                                  |
|  * Recent Chat 1 |  User: 'How to build loops?'     |  +-----------------------------+ |
|  * Recent Chat 2 |  Assistant: 'Based on...'        |  | Sandboxed Iframe Preview    | |
|  * Recent Chat 3 |  [Citation Chips: Casey Winters] |  | or Markdown Document        | |
|                  |                                  |  +-----------------------------+ |
|                  |  [Input: Ask Lenny's guests...]  |  [Allowed / Blocked Security]   |
+------------------+----------------------------------+----------------------------------+
```

### Component Breakdown
* **Left Sidebar (260px)**:
  * Persistent list of anonymous user sessions ordered by `updated_at DESC`.
  * One-click session creation (`+ New Chat`).
* **Center Chat Pane**:
  * Top bar displaying the active provider and model badge (`Ollama ? qwen2.5:7b-instruct`).
  * Message history with distinct visual treatment for user vs assistant.
  * Interactive citation cards linking to episode metadata.
  * Auto-resizing prompt textarea with submit shortcut (`Enter` to send, `Shift+Enter` for newline).
* **Right Artifact Viewer (Collapsible)**:
  * Synchronized with `artifact` SSE events.
  * Tabbed interface: **Preview** (rendered HTML/Markdown) and **Code** (raw source).
  * Quick action buttons: Copy code and Download file.
  * Security disclosure panel showing allowed vs stripped tags.

---

## 3. Key Interaction States

1. **Empty State**: Friendly greeting highlighting suggested prompts (e.g., *'Ada Chen Rekhi on leaving your job'*, *'Elena Verna on B2B product-led growth'*).
2. **Retrieval State**: Subtle spinner/pulse stating *'Searching 303 episodes in pgvector...'* before first token arrives.
3. **Streaming State**: Live markdown rendering token-by-token with active blinking cursor.
4. **No-Sources Refusal State**: Informative badge explaining that the topic was not discussed in the podcast, preventing hallucinations.
5. **Error State**: Non-blocking toast / banner showing structured error code (e.g., `MODEL_UNAVAILABLE`) with concrete resolution steps.

---

## 4. Responsive Behaviour

* **Desktop (>= 1024px)**: Full 3-pane side-by-side view.
* **Tablet (768px - 1023px)**: Sidebar collapses into a slide-out drawer; chat and artifact viewer split screen 50/50.
* **Mobile (< 768px)**: Single pane view. The artifact viewer opens as a full-screen bottom sheet with swipe-to-dismiss.

---

## 5. Accessibility Considerations

* **Keyboard Navigation**: All interactive elements (sessions, buttons, chips, tabs) are reachable via `Tab` and triggerable via `Enter`/`Space`.
* **Screen Reader Announcer**: Live streaming assistant messages use an `aria-live="polite"` container to notify screen readers without interrupting.
* **Color Contrast**: All text elements meet WCAG AA standards (minimum 4.5:1 contrast ratio against dark backgrounds).
* **Focus States**: High-visibility outline focus rings on all interactive elements.

---

## 6. Design Decisions & Security

### Why Iframe Sandboxing for HTML Artifacts?
Generated HTML from an LLM must be treated as untrusted input. Directly rendering it via `dangerouslySetInnerHTML` on the main application DOM would expose users to cross-site scripting (XSS), cookie/localStorage theft, or malicious redirections.

**Security Architecture**:
1. **Server Sanitization**: `bleach` / `DOMPurify` strips `<script>`, inline event handlers (`onload`, `onerror`), and external script tags before storage.
2. **Isolated Sandbox**: The iframe is created with:
   ```html
   <iframe sandbox="allow-forms" srcdoc="..." />
   ```
   Notice that neither `allow-scripts` nor `allow-same-origin` is granted.
3. **Strict Content Security Policy (CSP)**: Injected directly into the iframe header:
   ```http
   default-src 'none'; style-src 'unsafe-inline'; img-src data:;
   ```
4. **Audit Panel**: The viewer includes an explicit 'Allowed / Blocked' badge so evaluators can inspect stripped constructs in real-time.
