from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "transcript.json"
DB_PATH = BASE_DIR / "data" / "warehouse.duckdb"

