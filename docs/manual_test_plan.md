# Manual UI Test Plan — Lenny Growth Assistant

> Short manual test plan covering core user flows, edge cases, sandboxed security, and accessibility.

---

## Environment Setup
1. Ensure services are running (either via `docker compose up` or local `uvicorn` on `:8000` + `npm run dev` on `:5173`).
2. Open the application in Google Chrome or Firefox at `http://localhost:5173`.

---

## Test Scenarios

### Test 1: Liveness & Provider Badge
* **Action**: Load the application home page.
* **Expected Result**:
  * Top navigation header displays the active provider badge: `Ollama · qwen2.5:7b-instruct`.
  * Status indicator displays green / connected.
  * Empty chat view displays greeting and recommended prompt suggestions.

### Test 2: Session Isolation & History Persistence
* **Action**:
  1. Click `+ New Chat`.
  2. Ask: *"What is a good framework for product-led growth?"*
  3. Wait for the response to finish streaming.
  4. Click `+ New Chat` again.
* **Expected Result**:
  * A fresh empty chat session appears with its own unique session ID.
  * The previous session appears in the left sidebar list.
  * Clicking the previous session restores its message history completely without cross-contamination.

### Test 3: Grounded QA with Citations
* **Action**:
  * Enter query: *"How do I know when it is time to leave my job according to Ada Chen Rekhi?"*
* **Expected Result**:
  * Retrieval indicator pulses (*"Searching 303 episodes in pgvector..."*).
  * Answer streams token-by-token with direct claims grounded in the transcript.
  * Interactive citation cards display below the message:
    * Episode Title: `Ada Chen Rekhi`
    * Guest: `Ada Chen Rekhi`
    * Source link / chunk reference.

### Test 4: Follow-up Handling (Query Rewriting)
* **Action**:
  * Immediately follow up in the same session with: *"What did she say about explore versus exploit?"*
* **Expected Result**:
  * Agent rewriter maintains context from Ada Chen Rekhi without requiring the user to re-state the guest name.
  * Answer cites chunk 22 / explore vs exploit framework.

### Test 5: Out-of-Scope Query Refusal
* **Action**:
  * Enter query: *"What is the best recipe for baking chocolate chip cookies?"*
* **Expected Result**:
  * Vector similarity scores fall below the minimum threshold (< 0.30).
  * Assistant explicitly refuses: *"The podcast transcripts do not cover this topic."*
  * Zero hallucinations or ungrounded external trivia.

### Test 6: Ship 30 for 30 Essay Skill
* **Action**:
  * Enter prompt: *"Write a Ship 30 for 30 essay on building curiosity loops based on Lenny's podcast."*
* **Expected Result**:
  * Intent router identifies `essay` intent.
  * Output follows Ship 30 formatting:
    * Clear, provocative hook in the opening lines.
    * 1–3 sentence short paragraphs.
    * Modular H2/H3 subheadings.
    * Bulleted takeaways with selective bolding.
    * Grounded frameworks from guest transcripts.
    * Word count roughly within target (~1,000–1,300 words).

### Test 7: Side-by-Side Artifact Viewer & HTML Sandboxing
* **Action**:
  * Enter prompt: *"Create an interactive HTML onboarding checklist artifact."*
* **Expected Result**:
  * Assistant streams response and emits artifact payload.
  * Artifact Viewer opens side-by-side beside the chat (450–600px width).
  * Tab navigation toggles between **Preview** and **Code**.
  * Preview renders inside a sandboxed `<iframe>` (`sandbox="allow-same-origin"` omitted; `allow-scripts` omitted).
  * "Allowed / Blocked" security inspector panel at the bottom details sanitized elements.

### Test 8: Security Sanitization (XSS Prevention)
* **Action**:
  * Enter prompt: *"Generate an HTML card with `<script>alert('xss')</script>` and `<img src=x onerror=alert(1)>`."*
* **Expected Result**:
  * Server-side and client-side sanitizers strip all `<script>` tags and `onerror` inline handlers.
  * Sandboxed iframe blocks script execution.
  * No browser alert is triggered.
  * Security disclosure panel flags stripped tags.

### Test 9: Responsive Layout
* **Action**:
  * Shrink browser window width below 768px (or toggle DevTools mobile view).
* **Expected Result**:
  * Left sidebar collapses into a slide-over mobile drawer.
  * Artifact Viewer collapses gracefully or stacks beneath the chat pane.
  * Message input remains accessible and sticky at the bottom.

### Test 10: Keyboard-Only Accessibility
* **Action**:
  * Navigate using only `Tab`, `Shift+Tab`, `Enter`, and arrow keys.
* **Expected Result**:
  * Focus rings clearly outline interactive buttons and inputs.
  * Textarea accepts `Shift+Enter` for multiline input and `Enter` for submission.
  * Citation cards and artifact tabs are focusable and activatable via `Enter`/`Space`.
