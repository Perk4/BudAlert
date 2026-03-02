#!/bin/bash
# Auto-sync workspace to git

cd /root/clawd || exit 1

# Check if there are any changes
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to sync"
    exit 0
fi

# Stage all changes
git add -A

# Commit with timestamp
timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
git commit -m "Auto-sync: $timestamp"

# Push to remote
git push

echo "Workspace synced: $timestamp"
