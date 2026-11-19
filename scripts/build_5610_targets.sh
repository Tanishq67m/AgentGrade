#!/usr/bin/env bash
# Builds for the #5610 experiment (ADR 0018): current v2/main of mcp-server-git, plus three
# patched copies, one per option in the issue. Run from the AgentGrade folder:
#   bash scripts/build_5610_targets.sh
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
main_sha=640a8c31779b6b1d28b497437a0e1b47347d8e4a

bash "$root/scripts/build_server_target.sh" https://github.com/modelcontextprotocol/servers.git "$main_sha" v2main-640a8c3

for mode in optional described instructions; do
  dest="$root/.targets/repo5610-$mode/src"
  rm -rf "$root/.targets/repo5610-$mode"
  mkdir -p "$dest"
  cp -R "$root/.targets/v2main-640a8c3/src/git" "$dest/git"
  rm -rf "$dest/git/.venv"
  python3 "$root/scripts/patch_git_repo_path.py" "$dest/git/src/mcp_server_git/server.py" "$mode"
done
echo
echo "Ready: .targets/v2main-640a8c3 and .targets/repo5610-{optional,described,instructions}"
