#!/bin/bash
# Fetch historical USD exchange rates from datos.gob.ar
# Usage: bash scripts/02_fetch_dolar_exchange.sh

curl 'https://apis.datos.gob.ar/series/api/series/?ids=168.1_T_CAMBIOR_D_0_0_26&start_date=2018-07&limit=5000' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'referer: https://datosgobar.github.io/' > ../data/dolar_exchange.json
