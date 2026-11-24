#!/usr/bin/env bash
# Run all offline tests (no network needed).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
status=0
for t in "$ROOT"/scripts/tests/test_*.py; do
  printf '%-40s ' "$(basename "$t")"
  if out=$("$PYTHON" "$t" 2>&1); then echo "passed"; else echo "FAILED"; echo "$out" | tail -20; status=1; fi
done
exit $status
