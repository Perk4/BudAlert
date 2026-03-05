#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_BROWSERS_PATH="${SCRIPT_DIR}/.playwright-browsers"
PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$DEFAULT_BROWSERS_PATH}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DEFAULT_VENV_DIR="${SCRIPT_DIR}/.venv"
VENV_DIR="${VENV_DIR:-$DEFAULT_VENV_DIR}"
BROWSER="${BROWSER:-chromium}"
MODE="check"
WITH_DEPS=0

usage() {
  cat <<'EOF'
Usage:
  ./bootstrap_playwright.sh [--check] [--install] [--browser chromium|firefox|webkit] [--with-deps]

Behavior:
  --check    Validate python playwright import + browser binary in PLAYWRIGHT_BROWSERS_PATH (default)
  --install  Install missing python package/browser into PLAYWRIGHT_BROWSERS_PATH, then validate
  --with-deps
             Also run `python -m playwright install-deps <browser>` (Linux only, may require sudo)

Environment:
  PYTHON_BIN Optional explicit python interpreter (defaults to python3 or ./inventory/.venv/bin/python if present)
  VENV_DIR   Virtualenv location used as install fallback (default: ./inventory/.venv)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      MODE="check"
      shift
      ;;
    --install)
      MODE="install"
      shift
      ;;
    --with-deps)
      WITH_DEPS=1
      shift
      ;;
    --browser)
      BROWSER="${2:-}"
      if [[ -z "$BROWSER" ]]; then
        echo "Missing value for --browser" >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ "${PYTHON_BIN}" == "python3" && -x "${VENV_DIR}/bin/python" ]]; then
  PYTHON_BIN="${VENV_DIR}/bin/python"
fi

export PLAYWRIGHT_BROWSERS_PATH
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

echo "Python binary: $PYTHON_BIN"
echo "Browser: $BROWSER"
echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"

check_playwright_import() {
  "$PYTHON_BIN" - <<'PY'
import importlib.util
import sys

has_playwright = importlib.util.find_spec("playwright") is not None
print(f"python_playwright_installed={'yes' if has_playwright else 'no'}")
raise SystemExit(0 if has_playwright else 1)
PY
}

check_browser_install() {
  "$PYTHON_BIN" - "$BROWSER" <<'PY'
from pathlib import Path
import sys

browser_name = sys.argv[1]

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:
    print(f"playwright_import_error={exc}")
    raise SystemExit(2)

with sync_playwright() as p:
    browser_type = getattr(p, browser_name, None)
    if browser_type is None:
        print(f"unsupported_browser={browser_name}")
        raise SystemExit(3)

    executable_path = Path(browser_type.executable_path)
    print(f"browser_executable={executable_path}")
    print(f"browser_installed={'yes' if executable_path.exists() else 'no'}")
    raise SystemExit(0 if executable_path.exists() else 1)
PY
}

ensure_venv_python() {
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    python3 -m venv "${VENV_DIR}"
  fi

  PYTHON_BIN="${VENV_DIR}/bin/python"
  "$PYTHON_BIN" -m pip install --upgrade pip
}

if [[ "$MODE" == "install" ]]; then
  if ! check_playwright_import; then
    if ! "$PYTHON_BIN" -m pip install playwright; then
      echo "Primary pip install failed; falling back to virtualenv at ${VENV_DIR}"
      ensure_venv_python
      "$PYTHON_BIN" -m pip install playwright
    fi
  fi

  if [[ "$WITH_DEPS" -eq 1 ]]; then
    "$PYTHON_BIN" -m playwright install-deps "$BROWSER"
  fi

  "$PYTHON_BIN" -m playwright install "$BROWSER"
fi

check_playwright_import
check_browser_install

echo "Playwright environment check passed."
