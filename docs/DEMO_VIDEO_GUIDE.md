# Demo Video Guide & Walkthrough Script — Lenny Growth Assistant

> **Deliverable 8 Specification**: 2–3 minutes total duration, **camera on** (facecam visible), uploaded to **YouTube** (Public or Unlisted).

This guide provides the complete blueprint for recording the 2–3 minute video walkthrough of the **Lenny Growth Assistant**, ensuring all mandatory requirements from the assignment brief are hit with zero wasted time.

---

## 1. Video Requirements & Evaluation Rubric

| Requirement | Brief Specification | How We Satisfy It |
|---|---|---|
| **Length** | **2–3 minutes** (hard limit, stay under 3:15) | Structured 6-scene script timed to ~2 minutes 45 seconds |
| **Presenter** | **Camera ON** (face visible) | Use OBS Studio, Loom, or Screen Studio with floating webcam overlay |
| **Mandatory LLM** | **Ollama Local Model** | Header displays `Ollama · qwen2.5:7b-instruct` provider badge |
| **Corpus Grounding** | **Lenny's Podcast Transcripts** | 303 episodes / 19,434 chunks in PostgreSQL with pgvector |
| **Citations** | **Visible Attribution** | Answers cite source chunks `[S1]`, `[S2]` with interactive episode cards |
| **Refusal Path** | **Strict Grounding Guarantee** | Out-of-scope queries (< 0.30 similarity) are explicitly refused |
| **Skill Implementation** | **Ship 30 for 30 Framework** | Deep essay generator (~1,250 words, hook, bullets, bolding, grounded claims) |
| **Artifacts** | **Side-by-Side Sandboxed Viewer** | In-app iframe renderer beside chat with "Allowed / Blocked" security inspector |
| **Platform** | **YouTube** | Uploaded as Unlisted or Public; link included in `README.md` |

---

## 2. Pre-Recording Setup & Checklist

### Step 1: Start Services & Verify Health
Make sure Docker / local services are active before hitting record:

```bash
# Verify Ollama is running and models are loaded
ollama list
# Should show: qwen2.5:7b-instruct and nomic-embed-text

# Start Docker containers (or verify local FastAPI & Vite)
docker compose up -d

# Check API readiness
curl http://localhost:8000/health/ready
# Expected: {"status":"ready","database":"connected","provider":"ollama",...}
```

### Step 2: Prepare the Browser
1. Open Chrome/Brave/Edge in full screen at `http://localhost:5173`.
2. Clear previous session or click **`+ New Chat`** so the screen starts clean.
3. Ensure zoom level is comfortable (100% or 110%) so font sizes and citation cards are easily readable on video.

### Step 3: Screen & Webcam Setup
- **Tool Options**:
  - **Loom** (easiest: circular webcam in bottom-left or bottom-right corner, 1080p).
  - **OBS Studio** (display capture + video capture device overlay).
  - **Screen Studio** / **QuickTime + PhotoBooth** (floating always-on-top window).
- **Positioning**: Place your webcam overlay in the **bottom-left corner** (avoids overlapping the header badge, chat messages, and the right-hand artifact pane).

---

## 3. Second-by-Second Demo Script (Target: 2 min 45 sec)

```
0:00 ── 0:25   Scene 1: Introduction & Local Ollama Setup
0:25 ── 0:55   Scene 2: Grounded Q&A with Citation Chips
0:55 ── 1:15   Scene 3: Conversational Follow-up (Query Rewriter)
1:15 ── 1:35   Scene 4: Strict Out-of-Scope Refusal
1:35 ── 2:05   Scene 5: Ship 30 for 30 Essay Skill
2:05 ── 2:35   Scene 6: Side-by-Side Sandboxed Artifact Viewer
2:35 ── 2:50   Scene 7: Architecture Wrap-up & Conclusion
```

---

### Scene 1: Introduction & Local Ollama Setup (0:00 – 0:25)
* **Visual**: Browser on `http://localhost:5173` showing the landing chat page. Cursor points to top header badge.
* **What to say**:
  > *"Hi everyone, I'm [Your Name]. This is the Lenny Growth Assistant — an AI pair programmer and content synthesizer grounded in 303 episodes and 19,434 chunks of Lenny Rachitsky's podcast and newsletter transcripts.*
  >
  > *As required by the brief, notice our active provider badge in the top-right header: we are running 100% locally on Ollama with `qwen2.5:7b-instruct` and `nomic-embed-text` embeddings via PostgreSQL pgvector, with zero cloud dependency."*

---

### Scene 2: Grounded Q&A with Citation Chips (0:25 – 0:55)
* **Visual**: Paste Prompt 1 into the input box and send. Watch the streaming answer and the citation cards appear.
* **Copy-Paste Prompt 1**:
  ```text
  How do I know when it's time to leave my job according to Ada Chen Rekhi?
  ```
* **What to say**:
  > *"Let's ask a core growth career question: 'How do I know when it's time to leave my job according to Ada Chen Rekhi?'*
  >
  > *Notice the fast time-to-first-token under 1 second. The agent executes vector search across pgvector and streams back an answer strictly grounded in Ada's transcript. Below the answer, we have interactive citation chips `[S1]` and `[S2]` showing the exact episode title, guest name, and transcript excerpt. Every single claim is directly verified."*

---

### Scene 3: Conversational Follow-up & Rewriting (0:55 – 1:15)
* **Visual**: In the same chat session, paste Prompt 2.
* **Copy-Paste Prompt 2**:
  ```text
  What did she say about explore versus exploit?
  ```
* **What to say**:
  > *"Now let's test conversational memory with a short follow-up: 'What did she say about explore versus exploit?'*
  >
  > *Notice I didn't repeat Ada's name. Our orchestrator's query rewriter maintains session context, retrieves chunk 22 from the database, and articulates her explore vs exploit framework with matching citations."*

---

### Scene 4: Strict Out-of-Scope Refusal (1:15 – 1:35)
* **Visual**: Paste Prompt 3. Watch the model immediately refuse.
* **Copy-Paste Prompt 3**:
  ```text
  What is the best recipe for baking chocolate chip cookies?
  ```
* **What to say**:
  > *"Next, let's verify hallucination resistance and grounding guarantees. If I ask for a chocolate chip cookie recipe — something completely outside Lenny's podcast — our vector similarity check detects scores below our 0.30 threshold.*
  >
  > *Rather than hallucinating from the model's base training weights, the assistant strictly refuses: 'The podcast transcripts do not cover this topic.' Zero hallucinations."*

---

### Scene 5: Ship 30 for 30 Essay Skill (1:35 – 2:05)
* **Visual**: Click `+ New Chat`. Paste Prompt 4. Watch the structured essay stream.
* **Copy-Paste Prompt 4**:
  ```text
  Write a Ship 30 for 30 atomic essay on the explore vs exploit framework for career decisions based on Ada Chen Rekhi's episode.
  ```
* **What to say**:
  > *"Now let's demonstrate the Ship 30 for 30 skill. This is not a simple one-off prompt, but a dedicated multi-step generation pipeline.*
  >
  > *Notice the output structure: a punchy, provocative hook, short 1- to 3-sentence paragraphs, modular subheadings, bullet points with selective bolding, and concrete takeaways — all grounded in transcript citations and reaching our ~1,250-word target."*

---

### Scene 6: Side-by-Side Sandboxed Artifact Viewer (2:05 – 2:35)
* **Visual**: Paste Prompt 5. Watch the Artifact Viewer open side-by-side to the right. Toggle **Preview** and **Code** tabs. Click open the **Allowed / Blocked** security inspector at the bottom.
* **Copy-Paste Prompt 5**:
  ```text
  Create an HTML career decision matrix artifact based on this advice.
  ```
* **What to say**:
  > *"Finally, let's generate an interactive artifact. The assistant produces an HTML/CSS career matrix.*
  >
  > *Crucially, the Artifact Viewer opens directly beside the chat — no raw code dumped in chat, no external redirects. Because user and model HTML is untrusted, security is paramount:*
  > 1. *It passes through our server-side sanitizer.*
  > 2. *It renders inside a strictly sandboxed iframe with scripts and same-origin disabled.*
  > 3. *And down here in the security drawer, the 'Allowed / Blocked' inspector transparently shows which tags were safely rendered and what was blocked."*

---

### Scene 7: Architecture Wrap-up & Conclusion (2:35 – 2:50)
* **Visual**: Briefly show the sidebar session list (click previous chat to show session persistence) and wrap up.
* **What to say**:
  > *"To wrap up: independent sessions persist in PostgreSQL, 29/29 automated unit tests pass, and one command with `docker compose up` brings up the entire stack.*
  >
  > *All code, eval benchmarks, and transcripts of failed iterations are documented in the GitHub repository. Thank you for watching!"*

---

## 4. Quick Copy-Paste Prompts Sheet

Keep this open on a second monitor or notepad while recording:

```text
Prompt 1 (Grounded Q&A):
How do I know when it's time to leave my job according to Ada Chen Rekhi?

Prompt 2 (Follow-up):
What did she say about explore versus exploit?

Prompt 3 (Refusal):
What is the best recipe for baking chocolate chip cookies?

Prompt 4 (Ship 30 Essay):
Write a Ship 30 for 30 atomic essay on the explore vs exploit framework for career decisions based on Ada Chen Rekhi's episode.

Prompt 5 (Artifact):
Create an HTML career decision matrix artifact based on this advice.
```

---

## 5. Post-Recording Steps (To Complete Submission)

1. **Review Video Quality**:
   - Camera is clearly visible throughout.
   - Total runtime is between **2:15 and 3:00 minutes**.
   - Audio is clean and audible.
2. **Upload to YouTube**:
   - Title: `Lenny Growth Assistant — AI Walkthrough & Architecture Demo`
   - Privacy: **Unlisted** (or Public).
   - Description: Include link to your GitHub repo (`https://github.com/Karuna212006/Lenny_Growth_Assistant`).
3. **Update Repository**:
   - Paste your YouTube link into [`README.md`](file:///c:/lenny_Growth_Assistant/README.md#L225) line 225:
     ```markdown
     - **Video Walkthrough (2–3 mins, camera on):** [https://youtu.be/YOUR_VIDEO_ID](https://youtu.be/YOUR_VIDEO_ID)
     ```
   - Tick Deliverable 8 in [`docs/PLAN.md`](file:///c:/lenny_Growth_Assistant/docs/PLAN.md#L63):
     ```markdown
     - [x] 8. Demo video, 2–3 min, camera on, uploaded to YouTube
     ```
4. **Git Commit & Push**:
   ```bash
   git add README.md docs/PLAN.md docs/DEMO_VIDEO_GUIDE.md
   git commit -m "docs: add demo video guide and update youtube walkthrough link"
   git push origin main
   ```
5. **Submit**: Copy your GitHub repository link and YouTube video link into the final submission form.
