"""공지사항 상세페이지 수집 및 상세 정보 추출."""

from pathlib import Path
import re
import time

import pandas as pd
from bs4 import BeautifulSoup

from .config import settings
from .http_client import build_session, fetch
from .logging_config import setup_logger


logger = setup_logger(__name__)

PROGRAM_KEYWORDS = [
    "평생교육",
    "건강증진",
    "프로그램",
    "강좌",
    "교육",
    "참여자 모집",
    "신규참여자",
    "접수",
    "배움터",
    "아카데미",
    "상담",
    "검진",
]

EXCLUDE_KEYWORDS = [
    "결과발표",
    "합격자",
    "휴강",
    "방학",
    "주차 안내",
    "출결 안내",
    "홈페이지",
]

FIELD_PATTERNS = {
    "recruit_period": [
        r"모집기간\s*[:：]\s*([^\n]+)",
        r"접수기간\s*[:：]\s*([^\n]+)",
    ],
    "apply_method": [
        r"모집방법\s*[:：]\s*([^\n]+)",
        r"접수방법\s*[:：]\s*([^\n]+)",
        r"신청방법\s*[:：]\s*([^\n]+)",
    ],
    "target": [
        r"접수대상\s*[:：]\s*([^\n]+)",
        r"모집대상\s*[:：]\s*([^\n]+)",
        r"대상\s*[:：]\s*([^\n]+)",
    ],
    "contact": [
        r"문의\s*[:：]\s*([^\n]+)",
        r"문의처\s*[:：]\s*([^\n]+)",
    ],
    "program_period": [
        r"강의기간\s*[:：]\s*([^\n]+)",
        r"교육기간\s*[:：]\s*([^\n]+)",
        r"운영기간\s*[:：]\s*([^\n]+)",
        r"프로그램\s*기간\s*[:：]\s*([^\n]+)",
    ],
    "location": [
        r"장소\s*[:：]\s*([^\n]+)",
        r"교육장소\s*[:：]\s*([^\n]+)",
    ],
    "capacity": [
        r"모집인원\s*[:：]\s*([^\n]+)",
        r"정원\s*[:：]\s*([^\n]+)",
        r"접수대상\s*[:：][^\n]*?(\d+\s*명[^\n]*)",
    ],
    "fee": [
        r"수강료\s*[:：]\s*([^\n]+)",
        r"참가비\s*[:：]\s*([^\n]+)",
        r"비용\s*[:：]\s*([^\n]+)",
    ],
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def normalize_body_text(soup: BeautifulSoup) -> str:
    """
    상세 본문 영역을 우선 찾고, 실패하면 페이지 전체 텍스트에서
    제목/메뉴 노이즈를 감수하고 추출한다.
    """
    selectors = [
        ".board_view",
        ".view_cont",
        ".board-view",
        ".bbs_view",
        ".contents",
        "article",
    ]

    node = None
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            break

    if node is None:
        node = soup.body or soup

    text = node.get_text("\n", strip=True)
    lines = [
        " ".join(line.split())
        for line in text.splitlines()
        if line.strip()
    ]
    return "\n".join(lines)


def parse_field(body_text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(
            pattern,
            body_text,
            flags=re.IGNORECASE,
        )
        if match:
            return clean_text(match.group(1))
    return ""


def parse_phone(text: str) -> str:
    match = re.search(
        r"(0\d{1,2}-\d{3,4}-\d{4})",
        text,
    )
    return match.group(1) if match else ""


def is_program_candidate(title: str, category: str) -> bool:
    text = f"{category} {title}"

    included = any(
        keyword in text
        for keyword in PROGRAM_KEYWORDS
    )
    excluded = any(
        keyword in text
        for keyword in EXCLUDE_KEYWORDS
    )

    return included and not excluded


def parse_detail_html(content: bytes) -> dict:
    soup = BeautifulSoup(content, "html.parser")
    body_text = normalize_body_text(soup)

    result = {
        key: parse_field(body_text, patterns)
        for key, patterns in FIELD_PATTERNS.items()
    }
    result["phone"] = parse_phone(
        result.get("contact", "") or body_text
    )
    result["body_text"] = body_text

    return result


def save_detail_html(
    content: bytes,
    detail_batch_dir: Path,
    notice_id: str,
) -> Path:
    safe_id = notice_id or "unknown"
    path = detail_batch_dir / f"notice_{safe_id}.html"
    path.write_bytes(content)
    return path


def run_detail_collection(
    list_csv_path: Path,
    incremental_urls: set[str] | None = None,
) -> Path:
    df = pd.read_csv(
        list_csv_path,
        dtype=str,
        encoding="utf-8-sig",
    ).fillna("")

    candidates = df[
        df.apply(
            lambda row: is_program_candidate(
                row["title"],
                row["category"],
            ),
            axis=1,
        )
    ].copy()

    if incremental_urls:
        before = len(candidates)
        candidates = candidates[
            ~candidates["detail_url"].isin(incremental_urls)
        ].copy()
        logger.info(
            "증분 필터 적용 | 후보=%s | 신규=%s",
            before,
            len(candidates),
        )

    batch_id = list_csv_path.parent.name
    raw_dir = (
        settings.raw_detail_dir
        / batch_id
    )
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = build_session()
    detail_rows = []
    failed_rows = []

    for _, row in candidates.iterrows():
        url = row["detail_url"]
        notice_id = row.get("notice_id", "")

        try:
            response = fetch(session, url)
            save_detail_html(
                response.content,
                raw_dir,
                notice_id,
            )

            detail = parse_detail_html(
                response.content
            )
            detail_rows.append({
                **row.to_dict(),
                **detail,
                "detail_status": "success",
            })

            logger.info(
                "상세 수집 성공 | id=%s | %s",
                notice_id,
                row["title"][:50],
            )

        except Exception as exc:
            failed_rows.append({
                **row.to_dict(),
                "detail_status": "failed",
                "error_message": str(exc),
            })
            logger.exception(
                "상세 수집 실패 | id=%s | url=%s",
                notice_id,
                url,
            )

        time.sleep(settings.request_interval)

    out_dir = settings.interim_dir / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)

    detail_path = out_dir / "notice_detail.csv"
    pd.DataFrame(detail_rows).to_csv(
        detail_path,
        index=False,
        encoding="utf-8-sig",
    )

    if failed_rows:
        failed_path = out_dir / "failed_detail.csv"
        pd.DataFrame(failed_rows).to_csv(
            failed_path,
            index=False,
            encoding="utf-8-sig",
        )

    logger.info(
        "상세 수집 종료 | 성공=%s | 실패=%s",
        len(detail_rows),
        len(failed_rows),
    )

    return detail_path
