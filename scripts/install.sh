#!/usr/bin/env bash
# Check for, and where possible install, the prerequisites for this repository.
#
# Usage: scripts/install.sh [--check] [--no-venv] [--yes]
#   --check    only report what is present or missing; change nothing
#   --no-venv  install Python packages with `pip --user` instead of into ./.venv
#   --yes      don't ask before installing system packages (Homebrew/apt/dnf)
#
# Environment: PYTHON=<interpreter> to choose the Python used to create the venv.
set -euo pipefail

CHECK_ONLY=0; USE_VENV=1; ASSUME_YES=0
for a in "$@"; do
  case "$a" in
    --check) CHECK_ONLY=1 ;;
    --no-venv) USE_VENV=0 ;;
    --yes|-y) ASSUME_YES=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
MIN_PY="3.8"
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
FAILED=0

confirm() {  # confirm "question"
  [ "$ASSUME_YES" = 1 ] && return 0
  [ -t 0 ] || return 1
  read -r -p "  $1 [y/N] " r; [[ "$r" =~ ^[Yy] ]]
}

os_name() {
  case "$(uname -s)" in
    Darwin) echo macos ;;
    Linux)  grep -qi microsoft /proc/version 2>/dev/null && echo wsl || echo linux ;;
    *)      echo other ;;
  esac
}

install_system_pkg() {  # install_system_pkg <brew-name> <apt-name> <dnf-name>
  local brew="$1" apt="$2" dnf="$3"
  if command -v brew >/dev/null 2>&1; then
    confirm "Install '$brew' with Homebrew?" && brew install "$brew" && return 0
  elif command -v apt-get >/dev/null 2>&1; then
    confirm "Install '$apt' with apt-get (needs sudo)?" && sudo apt-get update -qq && sudo apt-get install -y $apt && return 0
  elif command -v dnf >/dev/null 2>&1; then
    confirm "Install '$dnf' with dnf (needs sudo)?" && sudo dnf install -y $dnf && return 0
  fi
  return 1
}

py_ok() {  # py_ok <interpreter>: true if it is Python >= MIN_PY
  "$1" -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int,'$MIN_PY'.split('.'))) else 1)" 2>/dev/null
}

echo "Prerequisites for $(basename "$ROOT") ($(os_name))"

# 1. Python 3.8+
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1 && py_ok "$c"; then PY="$c"; break; fi
  done
fi
if [ -n "$PY" ] && py_ok "$PY"; then
  ok "Python $("$PY" -c 'import platform; print(platform.python_version())') ($(command -v "$PY"))"
else
  err "Python >= $MIN_PY not found"
  if [ "$CHECK_ONLY" = 0 ] && install_system_pkg python python3 python3; then
    PY=python3; ok "Python installed"
  else
    warn "Install Python $MIN_PY+ from https://www.python.org/downloads/ (or: brew install python / sudo apt install python3)"
    exit 1
  fi
fi

# 2. git and make (informational; only needed for contributing / the Makefile)
for t in git make; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t $("$t" --version | head -1 | grep -oE '[0-9]+(\.[0-9]+)+' | head -1)"
  else
    warn "$t not found (macOS: xcode-select --install; Debian/Ubuntu: sudo apt install $t)"
  fi
done

# 3. Python packages (only the analysis scripts need them; the downloaders use the standard library)
if [ "$USE_VENV" = 1 ]; then
  if [ -x "$VENV/bin/python" ]; then
    ok "virtual environment: .venv"
  elif [ "$CHECK_ONLY" = 1 ]; then
    warn "virtual environment .venv not created yet (run: make install)"
  else
    if ! "$PY" -m venv --help >/dev/null 2>&1; then
      warn "the Python venv module is missing"
      install_system_pkg python python3-venv python3 || { err "cannot create a virtual environment; rerun with --no-venv"; exit 1; }
    fi
    "$PY" -m venv "$VENV" && ok "created .venv"
  fi
  PIP_PY="$VENV/bin/python"; PIP_FLAGS=()
else
  PIP_PY="$PY"; PIP_FLAGS=(--user)
fi

check_pkgs() {
  [ -x "$PIP_PY" ] || command -v "$PIP_PY" >/dev/null 2>&1 || return 1
  "$PIP_PY" - <<'PYEOF'
import importlib, sys
mods = {'openpyxl': 'openpyxl', 'xlrd': 'xlrd', 'docx': 'python-docx', 'striprtf': 'striprtf',
        'pdfplumber': 'pdfplumber', 'pandas': 'pandas'}
missing = []
for m, pkg in mods.items():
    try: importlib.import_module(m); print(f'  \033[32m✓\033[0m {pkg}')
    except Exception: print(f'  \033[33m!\033[0m {pkg} missing'); missing.append(pkg)
sys.exit(1 if missing else 0)
PYEOF
}

if [ "$CHECK_ONLY" = 1 ]; then
  check_pkgs || { warn "some Python packages are missing (run: make install)"; FAILED=1; }
else
  "$PIP_PY" -m pip install --quiet --upgrade pip ${PIP_FLAGS[@]+"${PIP_FLAGS[@]}"} || true
  "$PIP_PY" -m pip install --quiet ${PIP_FLAGS[@]+"${PIP_FLAGS[@]}"} -r "$ROOT/requirements.txt" && ok "installed requirements.txt"
  check_pkgs || { err "package check failed"; FAILED=1; }
fi

# 4. Network reachability (informational)
for u in https://cibmtr.org https://www.ebi.ac.uk/europepmc/webservices/rest/; do
  if "$PY" -c "import urllib.request,sys; urllib.request.urlopen(urllib.request.Request(sys.argv[1], headers={'User-Agent':'Mozilla/5.0'}), timeout=10)" "$u" 2>/dev/null; then
    ok "reachable: $u"
  else
    warn "cannot reach $u (downloads will fail until this works)"
  fi
done

if [ "$FAILED" = 0 ]; then echo "Ready. Try: make help"; else echo "Some checks failed; see above."; fi
exit "$FAILED"
