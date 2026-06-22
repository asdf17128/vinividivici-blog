#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOG_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SITE_DIR="${BLOG_ROOT}/site"

REMOTE="${BLOG_REMOTE:-root@192.129.183.208}"
REMOTE_DIR="${BLOG_REMOTE_DIR:-/var/www/blog/}"

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required" >&2
  exit 1
fi

rsync -az --delete \
  --exclude ".DS_Store" \
  "${SITE_DIR}/" \
  "${REMOTE}:${REMOTE_DIR}"

echo "Published ${SITE_DIR} to ${REMOTE}:${REMOTE_DIR}"
