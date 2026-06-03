# 4-Week Operation & Validation Plan

## 목적

본 PoC를 실제 사내 회의 흐름에 도입하기 전에 4주 동안 제한된 팀에서 운영 검증한다. 목표는 단순 자동화 성공 여부가 아니라 액션아이템 누락 감소, 담당자 검토 시간 절감, 낮은 신뢰도 항목의 관리 가능성을 확인하는 것이다.

## 운영 가정

- 대상: 광고 운영/마케팅 관련 2~3개 팀
- 규모: 주 20~30건 회의 transcript 기준
- 입력: 초기 2주는 제공 transcript 또는 내부 비식별 transcript, 이후 local STT 확장 검토
- 검토자: 회의 담당자 또는 PM 1명
- 저장: 원본 발화, 정규화 발화, chunk, action item, confidence, source utterance를 분리 저장

## 핵심 KPI

| KPI | 측정 방식 | 4주 목표 |
| --- | --- | --- |
| 회의 1건당 정리 시간 | 담당자 수동 기록 | 30~60분 -> 10~15분 |
| 액션아이템 precision | gold set 대비 `make evaluate` | 0.90 이상 |
| 액션아이템 recall | gold set 대비 `make evaluate` | 0.85 이상 |
| 낮은 confidence 비율 | `confidence < 0.7` 비중 | 20% 이하 |
| 담당자 수정률 | owner/task/due_date 수정 건수 | 주차별 감소 추세 |
| 중복 적재 발생 | 동일 meeting 재실행 후 row count 확인 | 0건 |

## 4주 검증 계획

### Week 1: Baseline & Gold Set 구축

- 실제 회의 transcript 5~10건을 수집하거나 비식별 샘플을 준비한다.
- 사람이 직접 액션아이템 gold set을 작성한다.
- `make run`, `make evaluate`로 baseline precision/recall/F1을 측정한다.
- 낮은 confidence 항목과 false negative 유형을 분류한다.

판단 기준:

- owner, task, due_date 중 어떤 필드에서 오류가 많은지 확인
- 암묵적 R&R, 흐릿한 결정, 광고 약어 처리 실패 유형을 우선순위화

### Week 2: Prompt & Rule 개선

- Week 1의 false negative와 낮은 confidence 케이스를 prompt few-shot에 반영한다.
- 약어 사전과 owner 추론 규칙을 보강한다.
- 같은 회의 재실행 시 중복 적재가 없는지 확인한다.
- 대시보드에서 낮은 confidence drilldown을 검토 프로세스에 연결한다.

판단 기준:

- recall이 개선되는지 확인
- precision 하락이 발생하면 근거 발화 없는 항목 저장 제한을 강화

### Week 3: Pilot Workflow 운영

- 제한된 팀에서 회의 후 자동 생성 결과를 실제 담당자가 검토한다.
- Slack payload를 mock으로 공유하고, 담당자 확인/수정 내역을 기록한다.
- 회의 1건당 검토 시간과 수정률을 수집한다.
- owner별 미완료 액션아이템과 반복 이슈 키워드가 실제 의사결정에 도움이 되는지 확인한다.

판단 기준:

- 담당자가 자동 결과를 신뢰하고 수정 가능한 수준인지 확인
- dashboard가 단순 조회가 아니라 업무 병목 파악에 쓰이는지 확인

### Week 4: Go/No-Go & Rollout 기준 확정

- 4주 누적 precision/recall, 수정률, 시간 절감 효과를 정리한다.
- false negative 상위 유형과 낮은 confidence 원인을 문서화한다.
- local STT 적용 여부, 실제 LLM API 적용 여부, Slack/Notion 연동 범위를 결정한다.
- 100명 조직 기준 운영 비용과 담당자 검토 프로세스를 확정한다.

Go 기준:

- precision 0.90 이상
- recall 0.85 이상
- 회의 1건당 검토 시간이 15분 이하
- 낮은 confidence 항목이 검토 큐에서 관리 가능
- 재실행 중복 적재 0건

No-Go 또는 보류 기준:

- owner mis-mapping이 반복되어 수동 수정 부담이 큰 경우
- 낮은 confidence 항목이 30% 이상 유지되는 경우
- 실제 회의 transcript에서 recall이 0.75 미만인 경우

## 모니터링 항목

- Pipeline: 실행 성공/실패, 처리 시간, meeting별 적재 row count
- Data Quality: null owner, empty task, duplicate action item, invalid due_date
- LLM Quality: confidence 분포, false positive, false negative, schema validation 실패
- Operation: 담당자 수정률, 검토 소요 시간, overdue action item 비율

## 개선 루프

1. 낮은 confidence 및 false negative 항목을 주 1회 리뷰한다.
2. 오류 유형을 prompt few-shot, 전처리 사전, owner 추론 규칙 중 하나로 매핑한다.
3. 수정 후 `make run`과 `make evaluate`로 지표 변화를 확인한다.
4. precision이 떨어지면 저장 조건을 강화하고, recall이 낮으면 few-shot과 chunking 기준을 보완한다.
