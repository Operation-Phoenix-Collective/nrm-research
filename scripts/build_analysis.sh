#!/usr/bin/env bash
# Rebuild every derived file in the data folder from downloaded dictionaries (and datasets, if present).
# Usage: scripts/build_analysis.sh [DATA_DIR]      (default: data)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
DATA="${1:-$ROOT/data}"
if ! ls "$DATA"/dictionaries/P-* >/dev/null 2>&1; then
  echo "No dictionaries in $DATA/dictionaries. Run: make dictionaries" >&2; exit 1
fi
echo "==> parsing dictionaries";        "$PYTHON" "$ROOT/scripts/parse_dictionaries.py" "$DATA" 2> >(grep -v -i 'warn' >&2)
if ls "$DATA"/datasets/*.zip >/dev/null 2>&1; then
  echo "==> counting patients and TRM events"; "$PYTHON" "$ROOT/scripts/dataset_sizes.py" "$DATA" "$DATA/dataset_sizes.csv"
else
  echo "==> no datasets in $DATA/datasets; keeping the existing dataset_sizes.csv (run: make datasets)"
fi
echo "==> scoring and tiering";        "$PYTHON" "$ROOT/scripts/analyze_nrm.py" "$DATA" | head -1
echo "==> building workbook";          "$PYTHON" "$ROOT/scripts/build_workbook.py" "$DATA"
echo "Done. Findings tables: $PYTHON scripts/make_findings_tables.py A"
