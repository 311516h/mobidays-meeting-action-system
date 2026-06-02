from src.chunking import chunk_transcript
from src.ingest import ingest_transcript
from src.llm_client import export_action_item_outputs, extract_and_store_action_items
from src.storage import init_db


def main() -> None:
    init_db()
    print("database initialized")
    result = ingest_transcript()
    print(f"meeting ingested: {result['meeting_id']}")
    print(f"utterances inserted: {result['utterance_count']}")
    chunk_result = chunk_transcript(meeting_id=result["meeting_id"])
    print(f"chunks inserted: {chunk_result['chunk_count']}")
    extraction_result = extract_and_store_action_items()
    print(f"action_items inserted: {extraction_result['action_item_count']}")
    export_result = export_action_item_outputs()
    print(f"action_items output saved: {export_result['action_items_path']}")
    print(f"slack payload saved: {export_result['slack_payload_path']}")


if __name__ == "__main__":
    main()
