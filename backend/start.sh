#!/bin/bash
# Legacy start alias. Root runtime is source of truth.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/start_backend.sh"
