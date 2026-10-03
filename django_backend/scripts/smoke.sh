#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
BASE_URL="${BASE_URL%/}"

echo "Checking $BASE_URL/healthz"
health="$(curl -fsS "$BASE_URL/healthz")"
echo "$health" | grep -q '"status":"ok"'
echo "$health" | grep -q '"database":"ok"'

echo "Checking public institutions endpoint"
curl -fsS "$BASE_URL/api/v1/institutions" | grep -q '"items"'

if [[ -n "${AUTH_TOKEN:-}" ]]; then
  echo "Checking authenticated /auth/me"
  curl -fsS -H "Authorization: Bearer $AUTH_TOKEN" "$BASE_URL/api/v1/auth/me" | grep -q '"id"'
fi

echo "CampusHub Django smoke test passed."
