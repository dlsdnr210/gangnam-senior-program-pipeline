"""전처리 CSV를 MySQL에 UPSERT하고 실행 이력을 저장한다."""

from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import settings
from .logging_config import setup_logger

logger = setup_logger(__name__)


def get_engine() -> Engine:
    password = quote_plus(settings.db_password)
    url = (
        f"mysql+pymysql://{settings.db_user}:{password}"
        f"@{settings.db_host}:{settings.db_port}"
        f"/{settings.db_name}?charset=utf8mb4"
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        future=True,
    )


def ensure_tables(engine: Engine) -> None:
    program_sql = """
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
    """

    history_sql = """
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
    """

    with engine.begin() as conn:
        conn.execute(text(program_sql))
        conn.execute(text(history_sql))


UPSERT_SQL = """
INSERT INTO senior_program (
    program_key,
    notice_id,
    center_name,
    region,
    category,
    title,
    views,
    post_date,
    detail_url,
    recruit_period,
    apply_method,
    target,
    contact,
    phone,
    program_period,
    location,
    capacity,
    capacity_num,
    fee,
    body_text,
    detail_status,
    batch_id
)
VALUES (
    :program_key,
    :notice_id,
    :center_name,
    :region,
    :category,
    :title,
    :views,
    :post_date,
    :detail_url,
    :recruit_period,
    :apply_method,
    :target,
    :contact,
    :phone,
    :program_period,
    :location,
    :capacity,
    :capacity_num,
    :fee,
    :body_text,
    :detail_status,
    :batch_id
)
ON DUPLICATE KEY UPDATE
    category = VALUES(category),
    title = VALUES(title),
    views = VALUES(views),
    post_date = VALUES(post_date),
    detail_url = VALUES(detail_url),
    recruit_period = VALUES(recruit_period),
    apply_method = VALUES(apply_method),
    target = VALUES(target),
    contact = VALUES(contact),
    phone = VALUES(phone),
    program_period = VALUES(program_period),
    location = VALUES(location),
    capacity = VALUES(capacity),
    capacity_num = VALUES(capacity_num),
    fee = VALUES(fee),
    body_text = VALUES(body_text),
    detail_status = VALUES(detail_status),
    batch_id = VALUES(batch_id),
    updated_at = CURRENT_TIMESTAMP;
"""


def load_processed_csv(processed_csv: Path) -> int:
    if not settings.db_enabled:
        logger.info(
            "DB_ENABLED=false 이므로 MySQL 적재를 건너뜁니다."
        )
        return 0

    df = pd.read_csv(
        processed_csv,
        encoding="utf-8-sig",
    )

    if df.empty:
        return 0

    engine = get_engine()
    ensure_tables(engine)

    records = df.where(
        pd.notna(df),
        None,
    ).to_dict(orient="records")

    with engine.begin() as conn:
        for record in records:
            conn.execute(
                text(UPSERT_SQL),
                record,
            )

    logger.info(
        "MySQL UPSERT 완료 | %s건",
        len(records),
    )

    return len(records)


def insert_run_history(
    *,
    batch_id: str,
    started_at: datetime,
    finished_at: datetime | None,
    status: str,
    list_count: int = 0,
    detail_count: int = 0,
    processed_count: int = 0,
    loaded_count: int = 0,
    error_message: str | None = None,
) -> None:
    if not settings.db_enabled:
        return

    engine = get_engine()
    ensure_tables(engine)

    sql = """
    INSERT INTO crawl_run_history (
        batch_id,
        started_at,
        finished_at,
        status,
        list_count,
        detail_count,
        processed_count,
        inserted_or_updated_count,
        error_message
    ) VALUES (
        :batch_id,
        :started_at,
        :finished_at,
        :status,
        :list_count,
        :detail_count,
        :processed_count,
        :loaded_count,
        :error_message
    );
    """

    with engine.begin() as conn:
        conn.execute(
            text(sql),
            {
                "batch_id": batch_id,
                "started_at": started_at,
                "finished_at": finished_at,
                "status": status,
                "list_count": list_count,
                "detail_count": detail_count,
                "processed_count": processed_count,
                "loaded_count": loaded_count,
                "error_message": error_message,
            },
        )
