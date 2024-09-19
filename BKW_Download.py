import json
import requests
import os
from concurrent.futures import ThreadPoolExecutor

# List of URLs to fetch JSON data from
urls = {
    "person": "https://api.wossidia.de/nodes/at_bkw0",
    "letters": "https://api.wossidia.de/nodes/at_bkw1",
    "sheets": "https://api.wossidia.de/nodes/at_bkw2",
    "pages": "https://api.wossidia.de/nodes/at_bkw3"
}


def fetch_json_data(url):
    response = requests.get(url)
    response.raise_for_status()
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

# Function to download an image
def download_image(hex_value, letter_id, sheet_id):
    image_url = f"https://digipool.wossidia.de/{hex_value}/working"
    image_dir = os.path.join("images", str(letter_id), str(sheet_id))
    image_path = os.path.join(image_dir, f"{hex_value}.jpg")

    os.makedirs(image_dir, exist_ok=True)

    try:
        # Download the image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        with open(image_path, 'wb') as img_file:
            img_file.write(response.content)
        print(f"Downloaded {image_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {image_url}: {e}")

# Function to process the hierarchy and download images
def process_hierarchy(node, letter_info=None, sheet_info=None):
    if node['type'] == "pages":
        page_imagedigital = node.get('imagedigital')
        page_imagedigital_hex = hex(int(page_imagedigital))[2:] if page_imagedigital is not None else None  # remove '0x' prefix

        # Download the image for the page
        if page_imagedigital_hex and letter_info and sheet_info:
            download_image(page_imagedigital_hex, letter_info['letter_id'], sheet_info['sheet_id'])
    else:
        next_level = {
            "person": "letters",
            "letters": "sheets",
            "sheets": "pages"
        }[node['type']]

        if node['type'] == "letters":
            letter_info = {
                "letter_id": node['id'],
                "letter_signature": node['signature'],
            }
        elif node['type'] == "sheets":
            sheet_info = {
                "sheet_id": node['id'],
                "sheet_signature": node['signature'],
            }

        for child in node.get(next_level, []):
            process_hierarchy(child, letter_info, sheet_info)

# Process each person node in the hierarchy to download images for all letters and sheets
for person_node in full_hierarchy:
    for letter in person_node.get('letters', []):
        process_hierarchy(letter)  # Ensure that all sheets within each letter are processed
