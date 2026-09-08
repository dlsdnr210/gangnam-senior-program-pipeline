"""프로젝트 루트에서 전체 파이프라인을 실행한다."""

from src.data_collection_pipeline import run_pipeline

if __name__ == "__main__":
    result = run_pipeline(
        incremental=True,
    )

    print()
    print("=" * 70)
    print("강남노인종합복지관 데이터 파이프라인 결과")
    print("=" * 70)
    print(f"배치 ID       : {result.batch_id}")
    print(f"목록 데이터    : {result.list_count}건")
    print(f"상세 수집      : {result.detail_count}건")
    print(f"전처리 완료    : {result.processed_count}건")
    print(f"DB 적재       : {result.loaded_count}건")
    print(f"결과 파일      : {result.processed_csv}")
