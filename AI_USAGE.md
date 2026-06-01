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

## 직접 수정한 판단 사례

- STT 직접 구현보다 제공 transcript JSON 기반 처리를 우선 선택했다. 과제의 핵심 평가 포인트가 액션아이템 추출의 신뢰성과 데이터 파이프라인 설계에 있다고 판단했기 때문이다.
- 기획안에서 "회의록 자동화"보다 "액션아이템 누락 방지"를 우선 페인포인트로 정의했다. 회의록은 사후 검토가 가능하지만 액션아이템 누락은 업무 지연과 책임 불명확으로 이어진다고 판단했다.
- AI가 제안한 표지/목차형 문서 흐름 대신, 5페이지 제한 안에서 필수 평가 항목을 모두 포함하도록 본문 중심 구성으로 수정했다.
- LLM 결과를 바로 저장하는 흐름이 아니라 `confidence`, `source_utterance`, Pydantic validation, retry를 포함하는 신뢰성 설계로 조정했다.
- 시스템 아키텍처 페이지에 trade-off 문장을 추가했다. STT 직접 처리보다 제공 transcript를 우선 사용해 STT 품질 변수를 줄이고, 액션아이템 추출 신뢰성 검증에 집중하기 위한 선택이다.

## 오늘 작업 기록

- 프로젝트 scaffold 생성 및 `make run` 실행 확인
- DuckDB 초기 스키마 생성: `meetings`, `utterances`, `chunks`, `action_items`
- 기획안 PDF 작성: `docs/mobidays_meeting_action_system_proposal.pdf`
- 제출 repo 기준 작업 경로 정리: `/Users/phjeong/Desktop/mobidays-meeting-action-system`
