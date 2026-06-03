import duckdb

from src.config import DB_PATH


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                meeting_id VARCHAR PRIMARY KEY,
                advertiser VARCHAR,
                campaign VARCHAR,
                meeting_date DATE,
                source_type VARCHAR,
                created_at TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS utterances (
                utterance_id VARCHAR PRIMARY KEY,
                meeting_id VARCHAR,
                speaker VARCHAR,
                role VARCHAR,
                start_time DOUBLE,
                end_time DOUBLE,
                text TEXT,
                normalized_text TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id VARCHAR PRIMARY KEY,
                meeting_id VARCHAR,
                chunk_order INTEGER,
                speaker_context TEXT,
                chunk_text TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS action_items (
                action_item_id VARCHAR PRIMARY KEY,
                meeting_id VARCHAR,
                chunk_id VARCHAR,
                owner VARCHAR,
                task TEXT,
                due_date VARCHAR,
                priority VARCHAR,
                status VARCHAR,
                confidence DOUBLE,
                source_utterance TEXT,
                reasoning TEXT,
                created_at TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS action_item_status_events (
                event_id VARCHAR PRIMARY KEY,
                action_item_id VARCHAR,
                meeting_id VARCHAR,
                previous_status VARCHAR,
                new_status VARCHAR,
                actor VARCHAR,
                note TEXT,
                event_ts TIMESTAMP,
                created_at TIMESTAMP
            );
            """
        )
