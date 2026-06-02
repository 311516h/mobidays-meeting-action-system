# Mobidays Meeting Action System

회의 transcript를 정제하고 액션아이템을 추출한 뒤 DuckDB와 Streamlit 대시보드로 확인하는 PoC입니다.

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

## Dashboard

```bash
make dashboard
```
