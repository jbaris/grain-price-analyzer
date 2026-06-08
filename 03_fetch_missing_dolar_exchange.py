#!/usr/bin/env python3
"""Build a complete daily USD exchange-rate series from BCRA raw text data."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

INPUT_FILE = Path("./data/dolar_bcra.txt")
OUTPUT_FILE = Path("./data/dolar_exchange_complete.json")


def parse_rate(raw_value: str) -> float:
    """Parse rates that may use comma decimal separator."""
    normalized = raw_value.strip()
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "")
    normalized = normalized.replace(",", ".")
    return float(normalized)


def load_rates_by_date(input_path: Path) -> dict[date, float]:
    """Load raw file rows as a date->rate map, validating row format."""
    rates: dict[date, float] = {}

    with input_path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid format at line {line_number}: expected '<date>\\t<value>'"
                )

            try:
                parsed_date = datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
                parsed_rate = parse_rate(parts[1])
            except ValueError as exc:
                raise ValueError(f"Invalid data at line {line_number}: {line}") from exc

            rates[parsed_date] = parsed_rate

    if not rates:
        raise ValueError(f"Input file has no valid data: {input_path}")

    return rates


def complete_daily_series(rates_by_date: dict[date, float]) -> list[list[object]]:
    """Fill missing dates using the latest previous published value."""
    start_date = min(rates_by_date)
    end_date = max(rates_by_date)

    output_rows: list[list[object]] = []
    current_date = start_date
    last_known_rate: float | None = None

    while current_date <= end_date:
        if current_date in rates_by_date:
            last_known_rate = rates_by_date[current_date]

        if last_known_rate is None:
            raise ValueError(
                "Cannot complete series before first known exchange-rate value"
            )

        output_rows.append([current_date.isoformat(), round(last_known_rate, 4)])
        current_date += timedelta(days=1)

    return output_rows


def main() -> None:
    rates_by_date = load_rates_by_date(INPUT_FILE)
    complete_rows = complete_daily_series(rates_by_date)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as output_file:
        json.dump({"data": complete_rows}, output_file, ensure_ascii=False)

    print(
        f"Generated {len(complete_rows)} daily exchange-rate rows in {OUTPUT_FILE} "
        f"(from {complete_rows[0][0]} to {complete_rows[-1][0]})."
    )


if __name__ == "__main__":
    main()
