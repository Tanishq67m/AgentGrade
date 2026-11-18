#!/usr/bin/env bash
# Check out ONE commit of the MCP servers repo (or a fork) into .targets/<name>/ and build the
# filesystem server there, so a suite variant can run that exact code (variant `server:`).
#
#   bash scripts/build_server_target.sh <repo-url> <commit> <name>
#
# After it finishes:
#   filesystem: node .targets/<name>/src/filesystem/dist/index.js <dir>
#   git:        uvx --from .targets/<name>/src/git mcp-server-git --repository <dir>  (no build step)
# .targets/ is git-ignored. Re-running with the same name re-uses the clone.
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <repo-url> <commit> <name>" >&2
  exit 2
fi
repo_url=$1
commit=$2
name=$3
root=$(cd "$(dirname "$0")/.." && pwd)
dest="$root/.targets/$name"

if [ ! -d "$dest/.git" ]; then
  git clone --quiet --filter=blob:none --no-checkout "$repo_url" "$dest"
fi
git -C "$dest" fetch --quiet origin "$commit" || true
git -C "$dest" checkout --quiet --detach "$commit"
echo "Checked out $(git -C "$dest" log -1 --format='%h %s') in $dest"

cd "$dest"
npm ci -w @modelcontextprotocol/server-filesystem --ignore-scripts --no-audit --no-fund
npm run build -w @modelcontextprotocol/server-filesystem
echo
echo "Built: $dest/src/filesystem/dist/index.js"
