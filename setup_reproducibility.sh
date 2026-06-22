#!/usr/bin/env bash
set -Eeuo pipefail

# Reproducibility setup for SegAud.
# It prepares Python dependencies for the benchmark, Node dependencies for the
# VS Code extension, and checks the local Ollama service used by both parts.
#
# Optional environment variables:
#   INSTALL_OLLAMA=1   Try to install Ollama if it is missing.
#   PULL_MODELS=1      Download all benchmark models with `ollama pull`.
#   RUN_BENCHMARK=1    Run benchmark/benchmark.py after setup.
#   PYTHON_BIN=python3 Override Python executable.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"
EXTENSION_DIR="$PROJECT_ROOT/extension"
VENV_DIR="$PROJECT_ROOT/.venv"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434/api/chat}"
OLLAMA_HEALTH_URL="${OLLAMA_HEALTH_URL:-${OLLAMA_URL%/api/chat}/api/tags}"

MODELS=(
  "granite4.1:3b"
  "gemma4:latest"
  "falcon3:latest"
  "deepseek-coder:latest"
  "yi-coder:latest"
  "stable-code:latest"
  "laguna-xs.2:latest"
  "exaone-deep:latest"
)

log() {
  printf '\n[setup] %s\n' "$*"
}

warn() {
  printf '\n[setup][warning] %s\n' "$*" >&2
}

fail() {
  printf '\n[setup][error] %s\n' "$*" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

detect_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    command_exists "$PYTHON_BIN" || fail "PYTHON_BIN='$PYTHON_BIN' was not found."
    printf '%s\n' "$PYTHON_BIN"
    return
  fi

  if command_exists python3; then
    printf '%s\n' "python3"
  elif command_exists python; then
    printf '%s\n' "python"
  else
    fail "Python 3.10+ is required but was not found."
  fi
}

check_python_version() {
  local python_bin="$1"

  "$python_bin" - <<'PY'
import sys

required = (3, 10)
current = sys.version_info[:2]

if current < required:
    raise SystemExit(
        f"Python {required[0]}.{required[1]}+ is required; found {current[0]}.{current[1]}"
    )
PY
}

activate_venv() {
  if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # Linux/macOS/Git Bash layout
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
  elif [[ -f "$VENV_DIR/Scripts/activate" ]]; then
    # Windows venv layout when running through Git Bash/MSYS.
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
  else
    fail "Virtual environment was created, but no activation script was found."
  fi
}

install_python_dependencies() {
  local python_bin="$1"

  log "Checking Python version"
  check_python_version "$python_bin"

  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating Python virtual environment at .venv"
    "$python_bin" -m venv "$VENV_DIR"
  else
    log "Reusing existing Python virtual environment at .venv"
  fi

  activate_venv

  log "Installing benchmark Python dependencies"
  python -m pip install --upgrade pip
  python -m pip install -r "$PROJECT_ROOT/requirements.txt"
}

install_extension_dependencies() {
  if ! command_exists npm; then
    warn "npm was not found; skipping extension dependency installation."
    warn "Install Node.js/npm to work on the VS Code extension in extension/."
    return
  fi

  log "Installing VS Code extension dependencies"
  cd "$EXTENSION_DIR"

  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi

  cd "$PROJECT_ROOT"
}

install_ollama() {
  if command_exists ollama; then
    log "Ollama CLI is already installed."
    return
  fi

  if [[ "${INSTALL_OLLAMA:-0}" != "1" ]]; then
    warn "Ollama CLI was not found."
    warn "Use INSTALL_OLLAMA=1 to let this script try to install it."
    return
  fi

  log "Trying to install Ollama"

  case "$(uname -s)" in
    Linux*)
      command_exists curl || fail "curl is required to install Ollama on Linux."
      curl -fsSL https://ollama.com/install.sh | sh
      ;;
    Darwin*)
      if command_exists brew; then
        brew install ollama
      else
        fail "Homebrew was not found. Install Ollama from https://ollama.com/download."
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*)
      if command_exists winget; then
        winget install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements
      elif command_exists powershell.exe; then
        powershell.exe -NoProfile -Command "winget install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements"
      else
        fail "Could not find winget. Install Ollama from https://ollama.com/download/windows."
      fi
      ;;
    *)
      fail "Unsupported OS for automatic Ollama installation. Install it from https://ollama.com/download."
      ;;
  esac

  if command_exists ollama; then
    log "Ollama CLI installed successfully."
  else
    warn "Ollama installation finished, but the CLI is not available in PATH yet."
    warn "Restart the terminal and rerun this script if needed."
  fi
}

start_ollama_if_possible() {
  command_exists ollama || return

  if command_exists curl && curl --silent --fail --max-time 5 "$OLLAMA_HEALTH_URL" >/dev/null; then
    return
  fi

  log "Trying to start Ollama service"

  case "$(uname -s)" in
    Linux*)
      if command_exists systemctl; then
        if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
          systemctl start ollama 2>/dev/null || warn "Could not start Ollama with systemctl."
        elif command_exists sudo && sudo -n true 2>/dev/null; then
          sudo systemctl start ollama 2>/dev/null || warn "Could not start Ollama with systemctl."
        else
          (ollama serve >/tmp/segaud-ollama.log 2>&1 &)
        fi
      else
        (ollama serve >/tmp/segaud-ollama.log 2>&1 &)
      fi
      ;;
    Darwin*)
      if command_exists brew; then
        brew services start ollama >/dev/null 2>&1 || (ollama serve >/tmp/segaud-ollama.log 2>&1 &)
      else
        (ollama serve >/tmp/segaud-ollama.log 2>&1 &)
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*)
      if command_exists powershell.exe; then
        powershell.exe -NoProfile -Command "Start-Process -FilePath ollama -ArgumentList 'serve' -WindowStyle Hidden" >/dev/null 2>&1 || true
      fi
      ;;
  esac

  sleep 3
}

check_ollama() {
  install_ollama

  if ! command_exists ollama; then
    warn "Install Ollama and start it before running the benchmark or extension analysis."
    return
  fi

  start_ollama_if_possible

  log "Checking Ollama local API at $OLLAMA_HEALTH_URL"

  if command_exists curl; then
    if curl --silent --fail --max-time 5 "$OLLAMA_HEALTH_URL" >/dev/null; then
      log "Ollama API is reachable."
    else
      warn "Ollama CLI exists, but the API did not respond at $OLLAMA_HEALTH_URL."
      warn "Start Ollama before running the benchmark."
    fi
  else
    warn "curl was not found; skipping Ollama HTTP health check."
  fi
}

pull_models() {
  if [[ "${PULL_MODELS:-0}" != "1" ]]; then
    log "Skipping model downloads. Use PULL_MODELS=1 to download benchmark models."
    return
  fi

  command_exists ollama || fail "PULL_MODELS=1 was set, but Ollama CLI was not found."

  log "Downloading benchmark models with Ollama"
  for model in "${MODELS[@]}"; do
    log "Pulling $model"
    if ! ollama pull "$model"; then
      warn "Could not pull $model. The benchmark will skip it if it is unavailable locally."
    fi
  done
}

run_benchmark() {
  if [[ "${RUN_BENCHMARK:-0}" != "1" ]]; then
    log "Skipping benchmark execution. Use RUN_BENCHMARK=1 to run it now."
    return
  fi

  log "Running benchmark"
  cd "$BENCHMARK_DIR"
  python benchmark.py
  cd "$PROJECT_ROOT"
}

main() {
  cd "$PROJECT_ROOT"

  [[ -d "$BENCHMARK_DIR" ]] || fail "benchmark/ directory not found."
  [[ -d "$EXTENSION_DIR" ]] || fail "extension/ directory not found."

  local python_bin
  python_bin="$(detect_python)"

  install_python_dependencies "$python_bin"
  install_extension_dependencies
  check_ollama
  pull_models
  run_benchmark

  log "Environment setup finished."
  log "Activate Python with: source .venv/bin/activate"
  log "Run benchmark with: cd benchmark && python benchmark.py"
}

main "$@"
