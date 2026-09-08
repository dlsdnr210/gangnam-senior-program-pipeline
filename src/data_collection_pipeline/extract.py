"""목록 HTML에서 공지사항 메타데이터 추출."""

import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup, Tag

from .config import settings
from .logging_config import setup_logger

logger = setup_logger(__name__)

RAW_PATTERN = "gangnam_notice_page_*.html"
RAW_RE = re.compile(r"gangnam_notice_page_(\d{3})\.html$")
CATEGORY_RE = re.compile(r"^\[([^\]]+)\]")
NOTICE_ID_RE = re.compile(r"/gnsw_www7/(\d+)/view\.do")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def extract_source_page(path: Path) -> int:
    match = RAW_RE.match(path.name)
    if not match:
        raise ValueError(f"잘못된 raw 파일명: {path.name}")
    return int(match.group(1))


def extract_category(title: str) -> str:
    match = CATEGORY_RE.search(title)
    return match.group(1).strip() if match else ""


def extract_notice_id(url: str) -> str:
    match = NOTICE_ID_RE.search(url)
    return match.group(1) if match else ""


def find_notice_table(soup: BeautifulSoup) -> Tag | None:
    for table in soup.find_all("table"):
        header = clean_text(table.get_text(" ", strip=True))
        if all(
            word in header
            for word in ["번호", "제목", "조회수", "작성일"]
        ):
            return table
    return None


def parse_list_html(raw_file: Path) -> pd.DataFrame:
    page = extract_source_page(raw_file)
    soup = BeautifulSoup(
        raw_file.read_bytes(),
        "html.parser",
    )
    table = find_notice_table(soup)

    if table is None:
        raise ValueError(
            f"공지사항 테이블을 찾지 못했습니다: {raw_file.name}"
        )

    records = []

    for row in table.select("tbody tr"):
        cells = row.find_all("td")
        link = row.find("a", href=True)

        if len(cells) < 4 or link is None:
            continue

        cell_texts = [
            clean_text(td.get_text(" ", strip=True))
            for td in cells
        ]

        title = clean_text(link.get_text(" ", strip=True))
        detail_url = urljoin(
            settings.base_domain,
            link.get("href", ""),
        )

        records.append({
            "source_page": page,
            "notice_no": cell_texts[0],
            "notice_id": extract_notice_id(detail_url),
            "category": extract_category(title),
            "title": title,
            "views": cell_texts[-2],
            "post_date": cell_texts[-1],
            "detail_url": detail_url,
        })

    return pd.DataFrame(records)


def run_extract(raw_batch_dir: Path) -> Path:
    raw_files = sorted(raw_batch_dir.glob(RAW_PATTERN))
    if not raw_files:
        raise FileNotFoundError(
            f"파싱할 목록 HTML이 없습니다: {raw_batch_dir}"
        )

    frames = []
    failed = 0

    for raw_file in raw_files:
        try:
            df = parse_list_html(raw_file)
            frames.append(df)
            logger.info(
                "목록 파싱 성공 | %s | %s건",
                raw_file.name,
                len(df),
            )
        except Exception:
              logger.exception(
              "목록 파싱 실패 | %s",
               raw_file.name,
            )

    if not frames:
        raise RuntimeError("파싱에 성공한 목록 데이터가 없습니다.")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(
        subset=["detail_url"],
        keep="first",
    ).reset_index(drop=True)

    out_dir = settings.interim_dir / raw_batch_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "notice_list.csv"

    merged.to_csv(
        out_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "목록 파싱 종료 | raw=%s개 | unique=%s건 | 실패=%s | %s",
        len(raw_files),
        len(merged),
        failed,
        out_path,
    )

    return out_path
