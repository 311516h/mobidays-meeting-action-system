import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from src.config import DB_PATH, DEFAULT_MEETING, RAW_DATA_PATH
from src.preprocess import normalize_role, normalize_speaker, normalize_text, normalize_whitespace


def load_transcript(path: Path = RAW_DATA_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def stable_id(*parts: object, prefix: str) -> str:
    raw_key = "::".join(str(part) for part in parts)
    digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def build_speaker_role_map(transcript: dict[str, Any]) -> dict[str, str]:
    return {
        normalize_speaker(speaker["name"]): normalize_role(speaker.get("role", ""))
        for speaker in transcript.get("speakers", [])
    }


def build_meeting_record() -> dict[str, Any]:
    return {
        **DEFAULT_MEETING,
        "created_at": datetime.now(),
    }


def build_utterance_records(
    transcript: dict[str, Any],
    meeting_id: str,
) -> list[dict[str, Any]]:
    speaker_roles = build_speaker_role_map(transcript)
    records = []

    for segment in transcript.get("segments", []):
        text = normalize_whitespace(segment.get("text", ""))
        speaker = normalize_speaker(segment.get("speaker", "unknown"))
        role = normalize_role(segment.get("role") or speaker_roles.get(speaker, ""))
        line_no = segment.get("line_no", segment.get("id", len(records) + 1))

        records.append(
            {
                "utterance_id": stable_id(
                    meeting_id,
                    line_no,
                    speaker,
                    text,
                    prefix="utt",
                ),
                "meeting_id": meeting_id,
                "speaker": speaker,
                "role": role,
                "start_time": segment.get("start_time"),
                "end_time": segment.get("end_time"),
                "text": text,
                "normalized_text": normalize_text(text),
            }
        )

    return records


def upsert_meeting(conn: duckdb.DuckDBPyConnection, meeting: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO meetings
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            meeting["meeting_id"],
            meeting["advertiser"],
            meeting["campaign"],
            meeting["meeting_date"],
            meeting["source_type"],
            meeting["created_at"],
        ],
    )


def upsert_utterances(
    conn: duckdb.DuckDBPyConnection,
    utterances: list[dict[str, Any]],
) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO utterances
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            [
                utterance["utterance_id"],
                utterance["meeting_id"],
                utterance["speaker"],
                utterance["role"],
                utterance["start_time"],
                utterance["end_time"],
                utterance["text"],
                utterance["normalized_text"],
            ]
            for utterance in utterances
        ],
    )


def ingest_transcript(path: Path = RAW_DATA_PATH, db_path: Path = DB_PATH) -> dict[str, Any]:
    transcript = load_transcript(path)
    meeting = build_meeting_record()
    utterances = build_utterance_records(transcript, meeting["meeting_id"])

    with duckdb.connect(db_path) as conn:
        upsert_meeting(conn, meeting)
        upsert_utterances(conn, utterances)

    return {
        "meeting_id": meeting["meeting_id"],
        "utterance_count": len(utterances),
        "source_path": str(path),
    }
