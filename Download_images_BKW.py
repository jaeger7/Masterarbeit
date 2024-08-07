import csv
import requests
import os

# URL to fetch JSON data
url = "https://api.wossidia.de/nodes/at_bkw3"

# Fetch the JSON data from the URL
response = requests.get(url)
data = response.json()

# Extract the relevant information from the JSON data
nodes = data.get('result', [])

# CSV file name
csv_file = "nodes_data_with_hex_sorted.csv"

# Field names
fieldnames = ["id", "signature", "parent", "sig3", "imagedigital", "imagedigital_hex", "wossig", "info2"]

# Function to extract 'info2' as a comma-separated string
def extract_info2(info2_list):
    if not info2_list:
        return ""
    return ", ".join([f"{item.get('key', '')}: {item.get('value', '')}" if item.get('value') else item.get('key', '') for item in info2_list])

# Sort the nodes first by 'parent' and then by 'sig3'
sorted_nodes = sorted(nodes, key=lambda x: (str(x['attributes'].get('parent', '')), x['attributes'].get('sig3', '')))

# Function to download an image
def download_image(hex_value, parent):
    image_url = f"https://digipool.wossidia.de/{hex_value}/working"
    image_path = os.path.join("images", str(parent), f"{hex_value}.jpg")

    # Create directories if not exist
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    # Download the image
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(image_path, 'wb') as img_file:
            img_file.write(response.content)
        print(f"Downloaded {image_path}")
    else:
        print(f"Failed to download {image_url}")

# Function to handle the downloading of images for specified parents
def download_images_for_parents(parents):
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Writing headers (field names)
        writer.writeheader()

        # Writing data rows and downloading images
        for node in sorted_nodes:
            parent = str(node['attributes'].get("parent", ""))
            if parent in parents:
                imagedigital = node['attributes'].get("imagedigital", "")
                imagedigital_hex = hex(imagedigital)[2:].upper() if isinstance(imagedigital, int) else ""
                node_data = {
                    "id": node.get("id", ""),
                    "signature": node.get("signature", ""),
                    "parent": parent,
                    "sig3": node['attributes'].get("sig3", ""),
                    "imagedigital": imagedigital,
                    "imagedigital_hex": imagedigital_hex,
                    "wossig": node['attributes'].get("wossig", ""),
                    "info2": extract_info2(node['attributes'].get("info2", []))
                }
                writer.writerow(node_data)

                # Download the image
                if imagedigital_hex:
                    download_image(imagedigital_hex, parent)

# List of parents for which images should be downloaded
parents_to_download = ["1120010863", "1120010864", "1120010897", "1120010898", "1120010899", "1120009515", "1120009516", "1120009517", "1120009518", "1120009519", "1120010093", "1120010094", "1120010095", "1120010096","1120011142"]  # Replace with actual parent values

# Call the function to download images and create the CSV
download_images_for_parents(parents_to_download)
