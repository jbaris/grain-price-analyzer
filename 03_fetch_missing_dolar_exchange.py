import requests
import json
from datetime import datetime, timedelta
from lxml import html

# Read the json file ./data/dolar_exchange.json
with open('./data/dolar_exchange.json', 'r') as f:
    data = json.load(f)

# Fetch the last record of .data
last_record = data['data'][-1]
last_date = datetime.strptime(last_record[0], '%Y-%m-%d')
last_value = last_record[1]

# Set the date range
init_date = last_date + timedelta(days=1)
end_date = datetime.now()

# Prepare output file
output_file = './data/dolar_exchange_complete.json'
seen_dates = set()
rows_to_write = []

for i in range((end_date - init_date).days + 1):
    print(f"Processing date {i+1} of {(end_date - init_date).days + 1}")
    current_date = init_date + timedelta(days=i)
    date_str_url = current_date.strftime('%d/%m/%Y')
    date_str_out = current_date.strftime('%Y-%m-%d')
    url = f'https://www.bna.com.ar/Cotizador/HistoricoPrincipales?id=billetes&fecha={date_str_url}&filtroEuro=0&filtroDolar=1'
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        content = resp.text
        # Skip all until <div id="cotizacionesCercanas">
        idx = content.find('<div id="cotizacionesCercanas">')
        if idx == -1:
            # fallback: write last known value
            if date_str_out not in seen_dates:
                rows_to_write.append({"date": date_str_out, "value": last_value})
                seen_dates.add(date_str_out)
            continue
        content = content[idx:]
        print(f"Fetched data for {date_str_url}: \n {content}")
        # Parse the HTML
        tree = html.fromstring(content)
        rows = tree.xpath('//div[@id="tablaDolar"]/table/tbody/tr')
        if not rows:
            # fallback: write last known value
            if date_str_out not in seen_dates:
                rows_to_write.append({"date": date_str_out, "value": last_value})
                seen_dates.add(date_str_out)
            continue
        for row in rows[1:]:  # skip header
            cells = row.xpath('./td')
            if len(cells) < 4:
                continue
            value_raw = cells[2].text_content().strip().replace(',', '.')
            try:
                value = float(value_raw)
                formatted_value = f"{value:.1f}"
            except Exception:
                continue
            date_cell = cells[3].text_content().strip()
            # Format date as YYYY-MM-DD
            try:
                date_obj = datetime.strptime(date_cell, '%d/%m/%Y')
                date_str = date_obj.strftime('%Y-%m-%d')
            except Exception:
                date_str = date_str_out
            if date_str not in seen_dates:
                rows_to_write.append({"date": date_str, "value": formatted_value})
                seen_dates.add(date_str)
    except Exception:
        # fallback: write last known value
        if date_str_out not in seen_dates:
            rows_to_write.append({"date": date_str_out, "value": last_value})
            seen_dates.add(date_str_out)

# Load existing data from dolar_exchange.json into rows_to_write
print(f"Loading existing data from ./data/dolar_exchange.json")
for record in data['data']:
    date_str = record[0]
    value = record[1]
    if date_str not in seen_dates:
        rows_to_write.append({"date": date_str, "value": value})
        seen_dates.add(date_str)

# Write to file, override on each run as valid JSON
print(f"Writing {len(rows_to_write)} records to {output_file}")
json_rows = []
for row in rows_to_write:
    date_part = row["date"]
    value_part = row["value"]
    try:
        value = float(value_part)
    except Exception:
        value = value_part
    # Truncate the float value to has only two decimals
    if isinstance(value, float):
        value = float(f"{value:.2f}")
    json_rows.append([date_part, value])

# Sort the list by date before writing
json_rows.sort(key=lambda x: x[0])

with open(output_file, 'w') as f:
    json.dump({"data": json_rows}, f, ensure_ascii=False)
