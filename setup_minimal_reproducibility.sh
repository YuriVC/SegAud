#!/usr/bin/env bash
set -Eeuo pipefail

# Minimal reproducibility setup for SegAud.
# It prepares the environment and runs the benchmark with a single Ollama model.
#
# Optional environment variables:
#   INSTALL_OLLAMA=1                 Try to install Ollama if it is missing.
#   PULL_MODEL=0                     Skip model download.
#   RUN_BENCHMARK=0                  Skip benchmark execution.
#   MINIMAL_MODEL=deepseek-coder     Override the single model.
#   PYTHON_BIN=python3               Override Python executable.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"
EXTENSION_DIR="$PROJECT_ROOT/extension"
VENV_DIR="$PROJECT_ROOT/.venv-minimal"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434/api/chat}"
OLLAMA_HEALTH_URL="${OLLAMA_HEALTH_URL:-${OLLAMA_URL%/api/chat}/api/tags}"
MINIMAL_MODEL="${MINIMAL_MODEL:-deepseek-coder:latest}"

log() {
  printf '\n[minimal-setup] %s\n' "$*"
}

warn() {
  printf '\n[minimal-setup][warning] %s\n' "$*" >&2
}

fail() {
  printf '\n[minimal-setup][error] %s\n' "$*" >&2
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
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
  elif [[ -f "$VENV_DIR/Scripts/activate" ]]; then
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
    log "Creating minimal Python virtual environment at .venv-minimal"
    "$python_bin" -m venv "$VENV_DIR"
  else
    log "Reusing existing minimal Python virtual environment at .venv-minimal"
  fi

  activate_venv

  log "Installing benchmark Python dependencies"
  python -m pip install --upgrade pip
  python -m pip install -r "$PROJECT_ROOT/requirements.txt"
}

install_extension_dependencies() {
  if ! command_exists npm; then
    warn "npm was not found; skipping extension dependency installation."
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
          (ollama serve >/tmp/segaud-ollama-minimal.log 2>&1 &)
        fi
      else
        (ollama serve >/tmp/segaud-ollama-minimal.log 2>&1 &)
      fi
      ;;
    Darwin*)
      if command_exists brew; then
        brew services start ollama >/dev/null 2>&1 || (ollama serve >/tmp/segaud-ollama-minimal.log 2>&1 &)
      else
        (ollama serve >/tmp/segaud-ollama-minimal.log 2>&1 &)
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
    fail "Ollama is required for minimal reproducibility."
  fi

  start_ollama_if_possible

  if command_exists curl && ! curl --silent --fail --max-time 5 "$OLLAMA_HEALTH_URL" >/dev/null; then
    warn "Ollama API did not respond at $OLLAMA_HEALTH_URL."
    warn "Model download or benchmark execution may fail if Ollama is not running."
  fi
}

pull_model() {
  if [[ "${PULL_MODEL:-1}" != "1" ]]; then
    log "Skipping model download. Use PULL_MODEL=1 to download $MINIMAL_MODEL."
    return
  fi

  log "Downloading minimal model: $MINIMAL_MODEL"
  if ! ollama pull "$MINIMAL_MODEL"; then
    warn "Could not pull $MINIMAL_MODEL. The benchmark will skip it if it is unavailable locally."
  fi
}

run_minimal_benchmark() {
  if [[ "${RUN_BENCHMARK:-1}" != "1" ]]; then
    log "Skipping benchmark execution. Use RUN_BENCHMARK=1 to run it."
    return
  fi

  log "Running benchmark with only $MINIMAL_MODEL"
  cd "$BENCHMARK_DIR"

  MINIMAL_MODEL="$MINIMAL_MODEL" python - <<'PY'
import os
import benchmark

model = os.environ.get("MINIMAL_MODEL", "deepseek-coder:latest")
benchmark.MODELS = [model]

print("Loading PHP security tests...")
results, heatmap_data = benchmark.run_benchmark()

print("\n=== FINAL RESULTS ===")
for model_name, data in results.items():
    print(f"\n{model_name.upper()}")
    if data.get("status") == "skipped":
        print("Status   : skipped")
        print(f"Reason   : {data.get('error', '')}")
        continue

    print(f"Accuracy : {data['accuracy']:.6f}")
    print(f"Precision: {data['precision']:.6f}")
    print(f"Recall   : {data['recall']:.6f}")
    print(f"F1 Score : {data['f1']:.6f}")
    print(f"TP={data['tp']} FP={data['fp']} FN={data['fn']}")

benchmark.print_ranking(results)
benchmark.save_csv(results)
benchmark.plot_f1(results)
benchmark.plot_metrics(results)
benchmark.plot_heatmap(heatmap_data)
benchmark.plot_radar(results)

print("\nMinimal benchmark finished successfully")
PY

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
  pull_model
  run_minimal_benchmark

  log "Minimal reproducibility setup finished."
}

main "$@"
