#!/usr/bin/env bash
# =============================================================================
# File    : publish_guard.sh
# Author  : Marcus Daley
# Date    : 2026-04-29
# Purpose : Bash twin of publish_guard.ps1. Scans the ClaudeSkills repo for
#           personal markers, project codenames, and disallowed remotes
#           before any publish/push/archive operation.
#
# Modes:
#   install : soft check (warn + log, exit 0 unless catastrophic)
#   publish : hard check (exit 1 on any redline outside excluded_paths)
#   audit   : informational scan grouped by severity
#
# Exit codes:
#   0  - pass / soft-warn
#   1  - hard block (publish-mode redline)
#   2  - guard itself failed (config missing, parse error)
#
# Usage:
#   ./scripts/publish_guard.sh --mode publish
#   ./scripts/publish_guard.sh --mode install --config /custom/path.json
# =============================================================================

# WHY: -e bails on the first uncaught failure so we never silently approve a
# push. -u catches typos in variable names. -o pipefail propagates errors out
# of pipelines (e.g. grep | head).
set -euo pipefail

# -----------------------------------------------------------------------------
# Argument parsing - keep it dependency-free so this runs on a fresh git-bash
# install or a minimal Linux container without getopt.
# -----------------------------------------------------------------------------
MODE="audit"
CONFIG_PATH=""
REPO_ROOT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="${2:-audit}"
            shift 2
            ;;
        --config)
            CONFIG_PATH="${2:-}"
            shift 2
            ;;
        --repo-root)
            REPO_ROOT="${2:-}"
            shift 2
            ;;
        -h|--help)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *)
            echo "publish_guard: unknown argument '$1'" >&2
            exit 2
            ;;
    esac
done

case "$MODE" in
    install|publish|audit) ;;
    *)
        echo "publish_guard: --mode must be install|publish|audit (got '$MODE')" >&2
        exit 2
        ;;
esac

# -----------------------------------------------------------------------------
# Path resolution - never hardcode C:/ClaudeSkills. Discover from script dir.
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -z "$REPO_ROOT"   ]] && REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
[[ -z "$CONFIG_PATH" ]] && CONFIG_PATH="$REPO_ROOT/config/publish_guard.json"

if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "publish_guard: config not found at $CONFIG_PATH" >&2
    exit 2
fi

# -----------------------------------------------------------------------------
# JSON parsing. Prefer jq when available; otherwise use a portable python3
# fallback. We refuse to ship a regex JSON parser - that path is how guards
# silently miss new fields and let leaks through.
# -----------------------------------------------------------------------------
have_jq() { command -v jq   >/dev/null 2>&1; }
have_py() { command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; }

PY_BIN=""
if   command -v python3 >/dev/null 2>&1; then PY_BIN="python3"
elif command -v python  >/dev/null 2>&1; then PY_BIN="python"
fi

if ! have_jq && [[ -z "$PY_BIN" ]]; then
    echo "publish_guard: requires either jq or python on PATH" >&2
    exit 2
fi

# get_array <key> -> emits one element per line on stdout
get_array() {
    local key="$1"
    if have_jq; then
        jq -r --arg k "$key" '.[$k][]?' "$CONFIG_PATH"
    else
        "$PY_BIN" - "$CONFIG_PATH" "$key" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1], "r", encoding="utf-8"))
for item in cfg.get(sys.argv[2], []) or []:
    print(item)
PYEOF
    fi
}

# get_scalar <dotted.path> -> emits a single string on stdout
get_scalar() {
    local key="$1"
    if have_jq; then
        jq -r --arg k "$key" '.[$k] // empty' "$CONFIG_PATH"
    else
        "$PY_BIN" - "$CONFIG_PATH" "$key" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1], "r", encoding="utf-8"))
val = cfg.get(sys.argv[2], "")
if val is None:
    val = ""
print(val)
PYEOF
    fi
}

get_block_exit_code() {
    if have_jq; then
        jq -r '.severity_levels.block.exit_code // 1' "$CONFIG_PATH"
    else
        "$PY_BIN" - "$CONFIG_PATH" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1], "r", encoding="utf-8"))
print(cfg.get("severity_levels", {}).get("block", {}).get("exit_code", 1))
PYEOF
    fi
}

# -----------------------------------------------------------------------------
# Load config slices. We materialize into bash arrays once so the scan loop
# stays tight and predictable.
# -----------------------------------------------------------------------------
mapfile -t PERSONAL_MARKERS    < <(get_array personal_markers)
mapfile -t PROJECT_CODENAMES   < <(get_array project_codenames)
mapfile -t BLOCKED_DESTINATIONS < <(get_array blocked_destinations)
mapfile -t ALLOWED_DESTINATIONS < <(get_array allowed_destinations)
mapfile -t EXCLUDED_PATHS      < <(get_array excluded_paths)
mapfile -t BINARY_EXTENSIONS   < <(get_array binary_extensions)

LOG_REL_PATH="$(get_scalar log_path)"
[[ -z "$LOG_REL_PATH" ]] && LOG_REL_PATH="logs/publish_guard.log"

MAX_BYTES_RAW="$(get_scalar max_file_size_bytes)"
MAX_BYTES="${MAX_BYTES_RAW:-2097152}"

BLOCK_EXIT_CODE="$(get_block_exit_code)"
[[ -z "$BLOCK_EXIT_CODE" ]] && BLOCK_EXIT_CODE=1

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# WHY: matches the PowerShell logic exactly. Trailing slash means prefix match,
# anything else is full-path or basename match.
is_excluded() {
    local rel="$1"
    rel="${rel#./}"
    rel="${rel//\\//}"

    local needle
    for needle in "${EXCLUDED_PATHS[@]}"; do
        needle="${needle//\\//}"
        needle="${needle#./}"

        if [[ "$needle" == */ ]]; then
            [[ "$rel" == "$needle"* ]] && return 0
        else
            [[ "$rel" == "$needle"   ]] && return 0
            [[ "$rel" == */"$needle" ]] && return 0
        fi
    done
    return 1
}

is_binary_ext() {
    local path="$1"
    local lower="${path,,}"
    local ext
    for ext in "${BINARY_EXTENSIONS[@]}"; do
        [[ "$lower" == *"$ext" ]] && return 0
    done
    return 1
}

write_log() {
    local mode="$1" verdict="$2" matches="$3" notes="$4"
    local log_dir log_file stamp line
    log_file="$REPO_ROOT/$LOG_REL_PATH"
    log_dir="$(dirname "$log_file")"
    mkdir -p "$log_dir"
    stamp="$(date +%Y-%m-%dT%H:%M:%S%z)"
    line="[$stamp] mode=$mode verdict=$verdict matches=$matches notes=$notes"
    printf '%s\n' "$line" >> "$log_file"
}

current_remote() {
    # WHY: graceful-fallback. Missing remote returns empty so the caller
    # can mark it "unknown" instead of crashing the guard.
    ( cd "$REPO_ROOT" && git remote get-url origin 2>/dev/null ) || true
}

remote_decision() {
    local remote="$1"
    if [[ -z "$remote" ]]; then
        echo "unknown|No git remote detected."
        return
    fi

    local pat
    for pat in "${BLOCKED_DESTINATIONS[@]}"; do
        if echo "$remote" | grep -Eq "$pat"; then
            echo "blocked|Remote matches blocked pattern: $pat"
            return
        fi
    done
    for pat in "${ALLOWED_DESTINATIONS[@]}"; do
        if echo "$remote" | grep -Eq "$pat"; then
            echo "allowed|Remote matches allowed pattern: $pat"
            return
        fi
    done
    echo "unknown|Remote $remote did not match allow or block list."
}

# -----------------------------------------------------------------------------
# Scan. Buffer hits to a temp file so we can both print the report and count
# total findings without re-walking the tree.
# -----------------------------------------------------------------------------

HITS_FILE="$(mktemp -t publish_guard.XXXXXX)"
# WHY: cleanup on every exit path keeps /tmp tidy and prevents stale hit
# files from being interpreted by a later run.
trap 'rm -f "$HITS_FILE"' EXIT

scan_repo() {
    local file rel size pattern category escaped
    while IFS= read -r -d '' file; do
        rel="${file#"$REPO_ROOT"/}"

        is_excluded "$rel"     && continue
        is_binary_ext "$file"  && continue

        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo 0)
        if [[ "$size" -gt "$MAX_BYTES" ]]; then continue; fi

        # Personal markers - patterns are full regex, used as-is.
        for pattern in "${PERSONAL_MARKERS[@]}"; do
            [[ -z "$pattern" ]] && continue
            grep -nE "$pattern" "$file" 2>/dev/null | while IFS=: read -r lineno match; do
                printf 'PERSONAL\t%s\t%s\t%s\t%s\n' "$rel" "$lineno" "$pattern" "$match" >> "$HITS_FILE"
            done || true
        done

        # Codenames - literal strings, treat as fixed but apply word boundary
        # via grep -w for accuracy ("Bob" should not match "Bobcat").
        for pattern in "${PROJECT_CODENAMES[@]}"; do
            [[ -z "$pattern" ]] && continue
            grep -nwiF "$pattern" "$file" 2>/dev/null | while IFS=: read -r lineno match; do
                printf 'CODENAME\t%s\t%s\t%s\t%s\n' "$rel" "$lineno" "$pattern" "$match" >> "$HITS_FILE"
            done || true
        done
    done < <(find "$REPO_ROOT" -type f -print0)
}

scan_repo

TOTAL_HITS=$(wc -l < "$HITS_FILE" | tr -d ' ')
TOTAL_HITS=${TOTAL_HITS:-0}

# -----------------------------------------------------------------------------
# Report
# -----------------------------------------------------------------------------
echo ""
echo "======================================================"
echo "  PUBLISH GUARD - mode: $MODE"
echo "======================================================"

REMOTE_DECISION=""
REMOTE_REASON=""
if [[ "$MODE" == "publish" ]]; then
    REMOTE_URL="$(current_remote)"
    DECISION_LINE="$(remote_decision "$REMOTE_URL")"
    REMOTE_DECISION="${DECISION_LINE%%|*}"
    REMOTE_REASON="${DECISION_LINE#*|}"
    echo "Remote check : $(echo "$REMOTE_DECISION" | tr '[:lower:]' '[:upper:]') - $REMOTE_REASON"
fi

PERSONAL_COUNT=$(grep -c '^PERSONAL'  "$HITS_FILE" 2>/dev/null || true)
CODENAME_COUNT=$(grep -c '^CODENAME'  "$HITS_FILE" 2>/dev/null || true)
PERSONAL_COUNT=${PERSONAL_COUNT:-0}
CODENAME_COUNT=${CODENAME_COUNT:-0}

echo ""
echo "Personal marker hits : $PERSONAL_COUNT"
echo "Project codename hits: $CODENAME_COUNT"
echo ""

if [[ "$TOTAL_HITS" -gt 0 ]]; then
    printf '%-9s  %-50s  %-6s  %s\n' "CATEGORY" "FILE" "LINE" "MATCH"
    printf '%-9s  %-50s  %-6s  %s\n' "---------" "----" "----" "-----"
    sort "$HITS_FILE" | while IFS=$'\t' read -r cat file line pat match; do
        printf '%-9s  %-50s  %-6s  %s\n' "$cat" "$file" "$line" "$match"
    done
    echo ""
else
    echo "No redline matches found outside excluded paths."
fi

# -----------------------------------------------------------------------------
# Verdict
# -----------------------------------------------------------------------------
VERDICT="PASS"
EXIT_CODE=0
NOTES=""

case "$MODE" in
    install)
        if [[ "$TOTAL_HITS" -gt 0 ]]; then
            VERDICT="WARN"
            NOTES="install-mode soft warn"
            echo "Install-mode soft check: continuing despite $TOTAL_HITS findings."
        fi
        EXIT_CODE=0
        ;;

    audit)
        if [[ "$TOTAL_HITS" -gt 0 ]]; then VERDICT="WARN"; fi
        EXIT_CODE=0
        ;;

    publish)
        if [[ "$REMOTE_DECISION" == "blocked" ]]; then
            VERDICT="BLOCK"; NOTES="${NOTES}remote=blocked "
            EXIT_CODE="$BLOCK_EXIT_CODE"
        elif [[ "$REMOTE_DECISION" == "unknown" ]]; then
            VERDICT="BLOCK"; NOTES="${NOTES}remote=unknown "
            EXIT_CODE="$BLOCK_EXIT_CODE"
        fi

        if [[ "$TOTAL_HITS" -gt 0 ]]; then
            VERDICT="BLOCK"; NOTES="${NOTES}redlines=$TOTAL_HITS "
            EXIT_CODE="$BLOCK_EXIT_CODE"
        fi

        if [[ "$EXIT_CODE" -ne 0 ]]; then
            echo ""
            echo "PUBLISH BLOCKED. Resolve findings or move them under excluded_paths."
        else
            echo ""
            echo "PUBLISH OK. No redlines, remote is on the allow list."
        fi
        ;;
esac

write_log "$MODE" "$VERDICT" "$TOTAL_HITS" "$NOTES"
exit "$EXIT_CODE"
