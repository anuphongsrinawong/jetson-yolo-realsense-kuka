#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/god/jetson-yolo-realsense-kuka"
BRANCH="main"

cd "$REPO_DIR"

if ! command -v inotifywait >/dev/null 2>&1; then
  echo "inotifywait not found. Please install inotify-tools." >&2
  exit 1
fi

# Ensure repo is initialized
if [ ! -d .git ]; then
  git init
fi

# Ensure branch exists
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
if [ -z "$current_branch" ] || [ "$current_branch" = "HEAD" ]; then
  git checkout -B "$BRANCH"
else
  BRANCH="$current_branch"
fi

echo "[auto-push] Watching $REPO_DIR on branch $BRANCH"

# Watch for changes and auto-commit/push
inotifywait -m -r -e close_write,create,delete,move \
  --exclude '(^|/)\.git(/|$)|(^|/)\.venv(/|$)|(^|/)models(/|$)|(^|/)__pycache__(/|$)|run\.log$' \
  "$REPO_DIR" | while read -r _; do
    # debounce
    sleep 1
    # Stage and commit if there are changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
      git add -A
      msg="auto: $(date -Iseconds) $(hostname)"
      git commit -m "$msg" || true
      # Push if remote is configured
      if git remote get-url origin >/dev/null 2>&1; then
        git push -u origin "$BRANCH" --no-verify || true
      else
        echo "[auto-push] No 'origin' remote configured; skipping push"
      fi
    fi
  done


