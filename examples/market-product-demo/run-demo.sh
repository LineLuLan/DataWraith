#!/usr/bin/env bash
set -euo pipefail

DURATION="${DURATION:-10}"
WORKERS="${WORKERS:-4}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/market-demo}"
DEMO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${DEMO_ROOT}/../.." && pwd)"
REPORT_DIR="${REPO_ROOT}/${OUTPUT_DIR}"

mkdir -p "${REPORT_DIR}"

printf '== DataWraith Market Product Demo ==\n'
printf 'Repo: %s\n' "${REPO_ROOT}"
printf 'Reports: %s\n\n' "${REPORT_DIR}"

printf '== Runtime doctor ==\n'
sdb doctor

printf '\n== Load demo schema ==\n'
sdb init "${DEMO_ROOT}/schema.sql" --execute

printf '\n== Load demo sample data ==\n'
sdb init "${DEMO_ROOT}/sample_data.sql" --execute

printf '\n== Concurrency: products.stock ==\n'
sdb attack concurrency --execute --table products --column stock --duration "${DURATION}" --workers "${WORKERS}" --updates 80 --output "${REPORT_DIR}/concurrency.json"

printf '\n== R/W-heavy workload ==\n'
sdb attack rw-heavy --execute --duration "${DURATION}" --workers "${WORKERS}" --row-count 100 --operations 300 --output "${REPORT_DIR}/rw-heavy.json"

printf '\n== Migration-lock workload ==\n'
sdb attack migration --execute --table products --column market_demo_flag --duration "${DURATION}" --workers 2 --row-count 100 --operations 200 --output "${REPORT_DIR}/migration.json"

printf '\n== Security/isolation workload ==\n'
sdb attack security --execute --duration "${DURATION}" --tenants 3 --rows-per-tenant 5 --fuzz-payloads 8 --output "${REPORT_DIR}/security.json"

printf '\n== Export security reports ==\n'
sdb report "${REPORT_DIR}/security.json" --format sarif --output "${REPORT_DIR}/security.sarif"
sdb report "${REPORT_DIR}/security.json" --format junit --output "${REPORT_DIR}/security.xml"
sdb report "${REPORT_DIR}/security.json" --format pdf --output "${REPORT_DIR}/security.pdf"

printf '\n== Compare concurrency vs rw-heavy ==\n'
sdb compare "${REPORT_DIR}/concurrency.json" "${REPORT_DIR}/rw-heavy.json"

printf '\nDemo complete. Open reports in: %s\n' "${REPORT_DIR}"
