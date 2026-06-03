import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from src.config import (
    BASE_DIR,
    DB_PATH,
    SLACK_UPDATE_EVENTS_PATH,
    SLACK_UPDATE_RESULT_PATH,
)
from src.llm_client import export_action_item_outputs, write_json
from src.schemas import Status


ALLOWED_STATUSES = set(Status.__args__)


def load_events(path: Path = SLACK_UPDATE_EVENTS_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def event_exists(conn: duckdb.DuckDBPyConnection, event_id: str) -> bool:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM action_item_status_events
        WHERE event_id = ?
        """,
        [event_id],
    ).fetchone()
    return bool(row and row[0])


def find_action_item(
    conn: duckdb.DuckDBPyConnection,
    event: dict[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    if event.get("action_item_id"):
        rows = conn.execute(
            """
            SELECT action_item_id, meeting_id, owner, task, status
            FROM action_items
            WHERE action_item_id = ?
            """,
            [event["action_item_id"]],
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT action_item_id, meeting_id, owner, task, status
            FROM action_items
            WHERE owner = ?
              AND task LIKE ?
            """,
            [event.get("owner"), f"%{event.get('task_contains', '')}%"],
        ).fetchall()

    if not rows:
        return "not_found", None

    if len(rows) > 1:
        return "ambiguous", None

    row = rows[0]
    return None, {
        "action_item_id": row[0],
        "meeting_id": row[1],
        "owner": row[2],
        "task": row[3],
        "status": row[4],
    }


def apply_event(
    conn: duckdb.DuckDBPyConnection,
    event: dict[str, Any],
) -> dict[str, Any]:
    event_id = event["event_id"]
    new_status = event.get("new_status")

    if event_exists(conn, event_id):
        return {
            "event_id": event_id,
            "result": "skipped",
            "reason": "duplicate_event",
        }

    if new_status not in ALLOWED_STATUSES:
        return {
            "event_id": event_id,
            "result": "skipped",
            "reason": "invalid_status",
            "new_status": new_status,
        }

    lookup_error, item = find_action_item(conn, event)
    if lookup_error:
        return {
            "event_id": event_id,
            "result": "skipped",
            "reason": lookup_error,
        }

    assert item is not None
    previous_status = item["status"]
    event_ts = event.get("event_ts") or datetime.now().isoformat(timespec="seconds")

    conn.execute(
        """
        UPDATE action_items
        SET status = ?
        WHERE action_item_id = ?
        """,
        [new_status, item["action_item_id"]],
    )
    conn.execute(
        """
        INSERT INTO action_item_status_events
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            event_id,
            item["action_item_id"],
            item["meeting_id"],
            previous_status,
            new_status,
            event.get("actor", "unknown"),
            event.get("note", ""),
            event_ts,
            datetime.now(),
        ],
    )

    return {
        "event_id": event_id,
        "result": "updated",
        "action_item_id": item["action_item_id"],
        "owner": item["owner"],
        "task": item["task"],
        "previous_status": previous_status,
        "new_status": new_status,
    }


def apply_slack_updates(
    db_path: Path = DB_PATH,
    events_path: Path = SLACK_UPDATE_EVENTS_PATH,
    result_path: Path = SLACK_UPDATE_RESULT_PATH,
) -> dict[str, Any]:
    events = load_events(events_path)

    with duckdb.connect(db_path) as conn:
        results = [apply_event(conn, event) for event in events]

    export_action_item_outputs(db_path=db_path)

    payload = {
        "event_count": len(events),
        "updated_count": sum(1 for result in results if result["result"] == "updated"),
        "skipped_count": sum(1 for result in results if result["result"] == "skipped"),
        "results": results,
    }
    write_json(result_path, payload)
    return {
        **payload,
        "result_path": str(result_path.relative_to(BASE_DIR)),
    }


def main() -> None:
    result = apply_slack_updates()
    print(f"slack mock events processed: {result['event_count']}")
    print(f"action_items updated: {result['updated_count']}")
    print(f"events skipped: {result['skipped_count']}")
    print(f"slack update result saved: {result['result_path']}")


if __name__ == "__main__":
    main()
