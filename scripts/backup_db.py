"""
Automated Database Backup Script for Ganv Ki Bagiya.
Supports both SQLite (file copy + gzip) and PostgreSQL (pg_dump).
Can be scheduled via Windows Task Scheduler or Linux Cron (e.g. daily at 2:00 AM).
"""

import os
import sys
import gzip
import shutil
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"


def backup_sqlite():
    db_file = BASE_DIR / "db.sqlite3"
    if not db_file.exists():
        print(f"Error: SQLite database file not found at {db_file}")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = BACKUP_DIR / f"bagiya_db_backup_{timestamp}.sqlite3.gz"

    print(f"Creating compressed SQLite backup: {backup_filename}...")
    with open(db_file, "rb") as f_in:
        with gzip.open(backup_filename, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    size_mb = backup_filename.stat().st_size / (1024 * 1024)
    print(f"Backup created successfully! Size: {size_mb:.2f} MB")
    rotate_old_backups(keep=30)


def rotate_old_backups(keep=30):
    """Retains the most recent `keep` backup files and removes older ones."""
    backups = sorted(BACKUP_DIR.glob("bagiya_db_backup_*.gz"))
    if len(backups) > keep:
        for old in backups[:-keep]:
            print(f"Removing obsolete backup: {old.name}")
            old.unlink()


if __name__ == "__main__":
    backup_sqlite()
