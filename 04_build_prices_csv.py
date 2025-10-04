#!/usr/bin/env python3
"""
Script to build prices CSV from GGSA prices and USD exchange rate data.

Reads maize, wheat, and soy prices from prices_ggsa.json and matches them
with USD exchange rates from dolar_exchange_complete.json to create a CSV
with prices converted to USD.
"""

import json
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Start date constant - only include data from this date onwards
START_DATE = '2018-07-01'


def load_prices_data(file_path: str) -> Dict:
    """Load prices data from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_exchange_rates(file_path: str) -> Dict[str, float]:
    """Load exchange rates and convert to date->rate dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert the data array to a dictionary for easy lookup
    exchange_rates = {}
    for date_str, rate in data['data']:
        exchange_rates[date_str] = float(rate)
    
    return exchange_rates


def extract_cereal_prices_by_date(prices_data: Dict, cereals: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Extract prices for specified cereals from the prices data, grouped by date.
    
    Returns dictionary: {date: {cereal: price_in_ars}}
    """
    prices_by_date = {}
    
    pizarra_data = prices_data.get('pizarra', {})
    
    for date_str, date_data in pizarra_data.items():
        date_prices = {}
        for cereal in cereals:
            if cereal in date_data:
                cereal_data = date_data[cereal]
                price_str = cereal_data.get('precio', '0.00')
                if price_str == '0.00':
                    price_str = cereal_data.get('estimativo', '0.00')
                # Convert price to float, handling potential string values
                try:
                    price_ars = float(price_str)
                    if price_ars > 0:  # Only include non-zero prices
                        date_prices[cereal] = price_ars
                except (ValueError, TypeError):
                    # Skip invalid price values
                    continue
        
        # Only include dates that have at least one cereal price
        if date_prices:
            prices_by_date[date_str] = date_prices
    
    return prices_by_date


def find_exchange_rate(date_str: str, exchange_rates: Dict[str, float]) -> Optional[float]:
    """
    Find exchange rate for a given date.
    If exact date not found, try to find the closest previous date.
    """
    if date_str in exchange_rates:
        return exchange_rates[date_str]
    
    # Try to find the closest previous date
    target_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Sort dates and find the closest previous one
    sorted_dates = sorted(exchange_rates.keys())
    for exchange_date_str in reversed(sorted_dates):
        exchange_date = datetime.strptime(exchange_date_str, '%Y-%m-%d')
        if exchange_date <= target_date:
            return exchange_rates[exchange_date_str]
    
    return None


def build_prices_csv():
    """Main function to build the prices CSV file."""
    
    # File paths
    prices_file = './data/prices_ggsa.json'
    exchange_file = './data/dolar_exchange_complete.json'
    output_file = './data/prices.csv'
    
    print("Loading prices data...")
    prices_data = load_prices_data(prices_file)
    
    print("Loading exchange rates...")
    exchange_rates = load_exchange_rates(exchange_file)
    
    print("Extracting cereal prices...")
    cereals = ['maiz', 'trigo', 'soja']  # maize, wheat, soy
    prices_by_date = extract_cereal_prices_by_date(prices_data, cereals)
    
    print(f"Found {len(prices_by_date)} dates with cereal price data")
    
    # Sort dates in ascending order
    sorted_dates = sorted(prices_by_date.keys())
    
    # Write CSV file
    print(f"Writing CSV to {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['fecha', 'maiz_ars', 'trigo_ars', 'soja_ars', 'tipo_cambio_usd', 'maiz_usd', 'trigo_usd', 'soja_usd'])
        
        # Write data rows
        records_written = 0
        for date_str in sorted_dates:
            # Only include data from START_DATE onwards
            if date_str < START_DATE:
                continue

            exchange_rate = find_exchange_rate(date_str, exchange_rates)
            
            if exchange_rate is not None:
                date_prices = prices_by_date[date_str]
                
                # Get prices for each cereal (0 if not available)
                maiz_ars = date_prices.get('maiz', 0)
                trigo_ars = date_prices.get('trigo', 0)
                soja_ars = date_prices.get('soja', 0)
                
                # Skip rows where any cereal price is zero
                if maiz_ars == 0 or trigo_ars == 0 or soja_ars == 0:
                    continue
                
                # Calculate USD prices
                maiz_usd = round(maiz_ars / exchange_rate, 2)
                trigo_usd = round(trigo_ars / exchange_rate, 2)
                soja_usd = round(soja_ars / exchange_rate, 2)
                
                writer.writerow([date_str, maiz_ars, trigo_ars, soja_ars, exchange_rate, maiz_usd, trigo_usd, soja_usd])
                records_written += 1
            else:
                print(f"Warning: No exchange rate found for date {date_str}")
    
    print(f"Successfully wrote {records_written} records to {output_file}")


if __name__ == '__main__':
    build_prices_csv()
