#!/usr/bin/env bash
set -euo pipefail

MODE="copy"
DRY_RUN=0
REPLACE=0

usage() {
  cat <<'EOF'
Usage: scripts/install-hermes-skills.sh [--mode copy|symlink] [--dry-run] [--replace]

Environment:
  HERMES_HOME      Defaults to ~/.hermes
  HERMES_PROFILE   Defaults to default. For default, installs into ~/.hermes/skills.
                   For named profiles, installs into ~/.hermes/profiles/<name>/skills.

By default the installer is non-destructive and refuses to overwrite an existing skill.
Pass --replace only after reviewing the target directory.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --replace)
      REPLACE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$MODE" != "copy" && "$MODE" != "symlink" ]]; then
  echo "--mode must be copy or symlink" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_PROFILE="${HERMES_PROFILE:-default}"

if [[ "$HERMES_PROFILE" == "default" ]]; then
  DEST="$HERMES_HOME/skills"
else
  DEST="$HERMES_HOME/profiles/$HERMES_PROFILE/skills"
fi

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '[dry-run] '
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

echo "source repo: $ROOT"
echo "target skills dir: $DEST"
echo "mode: $MODE"

run mkdir -p "$DEST"

for skill in claude-desktop-babysitting agent-session-progress; do
  src="$ROOT/skills/$skill"
  dst="$DEST/$skill"
  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "missing skill: $src/SKILL.md" >&2
    exit 1
  fi
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ "$REPLACE" != "1" ]]; then
      echo "target already exists: $dst" >&2
      echo "rerun with --replace to overwrite it, or use --dry-run to inspect first" >&2
      exit 1
    fi
    run rm -rf "$dst"
  fi
  if [[ "$MODE" == "symlink" ]]; then
    run ln -s "$src" "$dst"
  else
    run cp -R "$src" "$dst"
  fi
  echo "installed: $skill -> $dst"
done

echo
echo "Installed Claude Desktop Supervisor skills into: $DEST"
echo
echo "Validate the progress helper:"
echo "  python3 \"$DEST/agent-session-progress/scripts/agent_progress.py\" --help"
echo
echo "Then start a fresh Hermes session and ask it to load/use:"
echo "  claude-desktop-babysitting"
echo "  agent-session-progress"
