"""전처리 결과 데이터 품질 검증."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class ValidationResult:
    is_valid: bool
    total_rows: int
    duplicate_urls: int
    empty_titles: int
    invalid_dates: int
    missing_detail_urls: int
    detail_success_rate: float


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    required = [
        "center_name",
        "region",
        "title",
        "post_date",
        "detail_url",
    ]

    missing_columns = [
        col for col in required
        if col not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"필수 컬럼 누락: {missing_columns}"
        )

    total = len(df)
    duplicate_urls = int(
        df["detail_url"].duplicated().sum()
    )
    empty_titles = int(
        df["title"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )
    invalid_dates = int(
        pd.to_datetime(
            df["post_date"],
            errors="coerce",
        )
        .isna()
        .sum()
    )
    missing_detail_urls = int(
        df["detail_url"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    if "detail_status" in df.columns and total:
        success_count = int(
            df["detail_status"]
            .fillna("")
            .eq("success")
            .sum()
        )
        detail_success_rate = success_count / total
    else:
        detail_success_rate = 0.0

    is_valid = (
        duplicate_urls == 0
        and empty_titles == 0
        and missing_detail_urls == 0
        and invalid_dates == 0
    )

    return ValidationResult(
        is_valid=is_valid,
        total_rows=total,
        duplicate_urls=duplicate_urls,
        empty_titles=empty_titles,
        invalid_dates=invalid_dates,
        missing_detail_urls=missing_detail_urls,
        detail_success_rate=detail_success_rate,
    )
