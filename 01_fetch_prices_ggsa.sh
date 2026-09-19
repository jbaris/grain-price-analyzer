#!/bin/bash
# Fetch prices from GGSA website incrementally.
# Requests only from the last date already present in data/prices_ggsa.json
# and merges the response WITHOUT overwriting existing dates.
# Usage (from repo root): bash 01_fetch_prices_ggsa.sh
set -euo pipefail

OUTPUT="./data/prices_ggsa.json"
TODAY=$(date +%Y-%m-%d)

if [ -f "$OUTPUT" ]; then
  START=$(python3 -c "import json;print(max(json.load(open('$OUTPUT'))['pizarra']))")
else
  START="2017-01-01"
fi

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

echo "Fetching GGSA prices from $START to $TODAY..."
curl -sS "https://www.ggsa.com.ar/get_pizarra/pros59/$START/$TODAY/" \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -b 'csrftoken=L8agw2oRRNP4AEZ7i7scTHGhGZXcbyPLyUXXQnMsdNuRGJJLennnVHbCz0EzQWw7; _ga=GA1.1.435062795.1759241973; _ga_XE3TVVQ9N4=GS2.1.s1759568785$o7$g0$t1759568785$j60$l0$h0' \
  -H 'Origin: https://www.ggsa.com.ar' \
  -H 'Referer: https://www.ggsa.com.ar/' \
  -H 'X-CSRFToken: L8agw2oRRNP4AEZ7i7scTHGhGZXcbyPLyUXXQnMsdNuRGJJLennnVHbCz0EzQWw7' \
  --data-raw '{}' -k -o "$TMP"

python3 - "$TMP" "$OUTPUT" <<'PY'
import json, sys
tmp_path, out_path = sys.argv[1], sys.argv[2]

with open(tmp_path, encoding="utf-8") as f:
    fetched = json.load(f)
new = fetched.get("pizarra")
if not isinstance(new, dict):
    sys.exit(f"Unexpected GGSA response: {str(fetched)[:200]}")

try:
    with open(out_path, encoding="utf-8") as f:
        existing = json.load(f)
except FileNotFoundError:
    existing = {"pizarra": {}}

pizarra = existing.setdefault("pizarra", {})
added = {k: v for k, v in new.items() if k not in pizarra}
pizarra.update(added)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False)

if added:
    print(f"Added {len(added)} new dates ({min(added)} to {max(added)}); total {len(pizarra)} dates in {out_path}")
else:
    print(f"No new dates; {out_path} unchanged ({len(pizarra)} dates, last {max(pizarra)})")
PY
