# Ganv Ki Bagiya — Database Backup & Restoration Guide

## 1. Overview
The **Ganv Ki Bagiya** platform handles community funds and legal receipts. Continuous database backup is paramount. This document details backup, verification, and disaster-recovery procedures.

---

## 2. Automated SQLite Backup

### Running the Backup Script
Execute the provided Python backup script at any time:
```bash
python scripts/backup_db.py
```
This performs:
1. Creation of a timestamped, gzip-compressed snapshot inside `backups/`:
   `backups/bagiya_db_backup_YYYYMMDD_HHMMSS.sqlite3.gz`
2. Automatic retention pruning (retains the latest 30 daily backups).

### Scheduling via Windows Task Scheduler
1. Open **Task Scheduler** $\rightarrow$ **Create Basic Task**.
2. Name: `GanvKiBagiya_DailyBackup`.
3. Trigger: **Daily at 02:00 AM**.
4. Action: **Start a program**:
   - Program: `python.exe` (or full path to your virtualenv's `python.exe`)
   - Arguments: `scripts\backup_db.py`
   - Start in: `C:\path\to\Bagiya`

### Scheduling via Linux Cron
```bash
0 2 * * * cd /var/www/bagiya && /var/www/bagiya/venv/bin/python scripts/backup_db.py >> /var/log/bagiya_backup.log 2>&1
```

---

## 3. SQLite Restoration Procedure

To restore the database from a compressed backup:

1. **Stop the application service**:
   ```bash
   # On Linux/Gunicorn
   sudo systemctl stop bagiya
   ```
2. **Preserve existing database (safeguard)**:
   ```bash
   mv db.sqlite3 db.sqlite3.broken_backup
   ```
3. **Decompress target backup**:
   ```bash
   # Using Python:
   python -c "import gzip, shutil; shutil.copyfileobj(gzip.open('backups/bagiya_db_backup_TARGET.sqlite3.gz', 'rb'), open('db.sqlite3', 'wb'))"
   ```
4. **Verify integrity**:
   ```bash
   python manage.py showmigrations
   python manage.py check
   ```
5. **Restart application**:
   ```bash
   sudo systemctl start bagiya
   ```

---

## 4. PostgreSQL Production Backup & Restore

If running on PostgreSQL:

### Backup (Daily Dump):
```bash
pg_dump -U bagiya_user -h localhost -d bagiya_db -F c -b -v -f "/var/backups/bagiya/bagiya_$(date +\%Y\%m\%d).dump"
```

### Restore:
```bash
# Drop current connections and recreate
dropdb -U bagiya_user -h localhost bagiya_db
createdb -U bagiya_user -h localhost bagiya_db
pg_restore -U bagiya_user -h localhost -d bagiya_db -v "/var/backups/bagiya/bagiya_TARGET.dump"
```

---

## 5. Media & Uploads Backup

Remember that uploaded bills, receipts, and project photos are located in the `media/` directory:
```bash
tar -czvf backups/media_backup_$(date +\%Y\%m\%d).tar.gz media/
```
Ensure the `media/` directory is synchronized with offsite cold storage (such as AWS S3 or Google Drive) weekly.
