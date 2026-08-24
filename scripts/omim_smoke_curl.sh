#!/usr/bin/env bash
# Smoke: same GET as acquire.py _search_page. Prints HTTP status; on failure prints OMIM response body.
# Key: OMIM_API_KEY or legacy API_KEY from env/.env or repo-root .env (same as omim2obo / CI secrets).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

_key_from_file() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local line key
  line="$(grep -E '^[[:space:]]*(OMIM_API_KEY|API_KEY)=' "$f" | head -1 || true)"
  [[ -n "$line" ]] || return 1
  key="${line#*=}"
  key="$(printf '%s' "${key}" | sed $'s/^\xef\xbb\xbf//' | tr -d '\r\n')"
  key="${key#\"}"; key="${key%\"}"
  key="${key#"${key%%[![:space:]]*}"}"; key="${key%"${key##*[![:space:]]}"}"
  [[ -n "$key" ]] || return 1
  printf '%s' "$key"
}

KEY=""
KEY="$(_key_from_file "${ROOT}/env/.env" || true)"
if [[ -z "${KEY}" ]]; then
  KEY="$(_key_from_file "${ROOT}/.env" || true)"
fi
[[ -n "${KEY}" ]] || {
  echo "Missing API key: set OMIM_API_KEY or API_KEY in env/.env or .env" >&2
  exit 1
}

body="$(mktemp)"
trap 'rm -f "${body}"' EXIT
code="$(curl -sS -o "${body}" -w "%{http_code}" \
  -G "https://api.omim.org/api/entry/search" \
  --data-urlencode "search=*" \
  --data-urlencode "start=0" \
  --data-urlencode "limit=1" \
  --data-urlencode "format=json" \
  --data-urlencode "sort=number asc" \
  -H "ApiKey: ${KEY}" \
  -H "Accept: application/json" \
  -H "Accept-Encoding: gzip")"
echo "${code}"
if [[ "${code}" != 2* ]]; then
  echo "response body:" >&2
  cat "${body}" >&2
  exit 1
fi
