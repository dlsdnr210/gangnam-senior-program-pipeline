CREATE DATABASE IF NOT EXISTS senior_program_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE senior_program_db;

CREATE TABLE IF NOT EXISTS senior_program (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    program_key VARCHAR(128) NOT NULL UNIQUE,
    notice_id VARCHAR(30),
    center_name VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    views INT DEFAULT 0,
    post_date DATE NOT NULL,
    detail_url VARCHAR(1000) NOT NULL,
    recruit_period VARCHAR(500),
    apply_method VARCHAR(500),
    target VARCHAR(500),
    contact VARCHAR(500),
    phone VARCHAR(50),
    program_period VARCHAR(500),
    location VARCHAR(500),
    capacity VARCHAR(500),
    capacity_num INT NULL,
    fee VARCHAR(500),
    body_text LONGTEXT,
    detail_status VARCHAR(30),
    batch_id VARCHAR(30),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_program_post_date (post_date),
    INDEX idx_program_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS crawl_run_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(30) NOT NULL,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    status VARCHAR(30) NOT NULL,
    list_count INT DEFAULT 0,
    detail_count INT DEFAULT 0,
    processed_count INT DEFAULT 0,
    inserted_or_updated_count INT DEFAULT 0,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_history_batch_id (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
