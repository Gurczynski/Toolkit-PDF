#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-$(dirname "$0")/vps.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

: "${APP_DIR:?APP_DIR is required}"
: "${INPUT_DIR:?INPUT_DIR is required}"
: "${OUTPUT_DIR:?OUTPUT_DIR is required}"
: "${RULES_PATH:?RULES_PATH is required}"
: "${PYTHON_BIN:=python3}"
: "${VENV_DIR:=$APP_DIR/.venv}"
: "${LOG_DIR:=$APP_DIR/logs}"
: "${LOCK_FILE:=/tmp/pdf-html-toolkit.lock}"

mkdir -p "$APP_DIR" "$INPUT_DIR" "$OUTPUT_DIR" "$LOG_DIR"

run_workflow() {
  if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1090
  . "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip

  if [[ -n "${WHEEL_PATH:-}" && -f "${WHEEL_PATH}" ]]; then
    python -m pip install --upgrade "$WHEEL_PATH"
  else
    python -m pip install --upgrade "$APP_DIR"
  fi

  timestamp="$(date '+%Y-%m-%d_%H-%M-%S')"
  log_file="$LOG_DIR/run_$timestamp.log"

  {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting pdf-html-toolkit workflow"
    echo "APP_DIR=$APP_DIR"
    echo "INPUT_DIR=$INPUT_DIR"
    echo "OUTPUT_DIR=$OUTPUT_DIR"
    echo "RULES_PATH=$RULES_PATH"
    pdf-html-toolkit "$INPUT_DIR" --output-root "$OUTPUT_DIR" --rules "$RULES_PATH"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Workflow complete"
  } | tee "$log_file"

  cp "$log_file" "$LOG_DIR/latest.log"
}

if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK_FILE"
  flock -n 9 || { echo "Workflow already running" >&2; exit 1; }
  run_workflow
else
  run_workflow
fi
