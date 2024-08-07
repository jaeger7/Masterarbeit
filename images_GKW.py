import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import shutil

# Define the base URL and the local directory to save images
BASE_URL = "http://nrw.wossidia.de/"
LOCAL_DIR = "venv/downloaded_images"

# Create the local directory if it doesn't exist
os.makedirs(LOCAL_DIR, exist_ok=True)


# Function to download an image
def download_image(file_path):
    url = BASE_URL + file_path
    local_path = os.path.join(LOCAL_DIR, file_path.replace('/', '_'))
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"Successfully downloaded {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {file_path}: {e}")


# Function to read the CSV and start downloading images
def download_images_from_csv(csv_file_path, start_index, num_images):
    df = pd.read_csv(csv_file_path)
    file_paths = df['filepath'].tolist()

    # Select the specified range of file paths
    file_paths = file_paths[start_index - 1:start_index - 1 + num_images]

    # Use ThreadPoolExecutor to download images concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(download_image, file_paths)


# Provide the path to your CSV file
csv_file_path = 'C:/Users/Ahmad-PC/Desktop/data-1720545468962.csv'  # Update this with your CSV file path
download_images_from_csv(csv_file_path, start_index=1099, num_images=2000)


print("Images downloaded successfully.")
