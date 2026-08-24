#!/usr/bin/env bash
# Dumps the StudentHelp database to a timestamped, gzip-compressed file.
#
# Usage:
#   ./scripts/backup_db.sh                    # dumps DATABASE_URL from .env
#   DATABASE_URL=... ./scripts/backup_db.sh    # or pass it explicitly
#
# Run this on a schedule (cron, a GitHub Actions scheduled workflow, or your
# host's job scheduler) - it does nothing on its own otherwise. Example cron
# for a nightly backup at 2am:
#   0 2 * * * cd /path/to/backend && ./scripts/backup_db.sh >> /var/log/studenthelp-backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set (checked .env and environment). Aborting." >&2
  exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_FILE="$BACKUP_DIR/studenthelp_${TIMESTAMP}.sql.gz"

echo "Dumping database to $OUT_FILE ..."
pg_dump "$DATABASE_URL" | gzip > "$OUT_FILE"
echo "Done: $(du -h "$OUT_FILE" | cut -f1)"

# Keep the last 14 backups locally, delete older ones. Adjust to taste, or
# remove entirely if you're relying on S3/R2 lifecycle rules instead.
KEEP=14
ls -1t "$BACKUP_DIR"/studenthelp_*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm --
echo "Retention: keeping the most recent $KEEP backups in $BACKUP_DIR"

# Optional: also push to the same S3/R2 bucket used for resumes, under a
# separate prefix. Only runs if AWS CLI + credentials are available - safe
# to skip entirely for local/dev use.
if [ -n "${S3_BUCKET_NAME:-}" ] && command -v aws >/dev/null 2>&1; then
  echo "Uploading to s3://$S3_BUCKET_NAME/db-backups/$(basename "$OUT_FILE") ..."
  aws s3 cp "$OUT_FILE" "s3://$S3_BUCKET_NAME/db-backups/$(basename "$OUT_FILE")" \
    ${S3_ENDPOINT_URL:+--endpoint-url "$S3_ENDPOINT_URL"}
fi
