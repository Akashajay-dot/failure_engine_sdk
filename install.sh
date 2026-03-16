#!/usr/bin/env bash
set -e
REPO_ROOT=$(git rev-parse --show-toplevel)
SDK_DIR="$REPO_ROOT/.failure-memory"

API_KEY=""
if [[ "$1" == "--api-key" ]]; then
  API_KEY="$2"
fi

if [[ -n "$API_KEY" ]]; then
  perl -0777 -i -pe "s/key: \"\"/key: \"$API_KEY\"/" "$SDK_DIR/config/config.yml"
fi

mkdir -p "$REPO_ROOT/.git/hooks"
cp "$SDK_DIR/hooks/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit"
cp "$SDK_DIR/hooks/prepare-commit-msg" "$REPO_ROOT/.git/hooks/prepare-commit-msg"
cp "$SDK_DIR/hooks/commit-msg" "$REPO_ROOT/.git/hooks/commit-msg"
cp "$SDK_DIR/hooks/pre-push" "$REPO_ROOT/.git/hooks/pre-push"
chmod +x "$REPO_ROOT/.git/hooks/pre-commit" "$REPO_ROOT/.git/hooks/prepare-commit-msg" "$REPO_ROOT/.git/hooks/commit-msg" "$REPO_ROOT/.git/hooks/pre-push"

echo "Failure Memory SDK installed."
