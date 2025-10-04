#!/usr/bin/env python3
"""
Script to merge events_regular.json and events_special.json into all_events.json.
Regular events are duplicated for every year from 2018 to current year.
Special events are copied as is.
"""

import json
from datetime import datetime
import os

def load_json_file(filepath):
    """Load JSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return None

def merge_events():
    """Merge regular and special events into a single file."""
    # Define file paths
    regular_events_path = "data/events_regular.json"
    special_events_path = "data/events_special.json"
    output_path = "data/events_all.json"
    
    # Load input files
    regular_events = load_json_file(regular_events_path)
    special_events = load_json_file(special_events_path)
    
    if regular_events is None or special_events is None:
        return
    
    # Initialize the merged events dictionary
    all_events = {}
    
    # Copy special events as is
    all_events.update(special_events)
    
    # Get current year
    current_year = datetime.now().year
    
    # Duplicate regular events for each year from 2018 to current year
    for year in range(2018, current_year + 1):
        for date_key, event_description in regular_events.items():
            # Convert DD-MM format to YYYY-MM-DD format
            day, month = date_key.split('-')
            full_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            all_events[full_date] = event_description
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Write merged events to output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_events, f, indent=2, ensure_ascii=False)
        print(f"Successfully created {output_path}")
        print(f"Total events: {len(all_events)}")
        print(f"Regular events duplicated for years 2018-{current_year}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")

if __name__ == "__main__":
    merge_events()
