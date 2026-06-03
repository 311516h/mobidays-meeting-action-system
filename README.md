# Mobidays Meeting Action System

회의 transcript를 정제하고 액션아이템을 추출한 뒤 DuckDB와 Streamlit 대시보드로 확인하는 PoC입니다.

## Tech Stack

- Python: 데이터 파이프라인과 LLM 후처리 로직 구현
- DuckDB: 별도 서버 없이 로컬 분석 쿼리와 대시보드 연결 가능
- Pydantic: LLM 구조화 출력 검증과 필수 필드 강제
- Streamlit: PoC 대시보드를 빠르게 구현하고 결과를 시각적으로 검증
- pandas: 대시보드 집계와 키워드 분석용 dataframe 처리

DuckDB는 Postgres보다 운영 부담이 낮고, 과제 PoC 규모에서는 로컬 파일 기반으로도 재현성과 분석 편의성을 확보할 수 있어 선택했습니다.

### LLM / STT Trade-off

- LLM: 원천 회의 데이터의 외부 전송 금지 조건을 고려해 실제 API 호출 대신 mock extractor로 구조화 출력, schema validation, confidence, source_utterance 저장 흐름을 구현했다.
- STT: 제공 transcript JSON을 기본 입력으로 사용해 STT 품질 변수를 줄이고, 본 과제의 핵심인 액션아이템 추출 신뢰성 검증에 집중했다.
- Audio: mp3 원천 파일은 향후 local Whisper 기반 STT 확장을 위한 raw artifact로 보관한다.

## Input Data

본 PoC는 제공 transcript JSON을 기본 입력으로 사용하며, mp3 원천 파일은 STT 확장 검증을 위한 raw artifact로 보관한다.

- Transcript: `data/raw/ko_meeting_3speakers.json`
- Audio: `data/raw/ko_meeting_3speakers_4min_faster.mp3`

## Pipeline

`make run`은 아래 흐름을 한 번에 실행한다.

```text
transcript JSON
-> meetings / utterances 적재
-> preprocessing
-> chunks 생성
-> mock LLM action_items 추출
-> DuckDB 저장
-> action_items.json 생성
-> slack_payload.json 생성
```

## Architecture

- `src/ingest.py`: transcript JSON 로드, 회의/발화 적재
- `src/preprocess.py`: 화자/역할 정규화, filler 제거, 광고 용어 약어 정규화
- `src/chunking.py`: 발화를 LLM 입력 단위 chunk로 분리
- `src/schemas.py`: Pydantic 기반 액션아이템 출력 스키마 정의
- `src/llm_client.py`: mock LLM extractor, schema validation, 중복 제거, DuckDB 저장, JSON export
- `dashboard/app.py`: DuckDB 기반 분석 대시보드

원본 발화는 `utterances.text`에 보존하고, 전처리 결과는 `utterances.normalized_text`에 분리 저장합니다. 액션아이템은 `confidence`, `source_utterance`, `reasoning`을 함께 저장해 검토와 추적이 가능하도록 설계했습니다.

## Run

```bash
make run
```

Expected output:

```text
database initialized
meeting ingested: nova_dream_campaign_alignment_2026_06_01
utterances inserted: 37
chunks inserted: 10
action_items inserted: 6
action_items output saved: data/processed/action_items.json
slack payload saved: data/processed/slack_payload.json
```

## Outputs

- DuckDB: `data/warehouse.duckdb`
- Action items: `data/processed/action_items.json`
- Slack payload sample: `data/processed/slack_payload.json`

## Evaluation

액션아이템 추출 품질은 gold set과 예측 결과를 비교해 precision, recall, F1로 측정합니다.

```bash
make evaluate
```

평가 기준은 다음과 같습니다.

- Gold file: `data/eval/gold_action_items.json`
- Prediction file: `data/processed/action_items.json`
- Match rule: `owner` exact match + `task` token Jaccard similarity 0.5 이상
- Output: prediction count, gold count, true positive, false positive, false negative, precision, recall, F1

현재 샘플 기준 결과는 `precision 1.000`, `recall 0.857`, `F1 0.923`입니다. false negative 항목을 함께 출력해 다음 프롬프트/추출 규칙 개선 대상으로 사용할 수 있습니다.

## Operation Plan

도입 후 4주 운영·검증 계획은 `docs/operation_validation_plan.md`에 정리했습니다.

주요 내용:

- 주차별 운영 계획: baseline 구축, prompt/rule 개선, pilot workflow, rollout 판단
- KPI: 정리 시간, precision/recall, low-confidence 비율, 담당자 수정률, 중복 적재
- 모니터링: pipeline, data quality, LLM quality, operation 지표
- Go/No-Go 기준: precision 0.90 이상, recall 0.85 이상, 검토 시간 15분 이하

## Dashboard

```bash
make dashboard
```

대시보드는 다음 위젯을 포함합니다.

- 주차별 회의·액션아이템 발생 추이
- 담당자별 미완료 액션아이템 Top N
- 캠페인 / 광고주별 반복 이슈 키워드
- LLM 추출 confidence 분포와 낮은 항목 드릴다운

## Prompt Strategy

프롬프트 원본은 `prompts/action_item_prompt.md`에 있습니다.

핵심 설계는 다음과 같습니다.

- 광고 캠페인 회의 맥락과 `CPM`, `ROAS`, `A/B`, `CTA`, `GA` 등 도메인 용어를 명시
- "제가 챙길게요", "정리해둘게요" 같은 한국어 암묵적 R&R 표현을 owner 추론 규칙으로 반영
- JSON schema 기반 구조화 출력 요구
- `owner`, `task`, `due_date`, `priority`, `status`, `confidence`, `source_utterance`, `reasoning` 필수화
- Pydantic validation 실패 시 재시도하고, 근거 발화가 없는 항목은 신뢰 데이터로 저장하지 않는 정책 적용

현재 구현은 외부 API 전송 없이 mock extractor로 동작합니다. 이는 원천 회의 데이터 외부 유출을 피하면서 스키마 검증, 중복 제거, confidence, source evidence 흐름을 먼저 검증하기 위한 선택입니다.

## Assumptions

- 제공 transcript JSON의 화자 분리 결과를 신뢰 가능한 입력으로 사용합니다.
- mp3 파일은 STT 확장 검증용 artifact로 보관하며, 기본 파이프라인은 transcript JSON을 사용합니다.
- 실제 LLM API 대신 mock extractor를 사용해 무료/로컬 환경에서도 end-to-end 흐름을 재현합니다.
- `make run` 재실행 시 meeting 단위 action item 결과를 다시 생성해 중복 적재를 방지합니다.
- 대시보드의 반복 이슈 키워드는 PoC 범위에서 BoW 기반으로 계산합니다.
