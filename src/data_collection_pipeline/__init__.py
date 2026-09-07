"""강남노인종합복지관 프로그램 데이터 파이프라인."""

from .pipeline import PipelineResult, run_pipeline

__all__ = [
    "PipelineResult",
    "run_pipeline",
]
