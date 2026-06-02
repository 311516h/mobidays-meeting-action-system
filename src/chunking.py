import hashlib
from pathlib import Path
from typing import Any

import duckdb

from src.config import DB_PATH, DEFAULT_MEETING, RAW_DATA_PATH
from src.ingest import load_transcript
from src.preprocess import normalize_role, normalize_speaker, normalize_text


DEFAULT_CHUNK_SIZE = 4


def stable_chunk_id(meeting_id: str, chunk_order: int, chunk_text: str) -> str:
    raw_key = f"{meeting_id}::{chunk_order}::{chunk_text}"
    digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:12]
    return f"chunk_{digest}"


def build_segment_lines(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    lines = []
    for segment in transcript.get("segments", []):
        speaker = normalize_speaker(segment.get("speaker"))
        role = normalize_role(segment.get("role"))
        text = normalize_text(segment.get("text", ""))

        if not text:
            continue

        lines.append(
            {
                "line_no": segment.get("line_no", segment.get("id")),
                "speaker": speaker,
                "role": role,
                "text": text,
            }
        )

    return lines


def format_chunk_text(lines: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{line['speaker']}({line['role']}): {line['text']}"
        for line in lines
    )


def build_speaker_context(lines: list[dict[str, Any]]) -> str:
    speakers = []
    seen = set()

    for line in lines:
        key = (line["speaker"], line["role"])
        if key in seen:
            continue
        seen.add(key)
        speakers.append(f"{line['speaker']}={line['role']}")

    return ", ".join(speakers)


def build_chunks(
    transcript: dict[str, Any],
    meeting_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[dict[str, Any]]:
    lines = build_segment_lines(transcript)
    chunks = []

    for start in range(0, len(lines), chunk_size):
        chunk_lines = lines[start : start + chunk_size]
        chunk_order = len(chunks) + 1
        chunk_text = format_chunk_text(chunk_lines)

        chunks.append(
            {
                "chunk_id": stable_chunk_id(meeting_id, chunk_order, chunk_text),
                "meeting_id": meeting_id,
                "chunk_order": chunk_order,
                "speaker_context": build_speaker_context(chunk_lines),
                "chunk_text": chunk_text,
            }
        )

    return chunks


def upsert_chunks(
    conn: duckdb.DuckDBPyConnection,
    chunks: list[dict[str, Any]],
) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO chunks
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            [
                chunk["chunk_id"],
                chunk["meeting_id"],
                chunk["chunk_order"],
                chunk["speaker_context"],
                chunk["chunk_text"],
            ]
            for chunk in chunks
        ],
    )


def chunk_transcript(
    path: Path = RAW_DATA_PATH,
    db_path: Path = DB_PATH,
    meeting_id: str = DEFAULT_MEETING["meeting_id"],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[str, Any]:
    transcript = load_transcript(path)
    chunks = build_chunks(transcript, meeting_id, chunk_size)

    with duckdb.connect(db_path) as conn:
        upsert_chunks(conn, chunks)

    return {
        "meeting_id": meeting_id,
        "chunk_count": len(chunks),
    }
