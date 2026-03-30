#!/bin/bash
cd "$(dirname "$0")/.."
git add -A
if ! git diff --cached --quiet; then
  git commit -m "auto: update $(date +%Y-%m-%d_%H:%M:%S)"
  git push origin main
fi
