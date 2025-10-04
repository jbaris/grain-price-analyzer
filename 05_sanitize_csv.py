#!/usr/bin/env python3
"""
CSV Sanitization Script
Removes rows where any value differs by more than the threshold percentage from the previous row.
Displays warnings for discarded rows.
"""

import csv
import sys
from typing import List, Dict, Any

# Percentage threshold for outlier detection
OUTLIER_THRESHOLD_PERCENTAGE = 50.0


def is_numeric_column(column_name: str) -> bool:
    """Check if a column should be treated as numeric for comparison."""
    # Skip the date column
    return column_name != 'fecha'


def calculate_percentage_difference(current: float, previous: float) -> float:
    """Calculate the percentage difference between current and previous values."""
    if previous == 0:
        return float('inf') if current != 0 else 0
    return abs((current - previous) / previous) * 100


def sanitize_csv(input_file: str, output_file: str) -> None:
    """
    Sanitize CSV by removing rows with values that differ by more than the threshold from previous row,
    but only if the change is not sustained in the following 2 rows (indicating an isolated outlier).

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
    """
    discarded_count = 0
    total_rows = 0

    # First pass: read all rows into memory for lookahead analysis
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        all_rows = list(reader)

    # Get numeric columns
    numeric_columns = [col for col in fieldnames if is_numeric_column(col)]

    rows_to_keep = []

    for i, row in enumerate(all_rows):
        total_rows += 1
        row_num = i + 2  # Adjust for header row

        # Always keep the first data row
        if i == 0:
            rows_to_keep.append(row)
            continue

        previous_row = all_rows[i - 1]

        # Check for outliers in numeric columns
        is_outlier = False
        outlier_details = []

        for col in numeric_columns:
            try:
                current_value = float(row[col])
                previous_value = float(previous_row[col])

                diff_percentage = calculate_percentage_difference(current_value, previous_value)

                if diff_percentage > OUTLIER_THRESHOLD_PERCENTAGE:
                    # Check if this change is sustained in the next 2 rows
                    is_sustained_change = False

                    # Look ahead at next 2 rows (if they exist)
                    for j in range(1, 3):  # Check next 1-2 rows
                        if i + j < len(all_rows):
                            try:
                                next_value = float(all_rows[i + j][col])

                                # Check if the trend continues in the same direction
                                # If current > previous and next is also > previous (or close to current)
                                # then it's likely a real trend change, not an outlier

                                # Calculate if next value is closer to current than to previous
                                diff_current_to_next = abs(current_value - next_value)
                                diff_previous_to_next = abs(previous_value - next_value)

                                # If next value is closer to current value than to previous,
                                # it suggests the change is sustained
                                if diff_current_to_next <= diff_previous_to_next:
                                    is_sustained_change = True
                                    break

                            except (ValueError, TypeError):
                                continue

                    # Only mark as outlier if the change is NOT sustained
                    if not is_sustained_change:
                        is_outlier = True
                        outlier_details.append(f"{col}: {previous_value} -> {current_value} ({diff_percentage:.1f}% change, isolated)")

            except (ValueError, TypeError):
                # Skip non-numeric values
                continue

        if is_outlier:
            discarded_count += 1
            print(f"WARNING: Discarding row {row_num} - {row['fecha']} (isolated outlier)")
            for detail in outlier_details:
                print(f"  {detail}")
            print(f"  Full row: {dict(row)}")
            print()
        else:
            rows_to_keep.append(row)

    # Write sanitized data to output file
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)

    # Summary
    kept_rows = len(rows_to_keep)
    print(f"Sanitization complete:")
    print(f"  Total rows processed: {total_rows}")
    print(f"  Rows kept: {kept_rows}")
    print(f"  Rows discarded: {discarded_count}")
    print(f"  Output written to: {output_file}")


def main():
    """Main function to run the CSV sanitization."""
    input_file = './data/prices.csv'
    output_file = './data/prices_sanitized.csv'

    try:
        sanitize_csv(input_file, output_file)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
