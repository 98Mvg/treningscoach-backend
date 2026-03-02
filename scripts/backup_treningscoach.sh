#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:-$(pwd)}"
BACKUP_ROOT="${2:-/Volumes/SSD}"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source directory not found: $SOURCE_DIR" >&2
  exit 1
fi

if [[ ! -d "$BACKUP_ROOT" ]]; then
  echo "Backup destination not found: $BACKUP_ROOT" >&2
  exit 1
fi

DATE_STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
PROJECT_NAME="$(basename "$SOURCE_DIR")"
TARGET_DIR="$BACKUP_ROOT/${PROJECT_NAME}_backups"
ARCHIVE_PATH="$TARGET_DIR/${PROJECT_NAME}_backup_${DATE_STAMP}.tar.gz"

mkdir -p "$TARGET_DIR"

tar \
  --exclude=".pytest_cache" \
  --exclude="__pycache__" \
  --exclude="build" \
  --exclude="output" \
  --exclude="uploads" \
  --exclude="instance" \
  -czf "$ARCHIVE_PATH" \
  -C "$(dirname "$SOURCE_DIR")" \
  "$PROJECT_NAME"

echo "Backup created: $ARCHIVE_PATH"
