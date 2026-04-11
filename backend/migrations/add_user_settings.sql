-- Add user_settings table for persistent, server-side settings
-- Designed to support multiple users in the future (user_id column)

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1,  -- Default to user 1 (supports multiple users later)
    key VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);

-- Insert default settings for user 1
INSERT INTO user_settings (user_id, key, value) VALUES
    (1, 'default_location', '1'),
    (1, 'default_duration', '90'),
    (1, 'default_section', ''),
    (1, 'api_url', 'http://localhost:8002'),
    (1, 'model', 'local'),
    (1, 'ollama_url', 'http://localhost:11434'),
    (1, 'ollama_model', 'gemma3:12b'),
    (1, 'use_ai_generation', 'false'),
    (1, 'openrouter_api_key', ''),
    (1, 'openrouter_model', 'openrouter/auto')
ON CONFLICT (user_id, key) DO NOTHING;
