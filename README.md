# 강남 소재 노인종합복지관 시니어 프로그램 데이터 수집 파이프라인

강남 소재 노인종합복지관 공지사항에서 시니어 프로그램 관련 게시글을 수집하고,
목록 및 상세 페이지 파싱, 데이터 전처리 및 검증, 증분 수집, MySQL 적재까지 수행하는 데이터 수집 파이프라인입니다.

---

## 1. 프로젝트 개요

강남 소재 노인종합복지관 공지사항을 대상으로 프로그램 관련 게시글을 수집합니다.

목록 페이지에서 게시글 정보를 수집한 뒤 프로그램 관련 게시글을 선별하고,
각 상세 페이지에서 모집기간, 대상, 장소, 비용 등 프로그램 정보를 추출합니다.

수집된 데이터는 전처리 및 검증 과정을 거쳐 CSV로 저장되며,
설정에 따라 MySQL 데이터베이스에 UPSERT 방식으로 적재할 수 있습니다.

### 주요 기능

- 공지사항 목록 페이지 크롤링
- 상세 페이지 HTML 수집
- 프로그램 관련 게시글 선별
- 프로그램 상세 정보 추출
- 원본 HTML 저장
- CSV 데이터 생성
- 중복 데이터 제거
- 필수값 및 날짜 형식 검증
- 증분 수집
- MySQL UPSERT
- 크롤링 실행 이력 저장
- 실행 로그 기록
- 환경변수 기반 설정 관리

---

## 2. 데이터 처리 흐름

```text
강남 소재 노인종합복지관 공지사항
        │
        ▼
[목록 페이지 수집]
        │
        ▼
data/raw/list/<batch_id>/
        │
        ▼
[목록 데이터 파싱]
 title / category / date / url
        │
        ▼
data/interim/<batch_id>/notice_list.csv
        │
        ▼
[프로그램 관련 게시글 선별]
        │
        ▼
[상세 페이지 수집 및 파싱]
 모집기간 / 접수방법 / 대상 / 문의
 운영기간 / 장소 / 인원 / 비용 / 본문
        │
        ▼
data/raw/detail/<batch_id>/
        │
        ▼
data/interim/<batch_id>/notice_detail.csv
        │
        ▼
[전처리 및 데이터 검증]
        │
        ▼
data/processed/senior_programs_<batch_id>.csv
        │
        ├────► data/state/crawl_state.json
        │
        ▼
[MySQL]
        │
        ├─ senior_program
        └─ crawl_run_history
```

---

## 3. 수집 데이터

최종 데이터에는 다음과 같은 정보가 포함됩니다.

| 컬럼 | 설명 |
|---|---|
| `program_key` | 프로그램 고유 식별값 |
| `notice_id` | 게시글 ID |
| `center_name` | 기관명 |
| `region` | 지역 |
| `category` | 게시글 분류 |
| `title` | 게시글 제목 |
| `views` | 조회수 |
| `post_date` | 게시일 |
| `detail_url` | 상세페이지 URL |
| `recruit_period` | 모집기간 |
| `apply_method` | 접수방법 |
| `target` | 대상 |
| `contact` | 문의 정보 |
| `phone` | 전화번호 |
| `program_period` | 프로그램 운영기간 |
| `location` | 장소 |
| `capacity` | 모집 인원 |
| `capacity_num` | 모집 인원 숫자값 |
| `fee` | 비용 |
| `body_text` | 본문 |
| `detail_status` | 상세 수집 상태 |
| `batch_id` | 수집 배치 ID |

---

## 4. 프로젝트 구조

```text
gangnam_senior_program_pipeline_pro/
├─ .env.example
├─ .gitignore
├─ main.py
├─ README.md
├─ requirements.txt
│
├─ notebooks/
│  └─ 01_gangnam_senior_program_pipeline_pro.ipynb
│
├─ sql/
│  └─ schema.sql
│
├─ logs/
│
├─ data/
│  ├─ raw/
│  │  ├─ list/
│  │  └─ detail/
│  ├─ interim/
│  ├─ processed/
│  └─ state/
│
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

---

## 5. 주요 모듈

| 파일 | 역할 |
|---|---|
| `main.py` | 전체 파이프라인 실행 |
| `config.py` | 환경변수 및 설정 관리 |
| `logging_config.py` | 로그 설정 |
| `http_client.py` | HTTP 세션, 재시도, timeout 설정 |
| `crawling.py` | 목록 페이지 수집 |
| `extract.py` | 목록 HTML 파싱 및 CSV 생성 |
| `detail.py` | 상세 페이지 수집 및 정보 추출 |
| `validation.py` | 데이터 품질 검증 |
| `preprocess.py` | 데이터 정제 및 가공 |
| `state.py` | 수집 URL 상태 관리 |
| `load.py` | MySQL UPSERT 및 실행 이력 저장 |
| `pipeline.py` | 전체 처리 단계 제어 |

---

## 6. 설치

### 저장소 Clone

```bash
git clone <repository-url>
cd gangnam_senior_program_pipeline_pro
```

### 패키지 설치

```bash
pip install -r requirements.txt
```

주요 라이브러리:

- requests
- BeautifulSoup4
- pandas
- python-dotenv
- SQLAlchemy
- PyMySQL

---

## 7. 환경 설정

`.env.example`을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

기본 설정 예시:

```env
APP_ENV=local

DB_ENABLED=false

CRAWL_START_PAGE=1
CRAWL_END_PAGE=15

REQUEST_INTERVAL=0.5

CONNECT_TIMEOUT=5
READ_TIMEOUT=30

MAX_RETRIES=3
BACKOFF_FACTOR=0.8
```

### MySQL 사용 시

```env
DB_ENABLED=true

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=본인비밀번호
DB_NAME=senior_program_db
```

`.env` 파일은 `.gitignore`에 포함되어 Git 저장소에서 제외됩니다.

---

## 8. 실행

프로젝트 루트에서 다음 명령어를 실행합니다.

```bash
python main.py
```

실행 결과 예시:

```text
======================================================================
강남소재노인종합복지관 데이터 파이프라인 결과
======================================================================
배치 ID       : 20260827_161116
목록 데이터    : 000건
상세 수집      : 000건
전처리 완료    : 000건
DB 적재       : 000건
결과 파일      : data/processed/senior_programs_<batch_id>.csv
```

---

## 9. 증분 수집

기본 실행은 증분 수집 방식으로 동작합니다.

```python
result = run_pipeline(
    incremental=True,
)
```

처리한 상세페이지 URL은 다음 파일에 저장됩니다.

```text
data/state/crawl_state.json
```

다음 실행 시 이미 처리한 URL을 제외하고 신규 URL을 대상으로 상세 수집을 진행합니다.

---

## 10. 데이터 검증

전처리된 데이터는 다음 항목을 기준으로 검증합니다.

- 상세 URL 중복 여부
- 제목 누락 여부
- 게시일 형식 오류
- 상세 URL 누락 여부
- 상세 페이지 수집 성공률

필수 컬럼:

```text
center_name
region
title
post_date
detail_url
```

---

## 11. MySQL 적재

`DB_ENABLED=true`로 설정하면 전처리된 데이터를 MySQL에 저장합니다.

### senior_program

프로그램 데이터를 저장하는 테이블입니다.

`program_key`에 UNIQUE 제약조건을 적용하고,
동일한 프로그램이 다시 수집될 경우 `ON DUPLICATE KEY UPDATE`를 통해 기존 데이터를 갱신합니다.

### crawl_run_history

각 파이프라인 실행 결과를 저장합니다.

주요 정보:

- batch ID
- 시작 시간
- 종료 시간
- 실행 상태
- 목록 데이터 수
- 상세 데이터 수
- 전처리 데이터 수
- DB 적재 건수
- 오류 메시지

---

## 12. 데이터 저장 경로

### Raw 목록 HTML

```text
data/raw/list/<batch_id>/
```

### Raw 상세 HTML

```text
data/raw/detail/<batch_id>/
```

### 중간 데이터

```text
data/interim/<batch_id>/
```

### 최종 데이터

```text
data/processed/senior_programs_<batch_id>.csv
```

### 수집 상태

```text
data/state/crawl_state.json
```

### 실행 로그

```text
logs/
```

---

## 13. Git 관리 제외 항목

다음 파일 및 디렉터리는 `.gitignore`를 통해 Git 관리에서 제외합니다.

```text
.env
__pycache__/
*.py[cod]
.ipynb_checkpoints/
.venv/
venv/
logs/*.log
data/raw/
data/interim/
data/processed/
data/state/
```
