# 강남노인종합복지관 실무형 데이터 수집 파이프라인

강남노인종합복지관 공지사항에서 시니어 프로그램 관련 데이터를 수집하고,
상세정보 파싱 → 데이터 품질 검증 → 증분 처리 → MySQL UPSERT까지 수행하는 프로젝트입니다.

## 1. 실무형으로 보강한 부분

- 15페이지 기본 수집(100건 이상 확보를 목표)
- `requests.Session` 기반 재시도
- HTTP timeout
- 요청 간격 적용
- 콘솔 + 파일 로그
- 페이지 단위 실패 격리
- 상세페이지 개별 실패 격리
- 원본 HTML 보관
- 프로그램성 게시글 필터링
- 상세페이지 필드 추출
- 중복 제거
- 데이터 품질 검증
- 증분 수집(state)
- MySQL UPSERT
- 크롤링 실행 이력
- `.env` 환경변수 관리
- `.gitignore`
- Notebook 학습/검증용 + Python 운영 코드 분리

## 2. 전체 흐름

```text
강남노인종합복지관
        │
        ▼
[목록 크롤링]
 requests + retry + timeout
        │
        ▼
data/raw/list/<batch>/*.html
        │
        ▼
[목록 파싱]
 title / category / date / url
        │
        ▼
data/interim/<batch>/notice_list.csv
        │
        ▼
[프로그램 후보 선별]
        │
        ▼
[상세페이지 수집]
 모집기간 / 접수방법 / 대상 / 문의 /
 운영기간 / 장소 / 인원 / 비용 / 본문
        │
        ▼
data/raw/detail/<batch>/*.html
        │
        ▼
[전처리 + 검증]
 중복 / 누락 / 날짜 / 조회수 / program_key
        │
        ▼
data/processed/senior_programs_<batch>.csv
        │
        ├──────────────► state/crawl_state.json
        │                  증분 수집
        ▼
[MySQL UPSERT]
        │
        ├─ senior_program
        └─ crawl_run_history
```

## 3. 설치

```bash
pip install -r requirements.txt
```

## 4. 환경설정

`.env.example`을 참고하여 `.env`를 수정합니다.

처음에는 DB 없이 테스트할 수 있습니다.

```env
DB_ENABLED=false
CRAWL_START_PAGE=1
CRAWL_END_PAGE=15
```

MySQL 적재를 활성화하려면:

```env
DB_ENABLED=true
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=본인비밀번호
DB_NAME=senior_program_db
```

`.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

## 5. 실행

```bash
python main.py
```

처음 실행은 최근 15페이지의 프로그램 후보 상세페이지를 수집합니다.

다음 실행부터는 기본적으로 `crawl_state.json`을 이용하여
이미 처리한 URL을 제외하고 신규 URL만 상세 수집합니다.

## 6. 프로젝트 구조

```text
gangnam_senior_program_pipeline_pro/
├─ .env
├─ .env.example
├─ .gitignore
├─ requirements.txt
├─ main.py
├─ README.md
├─ notebooks/
│  └─ 01_gangnam_senior_program_pipeline_pro.ipynb
├─ sql/
│  └─ schema.sql
├─ logs/
├─ data/
│  ├─ raw/
│  │  ├─ list/
│  │  └─ detail/
│  ├─ interim/
│  ├─ processed/
│  └─ state/
└─ src/
   └─ data_collection_pipeline/
      ├─ __init__.py
      ├─ config.py
      ├─ logging_config.py
      ├─ http_client.py
      ├─ crawling.py
      ├─ extract.py
      ├─ detail.py
      ├─ validation.py
      ├─ preprocess.py
      ├─ state.py
      ├─ load.py
      └─ pipeline.py
```

## 7. 운영 관점 체크포인트

### 실패 대응
한 페이지나 상세글 한 건이 실패해도 전체 배치를 즉시 중단하지 않고,
실패한 건을 로그/CSV에 남긴 뒤 나머지 데이터를 계속 처리합니다.

### 원본 보존
파싱 로직이 잘못되었거나 사이트 구조가 바뀌었을 때 다시 크롤링하지 않고
저장된 raw HTML로 파서를 재실행할 수 있습니다.

### 증분 수집
매번 같은 상세 URL을 반복 수집하지 않습니다.

### UPSERT
`program_key`를 UNIQUE KEY로 사용하여 동일 프로그램이 다시 들어오면
INSERT가 아니라 UPDATE합니다.

### 수집 이력
각 실행의 시작/종료, 성공/실패, 단계별 건수를
`crawl_run_history`에 기록할 수 있습니다.

## 8. 다음 실무 확장

현재 버전에서 더 발전시키려면 다음 순서가 좋습니다.

1. 사이트 구조 변경 감지 알림
2. 실패 URL 재처리 전용 명령
3. APScheduler/Windows Task Scheduler 정기 실행
4. Docker
5. Spring Boot API 연결
6. 다기관 crawler adapter 구조
7. Airflow 같은 workflow orchestrator
