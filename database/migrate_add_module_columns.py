import sqlite3
from pathlib import Path


DB_NAME = "yoga_therapy.db"
TABLE = "modules"


EXPECTED_COLUMNS = {
    "id",
    "disease_id",
    "code",
    "developed_by",
    "paper_link",
    "age_range",
    "gender",
    "severity",
    "module_description",
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
    base = Path(__file__).resolve().parent.parent  # project root (yoga-therapy)
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
        if "age_range" in missing:
            print("Adding column 'age_range' (VARCHAR(200))...")
            add_column(conn, "age_range", "VARCHAR(200)")
        if "gender" in missing:
            print("Adding column 'gender' (VARCHAR(50))...")
            add_column(conn, "gender", "VARCHAR(50)")
        if "severity" in missing:
            print("Adding column 'severity' (VARCHAR(50))...")
            add_column(conn, "severity", "VARCHAR(50)")

        print("Migration completed successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

