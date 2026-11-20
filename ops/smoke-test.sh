#!/bin/bash
# Read-only smoke checks: no credentials, private data, or paid API calls.
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-}"

check_status() {
    local label="$1" url="$2" expected="$3" actual
    if ! actual=$(curl --silent --show-error --max-time 20 --retry 1 \
        --output /dev/null --write-out '%{http_code}' "$url"); then
        echo "$label: connection failed" >&2
        return 1
    fi
    if [[ "$actual" != "$expected" ]]; then
        echo "$label: expected HTTP $expected, got $actual" >&2
        return 1
    fi
    echo "$label: HTTP $actual"
}

check_status 'Backend health' "${BACKEND_URL%/}/health" 200
check_status 'Public jobs listing' "${BACKEND_URL%/}/jobs?page=1&per_page=5" 200
check_status 'Unauthenticated plan must be denied' "${BACKEND_URL%/}/users/me/plan" 401

if [[ -n "$FRONTEND_URL" ]]; then
    check_status 'Frontend home' "${FRONTEND_URL%/}/" 200
fi

# This is only an anonymous smoke check, not an authenticated Apply test.
echo 'Read-only smoke checks passed.'
