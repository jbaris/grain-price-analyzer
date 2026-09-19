#!/usr/bin/env python3
"""Append missing BCRA wholesale USD reference rates (Com. A 3500) to data/dolar_bcra.txt.

Fetches only the days after the last date already present in the file, from the
public BCRA API (v4, variable 5), and appends them in the file's own format:
"DD/MM/YYYY<TAB>1.442,4148". Existing lines are never modified.
Run from the repo root.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

load_rates_by_date = import_module("03_fetch_missing_dolar_exchange").load_rates_by_date

INPUT_FILE = Path("./data/dolar_bcra.txt")
METADATA_FILE = Path("./data/dolar_bcra.metadata")
BCRA_VARIABLE_ID = 5  # Tipo de cambio mayorista de referencia (Com. A 3500)
API_URL = f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{BCRA_VARIABLE_ID}"


def format_rate(value: float) -> str:
    """Format like the BCRA site export: thousands '.', decimal ',', 4 decimals."""
    integer_part, decimal_part = f"{value:.4f}".split(".")
    integer_part = f"{int(integer_part):,}".replace(",", ".")
    return f"{integer_part},{decimal_part}"


def fetch_rates(desde: date, hasta: date) -> dict[date, float]:
    params = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "limit": 3000}
    try:
        response = requests.get(API_URL, params=params, timeout=60)
    except requests.exceptions.SSLError:
        response = requests.get(API_URL, params=params, timeout=60, verify=False)
    response.raise_for_status()
    payload = response.json()

    rates: dict[date, float] = {}
    for result in payload.get("results", []):
        for row in result.get("detalle", []):
            rates[date.fromisoformat(row["fecha"])] = float(row["valor"])
    return rates


def main() -> None:
    existing = load_rates_by_date(INPUT_FILE)
    last_date = max(existing)
    today = date.today()
    desde = last_date + timedelta(days=1)

    if desde > today:
        print(f"{INPUT_FILE} already up to date (last {last_date}).")
        return

    print(f"Fetching BCRA rates from {desde} to {today}...")
    fetched = fetch_rates(desde, today)
    new_rows = sorted((d, v) for d, v in fetched.items() if d not in existing and d >= desde)

    if not new_rows:
        print(f"No new rates published after {last_date}; {INPUT_FILE} unchanged.")
        return

    needs_newline = not INPUT_FILE.read_bytes().endswith(b"\n")
    with INPUT_FILE.open("a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        for d, v in new_rows:
            f.write(f"{d.strftime('%d/%m/%Y')}\t{format_rate(v)}\n")

    METADATA_FILE.write_text(
        f"{API_URL}?desde=2018-01-01&hasta={new_rows[-1][0].isoformat()}\n", encoding="utf-8"
    )

    print(
        f"Appended {len(new_rows)} rates ({new_rows[0][0]} to {new_rows[-1][0]}) to {INPUT_FILE}."
    )


if __name__ == "__main__":
    main()
