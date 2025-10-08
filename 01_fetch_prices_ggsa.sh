#!/bin/bash
# Fetch historical prices from GGSA website
# Usage: bash scripts/01_fetch_prices_ggsa.sh

START="2017-01-01"
TODAY=$(date +%Y-%m-%d)
curl "https://www.ggsa.com.ar/get_pizarra/pros59/$START/$TODAY/" \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -b 'csrftoken=L8agw2oRRNP4AEZ7i7scTHGhGZXcbyPLyUXXQnMsdNuRGJJLennnVHbCz0EzQWw7; _ga=GA1.1.435062795.1759241973; _ga_XE3TVVQ9N4=GS2.1.s1759568785$o7$g0$t1759568785$j60$l0$h0' \
  -H 'Origin: https://www.ggsa.com.ar' \
  -H 'Referer: https://www.ggsa.com.ar/' \
  -H 'X-CSRFToken: L8agw2oRRNP4AEZ7i7scTHGhGZXcbyPLyUXXQnMsdNuRGJJLennnVHbCz0EzQWw7' \
  --data-raw '{}' -k # > ./data/prices_ggsa.json
