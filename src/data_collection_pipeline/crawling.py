"""강남노인종합복지관 공지사항 목록 HTML 수집."""

from datetime import datetime
from pathlib import Path
import time

from .config import settings
from .http_client import build_session, fetch
from .logging_config import setup_logger


logger = setup_logger(__name__)


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_batch_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_page_url(page: int) -> str:
    return f"{settings.list_url}?mid={settings.mid}&page={page}"


def save_list_html(
    content: bytes,
    batch_dir: Path,
    page: int,
) -> Path:
    path = batch_dir / f"gangnam_notice_page_{page:03d}.html"
    path.write_bytes(content)
    return path


def run_crawling(
    start_page: int | None = None,
    end_page: int | None = None,
    batch_id: str | None = None,
) -> Path:
    start_page = start_page or settings.start_page
    end_page = end_page or settings.end_page
    batch_id = batch_id or create_batch_id()

    if start_page < 1:
        raise ValueError("start_page는 1 이상이어야 합니다.")
    if end_page < start_page:
        raise ValueError("end_page는 start_page 이상이어야 합니다.")

    batch_dir = ensure_directory(
        settings.raw_list_dir / batch_id
    )

    session = build_session()
    succeeded = 0
    failed = 0

    logger.info(
        "목록 수집 시작 | page=%s~%s | batch=%s",
        start_page,
        end_page,
        batch_id,
    )

    for page in range(start_page, end_page + 1):
        url = build_page_url(page)

        try:
            response = fetch(session, url)
            saved = save_list_html(
                response.content,
                batch_dir,
                page,
            )
            succeeded += 1
            logger.info(
                "목록 수집 성공 | page=%s | status=%s | bytes=%s | %s",
                page,
                response.status_code,
                len(response.content),
                saved.name,
            )
        except Exception as exc:
            failed += 1
            logger.exception(
                "목록 수집 실패 | page=%s | url=%s | error=%s",
                page,
                url,
                exc,
            )

        if page < end_page:
            time.sleep(settings.request_interval)

    logger.info(
        "목록 수집 종료 | 성공=%s | 실패=%s | batch=%s",
        succeeded,
        failed,
        batch_id,
    )

    if succeeded == 0:
        raise RuntimeError("수집에 성공한 목록 페이지가 없습니다.")

    return batch_dir
