"""상세 수집 결과 전처리, 중복 제거, 품질 검증."""

from pathlib import Path
import hashlib
import re

import pandas as pd

from .config import settings
from .logging_config import setup_logger
from .validation import validate_dataframe


logger = setup_logger(__name__)


def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for column in result.columns:
        if result[column].dtype == "object":
            result[column] = (
                result[column]
                .fillna("")
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

    return result


def normalize_views(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["views"] = (
        result["views"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"(\d+)", expand=False)
    )
    result["views"] = (
        pd.to_numeric(
            result["views"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )
    return result


def normalize_post_date(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["post_date"] = pd.to_datetime(
        result["post_date"],
        errors="coerce",
    )
    return result


def extract_capacity_number(text: str) -> int | None:
    if not text:
        return None

    match = re.search(r"(\d+)\s*명", str(text))
    return int(match.group(1)) if match else None


def create_program_key(row: pd.Series) -> str:
    """
    notice_id가 가장 안정적인 원본 식별자.
    없을 경우 기관명 + 제목 + 게시일 해시로 대체한다.
    """
    notice_id = str(row.get("notice_id", "")).strip()
    if notice_id:
        return f"gangnam:{notice_id}"

    raw = "|".join([
        str(row.get("center_name", "")),
        str(row.get("title", "")),
        str(row.get("post_date", "")),
    ])
    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def run_preprocess(detail_csv_path: Path) -> Path:
    if not detail_csv_path.exists():
        raise FileNotFoundError(
            f"상세 CSV가 없습니다: {detail_csv_path}"
        )

    df = pd.read_csv(
        detail_csv_path,
        dtype=str,
        encoding="utf-8-sig",
    ).fillna("")

    if df.empty:
        raise ValueError(
            "상세 수집 결과가 비어 있습니다."
        )

    df = clean_string_columns(df)
    df = normalize_views(df)
    df = normalize_post_date(df)

    df.insert(0, "center_name", settings.center_name)
    df.insert(1, "region", settings.region)

    df["capacity_num"] = (
        df.get("capacity", "")
        .astype(str)
        .apply(extract_capacity_number)
    )

    df["program_key"] = df.apply(
        create_program_key,
        axis=1,
    )

    before = len(df)
    df = (
        df.drop_duplicates(
            subset=["program_key"],
            keep="first",
        )
        .reset_index(drop=True)
    )
    duplicates_removed = before - len(df)

    validation = validate_dataframe(df)

    logger.info(
        "품질검증 | rows=%s | duplicate=%s | empty_title=%s | "
        "invalid_date=%s | detail_success_rate=%.1f%%",
        validation.total_rows,
        validation.duplicate_urls,
        validation.empty_titles,
        validation.invalid_dates,
        validation.detail_success_rate * 100,
    )

    if not validation.is_valid:
        raise ValueError(
            "데이터 품질 검증 실패: "
            f"{validation}"
        )

    batch_id = detail_csv_path.parent.name
    settings.processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    out_path = (
        settings.processed_dir
        / f"senior_programs_{batch_id}.csv"
    )

    # CSV에서 날짜를 읽기 쉽게 YYYY-MM-DD로 저장.
    save_df = df.copy()
    save_df["post_date"] = (
        save_df["post_date"]
        .dt.strftime("%Y-%m-%d")
    )
    save_df.to_csv(
        out_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "전처리 완료 | 입력=%s | 중복제거=%s | 최종=%s | %s",
        before,
        duplicates_removed,
        len(df),
        out_path,
    )

    return out_path
