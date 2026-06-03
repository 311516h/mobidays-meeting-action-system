import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from src.config import (
    ACTION_ITEMS_OUTPUT_PATH,
    BASE_DIR,
    DB_PATH,
    SLACK_PAYLOAD_OUTPUT_PATH,
)
from src.schemas import ActionItem, ActionItemRecord, SlackPayload


ACTION_PATTERNS = [
    {
        "keywords": ["보정", "다시 돌리"],
        "owner": "수아",
        "task": "픽셀 이벤트 중복 발화 문제를 보정하고 전환 수치를 다시 산출한다.",
        "due_date": "내일 오전",
        "priority": "high",
        "reasoning": "전환 수치가 제안서 마무리의 선행 조건으로 언급됨",
        "confidence": 0.9,
    },
    {
        "keywords": ["비주얼 카드 순서", "빈 슬롯"],
        "owner": "채린",
        "task": "비주얼 카드 순서와 빈 슬롯 자리 카피를 정리한다.",
        "due_date": "내일 오전",
        "priority": "medium",
        "reasoning": "화자가 직접 정리해두겠다고 명시함",
        "confidence": 0.88,
    },
    {
        "keywords": ["캠페인 세트 분리"],
        "owner": "수아",
        "task": "캠페인 세트를 분리하고 운영 계정 적용 전 광고주 컨펌을 받는다.",
        "due_date": "수요일 오전",
        "priority": "high",
        "reasoning": "화자가 직접 완료 시점과 광고주 컨펌 필요성을 언급함",
        "confidence": 0.91,
    },
    {
        "keywords": ["광고주 컨펌", "슬랙으로 정리"],
        "owner": "지훈",
        "task": "광고주 컨펌 필요 사항을 Slack에 정리하고 확인한다.",
        "due_date": "오늘 중",
        "priority": "medium",
        "reasoning": "컨펌 담당자가 불명확해 후속 정리가 필요함",
        "confidence": 0.72,
    },
    {
        "keywords": ["같이 챙길게요"],
        "owner": "수아",
        "task": "CTA 변경에 따른 전환 추적 이벤트를 함께 점검한다.",
        "due_date": "픽셀 정리 이후",
        "priority": "high",
        "reasoning": "CTA 변경 시 전환 이벤트 재점검 필요성이 명시됨",
        "confidence": 0.86,
    },
    {
        "keywords": ["누끼 컷", "푸시"],
        "owner": "지훈",
        "task": "신제품 누끼 컷 전달을 광고주 담당자에게 다시 요청한다.",
        "due_date": "오늘 중",
        "priority": "high",
        "reasoning": "소재 미수급이 메인 비주얼 작업의 blocker로 확인됨",
        "confidence": 0.89,
    },
    {
        "keywords": ["A/B", "다시 세팅"],
        "owner": "수아",
        "task": "헤드라인 변경 후 A/B 테스트를 새 카피 기준으로 다시 세팅한다.",
        "due_date": "카피 변경 후",
        "priority": "medium",
        "reasoning": "기존 A/B를 닫고 바뀐 카피로 다시 세팅해야 한다고 명시됨",
        "confidence": 0.87,
    },
    {
        "keywords": ["슬랙에 바로 올려"],
        "owner": "지훈",
        "task": "누끼 컷 또는 픽셀 보정 결과가 나오면 Slack에 바로 공유한다.",
        "due_date": "결과 확인 즉시",
        "priority": "medium",
        "reasoning": "팀장이 결과 공유 채널과 시점을 명시함",
        "confidence": 0.84,
    },
]


def stable_action_item_id(
    meeting_id: str,
    chunk_id: str,
    owner: str,
    task: str,
) -> str:
    raw_key = f"{meeting_id}::{chunk_id}::{owner}::{task}"
    digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:12]
    return f"act_{digest}"


def parse_speaker_from_utterance(source_utterance: str) -> str:
    match = re.match(r"^(?P<speaker>[^()]+)\(", source_utterance)
    if match:
        return match.group("speaker").strip()
    return "미정"


def find_source_line(chunk_text: str, keywords: list[str]) -> str | None:
    for line in chunk_text.splitlines():
        if all(keyword in line for keyword in keywords):
            return line.strip()
    return None


def extract_action_items_from_chunk(chunk: dict[str, Any]) -> list[ActionItemRecord]:
    records = []

    for pattern in ACTION_PATTERNS:
        source_utterance = find_source_line(chunk["chunk_text"], pattern["keywords"])
        if not source_utterance:
            continue

        owner = pattern.get("owner") or parse_speaker_from_utterance(source_utterance)
        action_item = ActionItem(
            owner=owner,
            task=pattern["task"],
            due_date=pattern["due_date"],
            priority=pattern["priority"],
            status="todo",
            confidence=pattern["confidence"],
            source_utterance=source_utterance,
            reasoning=pattern["reasoning"],
        )

        records.append(
            ActionItemRecord(
                **action_item.model_dump(),
                action_item_id=stable_action_item_id(
                    chunk["meeting_id"],
                    chunk["chunk_id"],
                    action_item.owner,
                    action_item.task,
                ),
                meeting_id=chunk["meeting_id"],
                chunk_id=chunk["chunk_id"],
            )
        )

    return records


def load_chunks(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    with duckdb.connect(db_path) as conn:
        rows = conn.sql(
            """
            SELECT chunk_id, meeting_id, chunk_order, speaker_context, chunk_text
            FROM chunks
            ORDER BY chunk_order
            """
        ).fetchall()

    return [
        {
            "chunk_id": row[0],
            "meeting_id": row[1],
            "chunk_order": row[2],
            "speaker_context": row[3],
            "chunk_text": row[4],
        }
        for row in rows
    ]


def load_action_items(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    with duckdb.connect(db_path) as conn:
        rows = conn.sql(
            """
            SELECT
                action_item_id,
                meeting_id,
                chunk_id,
                owner,
                task,
                due_date,
                priority,
                status,
                confidence,
                source_utterance,
                reasoning
            FROM action_items
            ORDER BY priority, owner, task
            """
        ).fetchall()

    return [
        {
            "action_item_id": row[0],
            "meeting_id": row[1],
            "chunk_id": row[2],
            "owner": row[3],
            "task": row[4],
            "due_date": row[5],
            "priority": row[6],
            "status": row[7],
            "confidence": row[8],
            "source_utterance": row[9],
            "reasoning": row[10],
        }
        for row in rows
    ]


def upsert_action_items(
    conn: duckdb.DuckDBPyConnection,
    action_items: list[ActionItemRecord],
) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO action_items
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            [
                item.action_item_id,
                item.meeting_id,
                item.chunk_id,
                item.owner,
                item.task,
                item.due_date,
                item.priority,
                item.status,
                item.confidence,
                item.source_utterance,
                item.reasoning,
                datetime.now(),
            ]
            for item in action_items
        ],
    )


def extract_and_store_action_items(db_path: Path = DB_PATH) -> dict[str, Any]:
    chunks = load_chunks(db_path)
    action_items = []

    for chunk in chunks:
        action_items.extend(extract_action_items_from_chunk(chunk))

    action_items = deduplicate_action_items(action_items)

    with duckdb.connect(db_path) as conn:
        meeting_ids = sorted({item.meeting_id for item in action_items})
        for meeting_id in meeting_ids:
            conn.execute(
                "DELETE FROM action_item_status_events WHERE meeting_id = ?",
                [meeting_id],
            )
            conn.execute(
                "DELETE FROM action_items WHERE meeting_id = ?",
                [meeting_id],
            )
        upsert_action_items(conn, action_items)

    return {
        "chunk_count": len(chunks),
        "action_item_count": len(action_items),
    }


def deduplicate_action_items(
    action_items: list[ActionItemRecord],
) -> list[ActionItemRecord]:
    deduped = {}

    for item in action_items:
        key = (item.owner, item.task)
        current = deduped.get(key)
        if current is None or item.confidence > current.confidence:
            deduped[key] = item

    return list(deduped.values())


def build_slack_payload(action_items: list[dict[str, Any]]) -> SlackPayload:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "노바드림 캠페인 회의 액션아이템",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"총 {len(action_items)}개 액션아이템이 추출되었습니다.",
            },
        },
    ]

    for item in action_items:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*[{item['priority']}] {item['task']}*\n"
                        f"- 담당자: {item['owner']}\n"
                        f"- 기한: {item['due_date']}\n"
                        f"- 상태: {item['status']}\n"
                        f"- confidence: {item['confidence']:.2f}\n"
                        f"- 근거: {item['source_utterance']}"
                    ),
                },
            }
        )

    return SlackPayload(
        channel="#campaign-action-items",
        text="노바드림 캠페인 회의 액션아이템",
        blocks=blocks,
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def export_action_item_outputs(
    db_path: Path = DB_PATH,
    action_items_path: Path = ACTION_ITEMS_OUTPUT_PATH,
    slack_payload_path: Path = SLACK_PAYLOAD_OUTPUT_PATH,
) -> dict[str, Any]:
    action_items = load_action_items(db_path)
    slack_payload = build_slack_payload(action_items)

    write_json(action_items_path, action_items)
    write_json(slack_payload_path, slack_payload.model_dump())

    return {
        "action_items_path": str(action_items_path.relative_to(BASE_DIR)),
        "slack_payload_path": str(slack_payload_path.relative_to(BASE_DIR)),
        "action_item_count": len(action_items),
    }
