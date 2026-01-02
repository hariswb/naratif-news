-- Media Monitoring Pipeline Database Schema

-- Articles table: stores canonical articles
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR(512) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    source VARCHAR(100) NOT NULL,
    published_at TIMESTAMP,
    content_hash VARCHAR(32) UNIQUE NOT NULL,
    is_indonesian BOOLEAN DEFAULT TRUE,
    
    -- Sentiment signals
    sentiment_polarity NUMERIC(5,3),
    sentiment_subjectivity NUMERIC(5,3),
    sentiment_label VARCHAR(20),
    
    -- Metadata
    run_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_run_id ON articles(run_id);
CREATE INDEX IF NOT EXISTS idx_articles_sentiment_label ON articles(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);

-- Pipeline runs table: tracks pipeline executions
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) UNIQUE NOT NULL,
    run_date DATE NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    
    -- Stage completion tracking
    collect_completed BOOLEAN DEFAULT FALSE,
    parse_completed BOOLEAN DEFAULT FALSE,
    clean_completed BOOLEAN DEFAULT FALSE,
    signal_completed BOOLEAN DEFAULT FALSE,
    
    -- Statistics
    total_sources INTEGER,
    total_fetched INTEGER,
    total_parsed INTEGER,
    total_cleaned INTEGER,
    total_analyzed INTEGER,
    
    -- Error tracking
    errors TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Run statistics table: detailed stats per run
CREATE TABLE IF NOT EXISTS run_statistics (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL REFERENCES pipeline_runs(run_id),
    stage VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Source statistics table: per-source metrics
CREATE TABLE IF NOT EXISTS source_statistics (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL REFERENCES pipeline_runs(run_id),
    source VARCHAR(100) NOT NULL,
    articles_fetched INTEGER,
    articles_cleaned INTEGER,
    avg_sentiment_polarity NUMERIC(5,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily aggregates view
CREATE OR REPLACE VIEW daily_article_stats AS
SELECT 
    DATE(published_at) as date,
    source,
    sentiment_label,
    COUNT(*) as article_count,
    AVG(sentiment_polarity) as avg_polarity,
    AVG(sentiment_subjectivity) as avg_subjectivity
FROM articles
WHERE published_at IS NOT NULL
GROUP BY DATE(published_at), source, sentiment_label
ORDER BY date DESC, source;

-- Sentiment distribution view
CREATE OR REPLACE VIEW sentiment_distribution AS
SELECT 
    run_id,
    source,
    sentiment_label,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY run_id, source), 2) as percentage
FROM articles
GROUP BY run_id, source, sentiment_label
ORDER BY run_id DESC, source, sentiment_label;