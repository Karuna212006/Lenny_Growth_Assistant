-- =============================================================
-- Lenny Growth Assistant — PostgreSQL Schema (LOCKED 2026-10-09)
-- =============================================================
-- Run once on a fresh DB, or via the init SQL mount in docker-compose.
-- Requires PostgreSQL 15+ with pgvector and pgcrypto extensions.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for gen_random_uuid()

-- -------------------------------------------------------------
-- users
-- One row per anonymous browser session. anon_key is a UUID the
-- frontend generates and stores in localStorage.
-- -------------------------------------------------------------
CREATE TABLE users (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  anon_key    TEXT        NOT NULL UNIQUE,        -- browser-generated UUID
  metadata    JSONB       NOT NULL DEFAULT '{}',  -- e.g. user agent, locale
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- sessions
-- One row per chat. Independent context: never share across sessions.
-- updated_at is bumped by trigger trg_messages_touch_session.
-- -------------------------------------------------------------
CREATE TABLE sessions (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT        NOT NULL DEFAULT 'New chat',
  provider    TEXT        NOT NULL,               -- ollama | openai_compatible
  model       TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sessions_user ON sessions (user_id, updated_at DESC);

-- Auto-bump sessions.updated_at whenever a message is inserted.
CREATE OR REPLACE FUNCTION touch_session()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  UPDATE sessions SET updated_at = now() WHERE id = NEW.session_id;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_messages_touch_session
AFTER INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION touch_session();

-- -------------------------------------------------------------
-- messages
-- Full chat history. citations is an array of source references:
-- [{episode_id, title, guest, chunk_id, score}]
-- latency_ms is wall-clock time from request to last token.
-- -------------------------------------------------------------
CREATE TABLE messages (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content     TEXT        NOT NULL,
  citations   JSONB       NOT NULL DEFAULT '[]',
  provider    TEXT,
  model       TEXT,
  latency_ms  INTEGER,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_messages_session ON messages (session_id, created_at);

-- -------------------------------------------------------------
-- artifacts
-- Generated Markdown or HTML/CSS blobs.
-- content stored raw; sanitized at render time (DOMPurify + sandbox).
-- Storing raw lets us re-sanitize if rules improve later.
-- message_id SET NULL (not CASCADE) so artifacts survive message edits.
-- -------------------------------------------------------------
CREATE TABLE artifacts (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  message_id  UUID        REFERENCES messages(id) ON DELETE SET NULL,
  type        TEXT        NOT NULL CHECK (type IN ('markdown', 'html')),
  title       TEXT        NOT NULL,
  content     TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_artifacts_session ON artifacts (session_id, created_at);

-- -------------------------------------------------------------
-- episodes
-- One row per Lenny transcript file/URL.
-- content_hash is the refresh key: re-embed only on hash change.
-- Re-ingesting = DELETE chunks WHERE episode_id + re-insert.
-- -------------------------------------------------------------
CREATE TABLE episodes (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  title        TEXT        NOT NULL,
  guest        TEXT,
  source_path  TEXT        NOT NULL UNIQUE,       -- file path or URL in the repo
  content_hash TEXT        NOT NULL,
  ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- chunks
-- Speaker-turn chunks (~300-500 tokens, small overlap).
-- embedding: 768 dims (nomic-embed-text via Ollama).
-- Retrieval uses cosine distance (<=>); HNSW index matches this.
-- start_time is TEXT (nullable) because not all transcripts have timestamps.
-- UNIQUE (episode_id, chunk_index) prevents duplicate chunks on re-ingest.
-- -------------------------------------------------------------
CREATE TABLE chunks (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_id   UUID        NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  chunk_index  INTEGER     NOT NULL,
  text         TEXT        NOT NULL,
  speaker      TEXT,
  start_time   TEXT,                              -- e.g. "00:12:34", nullable
  embedding    vector(768) NOT NULL,
  UNIQUE (episode_id, chunk_index)
);

-- HNSW index for fast approximate nearest-neighbour search (cosine).
CREATE INDEX ix_chunks_embedding ON chunks
  USING hnsw (embedding vector_cosine_ops);

-- B-tree index for DELETE FROM chunks WHERE episode_id = $1 on re-ingest.
CREATE INDEX ix_chunks_episode ON chunks (episode_id);

-- =============================================================
-- Design notes
-- =============================================================
-- 1. UUID PKs: safe to expose in URLs; reveal no row counts.
-- 2. ON DELETE CASCADE: deleting a session removes messages + artifacts.
--    Deleting an episode removes all its chunks (clean re-ingest path).
--    No DELETE /sessions/{id} endpoint is built (not in the brief).
-- 3. sessions.updated_at: bumped by trigger, not application code.
-- 4. Artifact sanitization at render, not at storage: allows rule improvements
--    without a DB migration; viewer can show the "Blocked" panel.
-- 5. Conversation summary column: NOT added. History trimming handled by
--    query rewriting in the agent layer. Add later with ALTER TABLE if needed.
-- 6. Hybrid search / re-ranking: out of scope (first cut per plan).
