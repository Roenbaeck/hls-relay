#!/usr/bin/env bash

# Simple launcher that appends relay output to a YYYYMMDD.log file
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "${LOG_DIR}"

LOG_FILE="${LOG_DIR}/$(date +%Y%m%d).log"
echo "Logging to ${LOG_FILE}"

python3 -u "${SCRIPT_DIR}/hls_relay.py" >> "${LOG_FILE}" 2>&1
