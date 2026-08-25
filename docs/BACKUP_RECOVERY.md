# StudentHelp — Database & Backup Recovery Guide

## 1. Overview
This document details database backup, restore, and object storage recovery procedures for the StudentHelp platform.

---

## 2. PostgreSQL Database Backup

### Automated Daily Dump
Use `pg_dump` to create daily compressed backup archives of the PostgreSQL database:

```bash
#!/usr/bin/env bash
# File: scripts/backup_db.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/studenthelp"
mkdir -p "$BACKUP_DIR"

pg_dump -h "${POSTGRES_SERVER:-localhost}" \
        -U "${POSTGRES_USER:-studenthelp}" \
        -d "${POSTGRES_DB:-studenthelp}" \
        -F c \
        -b \
        -v \
        -f "$BACKUP_DIR/studenthelp_$TIMESTAMP.dump"

# Retain backups for 30 days
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +30 -delete
```

### PostgreSQL Database Restore Procedure
To restore the PostgreSQL database from a `.dump` file:

```bash
# 1. Terminate active connections
psql -U studenthelp -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'studenthelp';"

# 2. Re-create clean database
psql -U studenthelp -d postgres -c "DROP DATABASE IF EXISTS studenthelp;"
psql -U studenthelp -d postgres -c "CREATE DATABASE studenthelp OWNER studenthelp;"

# 3. Restore schema & data
pg_restore -h localhost -U studenthelp -d studenthelp -v "$BACKUP_DIR/studenthelp_20260825_000000.dump"

# 4. Run Alembic migrations to ensure schema is up to date
cd backend
alembic upgrade head
```

---

## 3. Resume & File Storage Backup
- **Production (Object Storage / S3 / R2)**: Enable S3 Versioning and Cross-Region Replication (CRR) on the bucket storing student resumes (`resumes/`).
- **Development / On-Premise**: Backup the `local_uploads/` directory on a daily schedule using `rsync` or tar archives.

```bash
# Local uploads backup
tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" -C backend local_uploads/
```

---

## 4. Disaster Recovery Checklist
1. Verify latest `.dump` file size and integrity (`pg_restore --list <file>`).
2. Restore to isolated staging instance.
3. Validate DB tables count & Alembic migration revision (`alembic current`).
4. Execute `python -m pytest` test suite on staging instance.
