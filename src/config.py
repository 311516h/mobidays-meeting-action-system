from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "warehouse.duckdb"
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "ko_meeting_3speakers.json"
AUDIO_DATA_PATH = BASE_DIR / "data" / "raw" / "ko_meeting_3speakers_4min_faster.mp3"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
ACTION_ITEMS_OUTPUT_PATH = PROCESSED_DATA_DIR / "action_items.json"
SLACK_PAYLOAD_OUTPUT_PATH = PROCESSED_DATA_DIR / "slack_payload.json"
SLACK_UPDATE_EVENTS_PATH = BASE_DIR / "data" / "mock" / "slack_update_events.json"
SLACK_UPDATE_RESULT_PATH = PROCESSED_DATA_DIR / "slack_update_result.json"

DEFAULT_MEETING = {
    "meeting_id": "nova_dream_campaign_alignment_2026_06_01",
    "advertiser": "노바드림",
    "campaign": "다음달 캠페인 제안 사전 정렬",
    "meeting_date": "2026-06-01",
    "source_type": "transcript_json",
}
