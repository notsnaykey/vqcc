#!/usr/bin/env bash
# Download the competition bundle (reference circuits, verifiers, FeMoCo data, paper).
# Needs a Kaggle API token in ~/.kaggle/kaggle.json (or KAGGLE_USERNAME/KAGGLE_KEY)
# and acceptance of the competition rules on the Kaggle website first.
set -euo pipefail
cd "$(dirname "$0")/.."
COMP=google-verifiable-quantum-circuit-compilation
mkdir -p data
if ! command -v kaggle >/dev/null; then
  echo "kaggle CLI missing: run 'uv sync --extra kaggle' or 'pip install kaggle'" >&2
  exit 1
fi
kaggle competitions download -c "$COMP" -p data
cd data && unzip -o -q "$COMP.zip" && rm -f "$COMP.zip"
echo "Done. Contents of data/:"
find . -maxdepth 2 | sort | head -50
