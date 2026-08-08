-- Tide Database Initialization Schema
-- Target: Postgres 16 with pgvector extension (Supabase compatible)

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. posts table
CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL, -- github, arxiv, hn, stackoverflow, newsapi
    source_id TEXT NOT NULL, -- canonical ID from the source API
    title TEXT NOT NULL,
    body TEXT,
    url TEXT,
    canonical_url TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    engagement JSONB DEFAULT '{}'::jsonb,
    native_tags TEXT[] DEFAULT '{}'::text[],
    embedding vector(768),
    CONSTRAINT unique_source_source_id UNIQUE (source, source_id)
);

-- Indexes for posts
CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_source ON posts (source);
-- HNSW Index for cosine similarity search (using nomic text embeddings)
CREATE INDEX IF NOT EXISTS idx_posts_embedding_hnsw ON posts USING hnsw (embedding vector_cosine_ops);

-- 2. concepts table
CREATE TABLE IF NOT EXISTS concepts (
    id BIGSERIAL PRIMARY KEY,
    canonical_label TEXT NOT NULL UNIQUE,
    aliases TEXT[] DEFAULT '{}'::text[],
    embedding vector(768) NOT NULL,
    status TEXT NOT NULL DEFAULT 'active', -- active, merged, dormant, deprecated
    merged_into BIGINT REFERENCES concepts(id) ON DELETE SET NULL,
    succeeds BIGINT[] DEFAULT '{}'::bigint[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_evidence_at TIMESTAMPTZ,
    community_id INT,
    community_version INT DEFAULT 0,
    post_count INT DEFAULT 0
);

-- Indexes for concepts
CREATE INDEX IF NOT EXISTS idx_concepts_status ON concepts (status);
CREATE INDEX IF NOT EXISTS idx_concepts_aliases ON concepts USING GIN (aliases);
CREATE INDEX IF NOT EXISTS idx_concepts_embedding_hnsw ON concepts USING hnsw (embedding vector_cosine_ops);

-- 3. post_concepts table
CREATE TABLE IF NOT EXISTS post_concepts (
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    concept_id BIGINT REFERENCES concepts(id) ON DELETE CASCADE,
    similarity REAL NOT NULL,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    link_source TEXT NOT NULL, -- embedding, phrase, native_tag
    PRIMARY KEY (post_id, concept_id)
);

-- Indexes for post_concepts
CREATE INDEX IF NOT EXISTS idx_post_concepts_concept_id ON post_concepts (concept_id);
CREATE INDEX IF NOT EXISTS idx_post_concepts_linked_at ON post_concepts (linked_at DESC);

-- 4. concept_edges table
CREATE TABLE IF NOT EXISTS concept_edges (
    concept_a BIGINT REFERENCES concepts(id) ON DELETE CASCADE,
    concept_b BIGINT REFERENCES concepts(id) ON DELETE CASCADE,
    co_count INT DEFAULT 0,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    pmi REAL DEFAULT 0.0,
    cross_community BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (concept_a, concept_b),
    CONSTRAINT chk_concept_order CHECK (concept_a < concept_b)
);

-- Index for concept_edges query speed
CREATE INDEX IF NOT EXISTS idx_concept_edges_concept_b ON concept_edges (concept_b);
CREATE INDEX IF NOT EXISTS idx_concept_edges_co_count ON concept_edges (co_count DESC);

-- 5. phrase_observations table
CREATE TABLE IF NOT EXISTS phrase_observations (
    id BIGSERIAL PRIMARY KEY,
    phrase TEXT NOT NULL,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    source TEXT NOT NULL, -- denormalized for speed
    observed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for phrase_observations
CREATE INDEX IF NOT EXISTS idx_phrase_obs_phrase ON phrase_observations (phrase);
CREATE INDEX IF NOT EXISTS idx_phrase_obs_observed_at ON phrase_observations (observed_at DESC);

-- 6. phrase_stats_daily table
CREATE TABLE IF NOT EXISTS phrase_stats_daily (
    phrase TEXT NOT NULL,
    day DATE NOT NULL,
    post_count INT DEFAULT 0,
    source_count INT DEFAULT 0,
    co_concept_ids BIGINT[] DEFAULT '{}'::bigint[],
    status TEXT NOT NULL DEFAULT 'watching', -- watching, graduated, noise
    PRIMARY KEY (phrase, day)
);

-- Index for phrase graduation
CREATE INDEX IF NOT EXISTS idx_phrase_stats_daily_day ON phrase_stats_daily (day DESC);
CREATE INDEX IF NOT EXISTS idx_phrase_stats_daily_status ON phrase_stats_daily (status);

-- 7. concept_evidence_daily table
CREATE TABLE IF NOT EXISTS concept_evidence_daily (
    concept_id BIGINT REFERENCES concepts(id) ON DELETE CASCADE,
    day DATE NOT NULL,
    post_count INT DEFAULT 0,
    source_breakdown JSONB DEFAULT '{}'::jsonb,
    avg_engagement REAL DEFAULT 0.0,
    PRIMARY KEY (concept_id, day)
);

-- 8. concept_edges_daily table
CREATE TABLE IF NOT EXISTS concept_edges_daily (
    concept_a BIGINT REFERENCES concepts(id) ON DELETE CASCADE,
    concept_b BIGINT REFERENCES concepts(id) ON DELETE CASCADE,
    day DATE NOT NULL,
    new_co_count INT DEFAULT 0,
    PRIMARY KEY (concept_a, concept_b, day),
    CONSTRAINT chk_concept_order_daily CHECK (concept_a < concept_b)
);

-- 9. pending_pool table
CREATE TABLE IF NOT EXISTS pending_pool (
    post_id BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    nearest_sim REAL,
    distinctive_tokens TEXT[] DEFAULT '{}'::text[]
);

-- Index for pending pool retrieval
CREATE INDEX IF NOT EXISTS idx_pending_pool_added_at ON pending_pool (added_at);
