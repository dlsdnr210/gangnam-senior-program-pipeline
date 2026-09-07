"""전체 실무형 데이터 파이프라인 오케스트레이션."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from .crawling import create_batch_id, run_crawling
from .detail import run_detail_collection
from .extract import run_extract
from .load import load_processed_csv, insert_run_history
from .logging_config import setup_logger
from .preprocess import run_preprocess
from .state import load_seen_urls, save_seen_urls


logger = setup_logger(__name__)


@dataclass
class PipelineResult:
    batch_id: str
    list_count: int
    detail_count: int
    processed_count: int
    loaded_count: int
    processed_csv: Path


def _count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    return len(
        pd.read_csv(
            path,
            encoding="utf-8-sig",
        )
    )


def run_pipeline(
    *,
    incremental: bool = True,
    start_page: int | None = None,
    end_page: int | None = None,
) -> PipelineResult:
    started_at = datetime.now()
    batch_id = create_batch_id()

    list_count = 0
    detail_count = 0
    processed_count = 0
    loaded_count = 0

    logger.info(
        "파이프라인 시작 | batch=%s | incremental=%s",
        batch_id,
        incremental,
    )

    try:
        raw_list_dir = run_crawling(
            start_page=start_page,
            end_page=end_page,
            batch_id=batch_id,
        )

        list_csv = run_extract(
            raw_list_dir
        )
        list_count = _count_csv(list_csv)

        seen_urls = (
            load_seen_urls()
            if incremental
            else set()
        )

        detail_csv = run_detail_collection(
            list_csv,
            incremental_urls=seen_urls,
        )
        detail_count = _count_csv(detail_csv)

        if detail_count == 0:
            logger.info(
                "신규 상세 데이터가 없어 파이프라인을 종료합니다."
            )
            # 신규 없음도 정상 완료로 간주.
            empty_path = detail_csv
            insert_run_history(
                batch_id=batch_id,
                started_at=started_at,
                finished_at=datetime.now(),
                status="SUCCESS_NO_NEW_DATA",
                list_count=list_count,
                detail_count=0,
                processed_count=0,
                loaded_count=0,
            )
            return PipelineResult(
                batch_id=batch_id,
                list_count=list_count,
                detail_count=0,
                processed_count=0,
                loaded_count=0,
                processed_csv=empty_path,
            )

        processed_csv = run_preprocess(
            detail_csv
        )
        processed_count = _count_csv(
            processed_csv
        )

        loaded_count = load_processed_csv(
            processed_csv
        )

        processed_df = pd.read_csv(
            processed_csv,
            encoding="utf-8-sig",
        )
        current_urls = set(
            processed_df["detail_url"]
            .dropna()
            .astype(str)
            .tolist()
        )
        save_seen_urls(
            seen_urls | current_urls
        )

        insert_run_history(
            batch_id=batch_id,
            started_at=started_at,
            finished_at=datetime.now(),
            status="SUCCESS",
            list_count=list_count,
            detail_count=detail_count,
            processed_count=processed_count,
            loaded_count=loaded_count,
        )

        result = PipelineResult(
            batch_id=batch_id,
            list_count=list_count,
            detail_count=detail_count,
            processed_count=processed_count,
            loaded_count=loaded_count,
            processed_csv=processed_csv,
        )

        logger.info(
            "파이프라인 완료 | list=%s | detail=%s | "
            "processed=%s | loaded=%s",
            list_count,
            detail_count,
            processed_count,
            loaded_count,
        )
        return result

    except Exception as exc:
        logger.exception(
            "파이프라인 실패 | batch=%s | %s",
            batch_id,
            exc,
        )
        try:
            insert_run_history(
                batch_id=batch_id,
                started_at=started_at,
                finished_at=datetime.now(),
                status="FAILED",
                list_count=list_count,
                detail_count=detail_count,
                processed_count=processed_count,
                loaded_count=loaded_count,
                error_message=str(exc),
            )
        finally:
            raise
