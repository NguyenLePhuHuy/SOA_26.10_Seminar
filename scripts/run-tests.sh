#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/tests/run-tests.sh" ]; then
    bash "$PROJECT_ROOT/tests/run-tests.sh"
elif [ -f "$PROJECT_ROOT/prepare/tests/run-tests.sh" ]; then
    bash "$PROJECT_ROOT/prepare/tests/run-tests.sh"
else
    echo "[X] Khong tim thay test suite"
    exit 1
fi
