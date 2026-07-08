CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(120) NOT NULL UNIQUE,
    api_key VARCHAR(128) NOT NULL UNIQUE,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    created_at DATETIME NOT NULL,
    INDEX ix_users_username (username),
    INDEX ix_users_api_key (api_key)
);

CREATE TABLE rate_limit_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    endpoint VARCHAR(255) NULL,
    algorithm VARCHAR(50) NOT NULL,
    max_requests INT NOT NULL,
    time_window INT NOT NULL,
    refill_rate FLOAT NOT NULL DEFAULT 0,
    bucket_capacity INT NOT NULL,
    CONSTRAINT fk_rate_limit_rules_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_rate_limit_rules_user_endpoint UNIQUE (user_id, endpoint),
    CONSTRAINT ck_rate_limit_max_requests_positive CHECK (max_requests > 0),
    CONSTRAINT ck_rate_limit_time_window_positive CHECK (time_window > 0),
    CONSTRAINT ck_rate_limit_bucket_capacity_positive CHECK (bucket_capacity > 0),
    CONSTRAINT ck_rate_limit_refill_rate_non_negative CHECK (refill_rate >= 0),
    INDEX ix_rate_limit_rules_user_id (user_id),
    INDEX ix_rate_limit_rules_endpoint (endpoint)
);

CREATE TABLE request_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    endpoint VARCHAR(255) NOT NULL,
    timestamp DATETIME NOT NULL,
    allowed BOOLEAN NOT NULL,
    algorithm VARCHAR(50) NOT NULL DEFAULT 'unknown',
    response_time_ms FLOAT NOT NULL DEFAULT 0,
    CONSTRAINT fk_request_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX ix_request_logs_user_id (user_id),
    INDEX ix_request_logs_endpoint (endpoint),
    INDEX ix_request_logs_timestamp (timestamp)
);

CREATE TABLE algorithm_states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    algorithm VARCHAR(50) NOT NULL,
    window_start DATETIME NULL,
    request_count INT NOT NULL DEFAULT 0,
    tokens FLOAT NULL,
    water_level FLOAT NULL,
    last_updated DATETIME NOT NULL,
    CONSTRAINT fk_algorithm_states_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_algorithm_state_scope UNIQUE (user_id, endpoint, algorithm),
    INDEX ix_algorithm_states_user_id (user_id),
    INDEX ix_algorithm_states_endpoint (endpoint),
    INDEX ix_algorithm_states_algorithm (algorithm)
);
