# PRD — Lenny Growth Assistant

> Product Requirements Document for the AI-powered growth assistant grounded in Lenny's Podcast & Newsletter transcripts.

---

## 1. Discovery Brief

### 1.1 Problem Statement
Product managers, founders, and growth leads spend dozens of hours searching through audio/video transcripts and newsletters trying to find actionable growth frameworks and tactical advice. Generic AI chat tools frequently hallucinate, lack source attribution, or provide generic platitudes that cannot be cited or trusted for strategic product decisions.

### 1.2 Target User & Jobs to Be Done
* **Primary Persona**: Senior Product Managers, Growth Leads, and Startup Founders.
* **Core Job**: Retrieve authoritative, battle-tested growth and product frameworks backed directly by Lenny Rachitsky's podcast guests, and transform them into publishable essays and actionable frameworks.
* **Pain Points**: Manual search through 300+ podcast hours; untrusted hallucinated advice from general-purpose LLMs.

### 1.3 Success Metrics
| Metric | Target | Measurement Method |
|---|---|---|
| **Citation Rate** | >= 95% | Valid citations attached to all QA answers backed by transcripts |
| **Out-of-Scope Refusal** | >= 90% | Explicit refusal when questions cannot be answered from transcripts |
| **Time to First Token (TTFT)** | < 4.0s | Measured from request start to first streamed SSE token on local 7B model |
| **Essay Target Adherence** | 1,250 words (+-10%) | Word count check on Ship 30 for 30 generated essays |

### 1.4 Core Assumptions
1. **Single-Tenant / Anonymous Auth**: Session identity is keyed by client-generated UUID stored in localStorage (X-Anon-Key).
2. **Local Model Mandatory**: Demo runs fully offline on Ollama (qwen2.5:7b-instruct). Cloud LLMs are optional and toggled via configuration only.
3. **Unified Embeddings**: Local nomic-embed-text (768 dimensions) is used for both local and cloud modes to keep index unified.
4. **Data Source Boundary**: The assistant strictly relies on ingested transcript files and explicitly refuses out-of-scope inquiries.
5. **English Only**: The corpus and interface target English-language content.
6. **Artifact Sandboxing**: Generated HTML/CSS code is treated as untrusted and rendered in isolated sandboxed iframes without script execution.

---

## 2. User Flows

### Flow 1: Grounded QA with Citations
1. User enters a query (e.g., 'How do I know when it is time to leave my job?').
2. Agent rewrites follow-up query based on session history.
3. Vector similarity search retrieves top-k chunks from PostgreSQL pgvector.
4. If similarity < 0.30 threshold, assistant returns explicit refusal: 'The podcast transcripts do not cover this topic.'
5. Otherwise, assistant streams answer with episode titles, guest names, and relevance scores.

### Flow 2: Ship 30 for 30 Essay Generation
1. User requests an essay or deep-dive on a topic (e.g., 'Write a Ship 30 essay on customer retention loops').
2. Intent router classifies intent as essay.
3. System retrieves relevant case studies and frameworks from transcripts.
4. Generator drafts a ~1,250-word structured piece with strong hook, narrative progression, bulleted takeaways, and selective bolding.
5. Essay streams into the chat with transcript citations.

### Flow 3: Artifact Generation & Inspection
1. User prompts for a deliverable (e.g., 'Create an onboarding checklist artifact in HTML').
2. Agent classifies as artifact and generates structured Markdown or HTML.
3. Server-side sanitizer strips script tags, event handlers, iframes, and dangerous attributes.
4. Server stores artifact in artifacts table and streams an artifact event.
5. Frontend side-by-side viewer displays preview in a sandboxed iframe with an 'Allowed / Blocked' inspector panel.

---

## 3. Acceptance Criteria

1. **Independent Session Context**: Creating a new chat session produces an isolated conversation thread that never leaks messages across sessions.
2. **Grounding Integrity**: Assistant never answers from internal pretraining knowledge when retrieval scores are below threshold.
3. **Config-Only Model Switching**: Changing LLM_PROVIDER in .env changes model provider without code modifications.
4. **Error Handling**: Graceful error envelopes returned for MODEL_UNAVAILABLE, MODEL_TIMEOUT, NO_RELEVANT_SOURCES, and DB_UNAVAILABLE.
5. **Sanitization Compliance**: Any generated HTML containing script tags or event handlers must have malicious content stripped before rendering.

---

## 4. Scope

### In Scope
* Multi-session chat interface with persistent history in PostgreSQL.
* Hybrid ingestion pipeline for 303 podcast transcripts into pgvector.
* Local Ollama inference (qwen2.5:7b-instruct + nomic-embed-text).
* Real-time Server-Sent Events (SSE) token streaming.
* Ship 30 for 30 essay generation skill.
* Side-by-side artifact viewer with CSP and iframe sandboxing.
* Complete test suite for API, retrieval, routing, and persistence.

### Out of Scope
* Multi-tenant enterprise SSO / User authentication (anonymous session UUID only).
* Billing, payments, and subscription management.
* Voice/audio synthesis and video rendering.
* Automated real-time YouTube scraping daemon.

---

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Hallucination on small 7B model** | High | Strict system prompt rules, context grounding, and mandatory citation format. |
| **Local LLM Latency** | Medium | Streaming SSE tokens with early TTFT; batching embeddings during ingestion. |
| **Out-of-Scope Queries** | Medium | Vector distance threshold (< 0.30) triggers automatic canned refusal. |
| **XSS from generated HTML** | Critical | Dual-layer security: DOMPurify server/client sanitization + iframe sandbox without allow-scripts or allow-same-origin. |
| **Ollama Service Downtime** | Medium | Pre-flight /config/providers check and structured MODEL_UNAVAILABLE error guidance. |
