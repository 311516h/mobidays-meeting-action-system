# AI Usage

## 사용 도구

- ChatGPT / Codex: 과제 요구사항 해석, 프로젝트 구조 설계, 초기 코드 스캐폴딩, 기획안 구성 검토에 사용
- Canva: 5페이지 이내 기획안 PDF 시각화와 제출용 문서 제작에 사용

## 활용 방식

- 과제 요구사항을 기준으로 데이터 파이프라인, 저장소 스키마, 대시보드 구성 요소를 정리했다.
- AI가 제안한 구조를 그대로 사용하지 않고, PoC 범위와 제출 기한을 고려해 DuckDB, Streamlit, Pydantic 중심으로 단순화했다.
- Codex를 사용해 `src/`, `data/`, `dashboard/`, `docs/`, `prompts/` 중심의 Python 프로젝트 구조를 만들고, `make run`으로 DuckDB 테이블을 초기화하는 최소 실행 흐름을 구성했다.
- ChatGPT와 함께 기획안의 5페이지 구성을 검토했다. 최종 구성은 문제 정의, End-to-End Architecture, Data Model & Idempotency, LLM Extraction Reliability, Impact & Failure Handling으로 정리했다.
- Canva 템플릿 선택 과정에서 표지, 목차, 감사 페이지를 제외하고 과제 요구사항을 직접 커버하는 본문 5장으로 압축했다.
- Codex를 사용해 제공 transcript JSON 구조를 확인하고, `meetings -> utterances -> chunks -> action_items -> processed JSON` 흐름을 구현했다.
- 실제 LLM API 호출 전 단계로 mock extractor를 구성해 Pydantic schema, confidence, source_utterance, reasoning, Slack payload 생성 흐름을 먼저 검증했다.
- Codex를 사용해 Streamlit 대시보드의 필수 위젯 구성을 설계하고, DuckDB 기반 집계 쿼리와 confidence 드릴다운 흐름을 구현했다.
- 액션아이템 추출 프롬프트를 실제 LLM 연동 가능한 문서 형태로 구체화했다.
- Codex를 사용해 액션아이템 추출 품질 평가 코드를 추가하고, gold set 대비 precision, recall, F1을 계산하는 검증 흐름을 구성했다.

## 직접 수정한 판단 사례

- STT 직접 구현보다 제공 transcript JSON 기반 처리를 우선 선택했다. 과제의 핵심 평가 포인트가 액션아이템 추출의 신뢰성과 데이터 파이프라인 설계에 있다고 판단했기 때문이다.
- 기획안에서 "회의록 자동화"보다 "액션아이템 누락 방지"를 우선 페인포인트로 정의했다. 회의록은 사후 검토가 가능하지만 액션아이템 누락은 업무 지연과 책임 불명확으로 이어진다고 판단했다.
- AI가 제안한 표지/목차형 문서 흐름 대신, 5페이지 제한 안에서 필수 평가 항목을 모두 포함하도록 본문 중심 구성으로 수정했다.
- LLM 결과를 바로 저장하는 흐름이 아니라 `confidence`, `source_utterance`, Pydantic validation, retry를 포함하는 신뢰성 설계로 조정했다.
- 시스템 아키텍처 페이지에 trade-off 문장을 추가했다. STT 직접 처리보다 제공 transcript를 우선 사용해 STT 품질 변수를 줄이고, 액션아이템 추출 신뢰성 검증에 집중하기 위한 선택이다.
- 전처리 단계에서는 원문 발화를 `text`에 보존하고, filler 제거와 약어 정규화 결과만 `normalized_text`에 저장하도록 조정했다. 원문 근거 추적성을 잃지 않기 위해서다.
- mock extractor가 회의 후반 요약 발화에서 같은 업무를 중복 추출하는 문제가 있어, `(owner, task)` 기준 중복 제거를 추가했다.
- CTA 관련 액션아이템은 질문한 화자가 아니라 "그건 제가 같이 챙길게요"라고 말한 수아가 담당자로 잡히도록 owner override 규칙을 추가했다.
- `make run` 재실행 시 중복 결과가 쌓이지 않도록 action_items 저장 전 meeting 단위 기존 결과를 삭제하고 다시 적재하는 방식으로 보정했다.
- 대시보드는 랜딩 페이지가 아니라 운영자가 바로 판단할 수 있는 분석 화면으로 구성했다. 상단 KPI, 발생 추이, 담당자별 미완료, 반복 이슈 키워드, confidence 드릴다운 순서로 배치했다.
- 반복 이슈 분석은 임베딩 대신 BoW 키워드 집계로 단순화했다. 단일 샘플 PoC에서는 구현 복잡도보다 설명 가능성과 재현성이 더 중요하다고 판단했다.
- Streamlit 첫 실행 이메일 프롬프트와 Makefile target 충돌을 발견해 `.PHONY`와 headless 옵션을 추가했다.
- 평가 지표는 단순 문자열 완전일치가 아니라 `owner` exact match와 `task` token Jaccard similarity를 함께 사용하도록 수정했다. 같은 업무가 자연어로 약간 다르게 표현될 수 있기 때문이다.
- gold set에는 현재 mock extractor가 놓치는 액션아이템 1건을 포함했다. precision만 높게 보이는 결과가 아니라 recall 개선 여지를 드러내기 위한 판단이다.

## 2026-06-01 작업 기록

- 프로젝트 scaffold 생성 및 `make run` 실행 확인
- DuckDB 초기 스키마 생성: `meetings`, `utterances`, `chunks`, `action_items`
- 기획안 PDF 작성: `docs/mobidays_meeting_action_system_proposal.pdf`
- 제출 repo 기준 작업 경로 정리: `/Users/phjeong/Desktop/mobidays-meeting-action-system`

## 2026-06-02 작업 기록

- 제공 transcript JSON과 mp3 파일을 `data/raw/`에 추가했다.
- `ingest.py`에서 transcript JSON을 읽어 `meetings`, `utterances`에 적재했다.
- `preprocess.py`에서 화자/역할 정규화, filler 제거, 광고 용어 약어 정규화를 구현했다.
- `chunking.py`에서 발화를 4개 단위로 묶어 LLM 입력용 chunk를 생성했다.
- `schemas.py`에 Pydantic 기반 `ActionItem`, `ActionItemRecord`, `SlackPayload` 스키마를 정의했다.
- `llm_client.py`에 mock LLM extractor, schema validation, 중복 제거, DuckDB 저장, `action_items.json`, `slack_payload.json` export 흐름을 구현했다.
- `make run` 실행 결과 `utterances 37`, `chunks 10`, `action_items 6` 생성까지 확인했다.

## 2026-06-03 작업 기록

- `dashboard/app.py`에 Streamlit 대시보드를 구현했다.
- 대시보드에 필수 위젯 4개를 반영했다.
  - 주차별 회의·액션아이템 발생 추이
  - 담당자별 미완료 액션아이템 Top N
  - 캠페인 / 광고주별 반복 이슈 키워드
  - LLM 추출 confidence 분포와 낮은 항목 드릴다운
- `Makefile`에 `.PHONY`를 추가하고, `make dashboard`가 Streamlit 서버를 안정적으로 실행하도록 headless 옵션을 적용했다.
- `prompts/action_item_prompt.md`를 role, domain context, extraction rules, implicit R&R, JSON schema, few-shot, validation/retry policy까지 포함하도록 구체화했다.
- `README.md`에 기술 스택 선택 근거, 아키텍처, 대시보드 위젯, 프롬프트 전략, 가정 사항을 보강했다.
- `src/evaluate.py`와 `data/eval/gold_action_items.json`을 추가해 추출 품질 평가 지표를 계산했다.
- `make evaluate` 실행 결과 `precision 1.000`, `recall 0.857`, `F1 0.923`을 확인했다.
