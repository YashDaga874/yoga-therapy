import sqlite3
from pathlib import Path


DB_NAME = "yoga_therapy.db"
TABLE = "rcts"


EXPECTED_COLUMNS = {
    # existing RCT columns we care about
    "id",
    "doi",
    "review_doi",
}


def get_existing_columns(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({TABLE})")
        rows = cur.fetchall()
        return [r[1] for r in rows]  # column names
    finally:
        conn.close()


def add_column(conn, name: str, col_type: str):
    cur = conn.cursor()
    cur.execute(f"ALTER TABLE {TABLE} ADD COLUMN {name} {col_type}")
    conn.commit()


def main():
    base = Path(__file__).resolve().parent.parent  # project root
    db_path = base / DB_NAME

    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        return

    existing = set(get_existing_columns(db_path))
    missing = EXPECTED_COLUMNS - existing

    print(f"Existing columns in {TABLE}: {sorted(existing)}")
    print(f"Missing expected columns: {sorted(missing)}")

    if not missing:
        print("No changes needed.")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        if "review_doi" in missing:
            print("Adding column 'review_doi' (VARCHAR(500))...")
            add_column(conn, "review_doi", "VARCHAR(500)")

        print("Migration completed successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
