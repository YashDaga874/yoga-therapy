import sqlite3
from pathlib import Path


def get_table_schema(db_path: Path, table: str):
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        rows = cur.fetchall()
    finally:
        conn.close()
    return rows


def main():
    base = Path(__file__).resolve().parent
    for name in ["yoga_therapy.db", "yoga_therapy_old.db"]:
        db_file = base / name
        print("=" * 60)
        print(f"Schema for {name}")
        print("=" * 60)
        if not db_file.exists():
            print(f"(missing file: {db_file})")
            continue
        for table in ["contraindications", "practices"]:
            print(f"\nTable: {table}")
            try:
                rows = get_table_schema(db_file, table)
            except sqlite3.OperationalError as exc:
                print(f"  ERROR: {exc}")
                continue
            for cid, col_name, col_type, notnull, dflt_value, pk in rows:
                print(
                    f"  {cid}: {col_name} {col_type} NOT NULL={bool(notnull)} "
                    f"DEFAULT={dflt_value!r} PK={bool(pk)}"
                )
        print()


if __name__ == "__main__":
    main()

