import json
import requests
import csv
from concurrent.futures import ThreadPoolExecutor

# List of URLs to fetch JSON data from
urls = {
    "person": "https://api.wossidia.de/nodes/at_bkw0",
    "letters": "https://api.wossidia.de/nodes/at_bkw1",
    "sheets": "https://api.wossidia.de/nodes/at_bkw2",
    "pages": "https://api.wossidia.de/nodes/at_bkw3"
}

# Helper function to fetch JSON data from a URL
def fetch_json_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    return response.json()

# Function to process the nodes and create a hierarchical structure
def process_nodes(data, level_name):
    processed_data = []
    for item in data['result']:
        node = {
            'id': item.get('id'),
            'signature': item.get('signature'),
            'type': level_name,
            'parent': item['attributes'].get('parent'),
            'sig3': item['attributes'].get('sig3'),
            'imagedigital': item['attributes'].get('imagedigital'),
            'wossig': item['attributes'].get('wossig'),
            'info2': ', '.join([f"{info['key']}: {info['value']}" if info['value'] else info['key'] for info in item['attributes'].get('info2', [])])
        }
        processed_data.append(node)
    return processed_data

# Fetch data from all URLs concurrently and process nodes
with ThreadPoolExecutor() as executor:
    futures = {level_name: executor.submit(fetch_json_data, url) for level_name, url in urls.items()}
    results = {level_name: future.result() for level_name, future in futures.items()}

# Combine the data into a hierarchical dictionary
hierarchy = {
    "person": {},
    "letters": {},
    "sheets": {},
    "pages": {}
}

for level_name, result in results.items():
    for node in process_nodes(result, level_name):
        hierarchy[level_name][node['id']] = node

# Function to recursively build the hierarchical structure
def build_hierarchy(hierarchy, current_id, current_level):
    if current_level == "pages":
        return [hierarchy["pages"].get(current_id, {})]

    next_level = {
        "person": "letters",
        "letters": "sheets",
        "sheets": "pages"
    }[current_level]

    children = []
    for node_id, node in hierarchy[next_level].items():
        if node['parent'] == current_id:
            children.extend(build_hierarchy(hierarchy, node_id, next_level))

    current_node = hierarchy[current_level].get(current_id, {})
    current_node[next_level] = children
    return [current_node]

# Build the complete hierarchy
full_hierarchy = []
for person_id in hierarchy["person"]:
    full_hierarchy.extend(build_hierarchy(hierarchy, person_id, "person"))

# Flatten the hierarchy for CSV output
flattened_data = []

def flatten_node(node, person_info=None, letter_info=None, sheet_info=None):
    if node['type'] == "pages":
        page_imagedigital = node.get('imagedigital')
        page_imagedigital_hex = hex(int(page_imagedigital))[2:] if page_imagedigital is not None else None  # remove '0x' prefix
        flattened_data.append({
            **person_info,
            **letter_info,
            **sheet_info,
            "page_id": node['id'],
            "page_signature": node['signature'],
            "page_imagedigital": page_imagedigital,
            "page_imagedigital_hex": page_imagedigital_hex,
            "page_wossig": node['wossig'],
            "page_info2": node['info2'],
            "page_sig3": node['sig3']
        })
    else:
        next_level = {
            "person": "letters",
            "letters": "sheets",
            "sheets": "pages"
        }[node['type']]

        if node['type'] == "person":
            person_info = {
                "person_id": node['id'],
                "person_signature": node['signature'],
                "person_imagedigital": node['imagedigital'],
                "person_wossig": node['wossig'],
                "person_info2": node['info2'],
                "person_sig3": node['sig3']
            }
        elif node['type'] == "letters":
            letter_info = {
                "letter_id": node['id'],
                "letter_signature": node['signature'],
                "letter_imagedigital": node['imagedigital'],
                "letter_wossig": node['wossig'],
                "letter_info2": node['info2'],
                "letter_sig3": node['sig3']
            }
        elif node['type'] == "sheets":
            sheet_info = {
                "sheet_id": node['id'],
                "sheet_signature": node['signature'],
                "sheet_imagedigital": node['imagedigital'],
                "sheet_wossig": node['wossig'],
                "sheet_info2": node['info2'],
                "sheet_sig3": node['sig3']
            }

        for child in node.get(next_level, []):
            flatten_node(child, person_info, letter_info, sheet_info)

for person_node in full_hierarchy:
    flatten_node(person_node)

# Save the flattened data to a CSV file
csv_file = 'combined_data.csv'
fieldnames = [
    'person_id', 'person_signature', 'person_imagedigital', 'person_wossig', 'person_info2', 'person_sig3',
    'letter_id', 'letter_signature', 'letter_imagedigital', 'letter_wossig', 'letter_info2', 'letter_sig3',
    'sheet_id', 'sheet_signature', 'sheet_imagedigital', 'sheet_wossig', 'sheet_info2', 'sheet_sig3',
    'page_id', 'page_signature', 'page_imagedigital', 'page_imagedigital_hex', 'page_wossig', 'page_info2', 'page_sig3'
]

with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(flattened_data)

# Print the path to the output file
print(f"Combined data has been saved to {csv_file}")
