import os
import pandas as pd
from PIL import Image as PILImage
from wand.image import Image as WandImage
import math

def radians_to_degrees(radians):
    return math.degrees(radians)

def generate_unique_filename(base_name, extension, output_dir):
    counter = 1
    new_filename = f"{base_name}{extension}"
    while os.path.exists(os.path.join(output_dir, new_filename)):
        new_filename = f"{base_name}_{counter}{extension}"
        counter += 1
    return new_filename

def rotate_image_with_wand(input_path, output_temp_path, angle_radians):
    angle_degrees = radians_to_degrees(angle_radians)  # Convert radians to degrees
    with WandImage(filename=input_path) as img:
        img.rotate(angle_degrees)
        img.format = 'jpeg'  # Save as JPEG
        img.save(filename=output_temp_path)

def rotate_and_crop_image(input_path, output_path, angle_radians, left_cut, top_cut, right_cut, bottom_cut):
    temp_path = 'temp_rotated_image.jpg'
    try:
        # Rotate image with Wand
        rotate_image_with_wand(input_path, temp_path, angle_radians)

        # Open the rotated image with PIL for cropping
        with PILImage.open(temp_path) as img:
            # Crop image using the provided coordinates
            img = img.crop((left_cut, top_cut, img.width - right_cut, img.height - bottom_cut))
            img.save(output_path)
    except Exception as e:
        print(f"Error processing image {input_path}: {e}")
    finally:
        # Ensure the temporary file is properly closed before attempting to delete it
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)  # Clean up the temporary file
        except PermissionError as e:
            print(f"Error removing temp file {temp_path}: {e}")

# Example usage with CSV
csv_file_path = 'C:/Users/Ahmad-PC/Desktop/data-1720545468962.csv'
base_image_path = 'C:/Users/Ahmad-PC/Desktop/downloaded_images/'  # Update with the base path where images are located
output_dir = 'C:/Users/Ahmad-PC/Desktop/Cropped_Images/'  # Update with the output directory

df = pd.read_csv(csv_file_path)

start_row = 0  # Set this to the desired starting row index

for index, row in df.iloc[start_row:].iterrows():
    filename = row['filepath'].replace('/', '_')
    input_image_path = os.path.join(base_image_path, filename)

    if os.path.exists(input_image_path):
        base_name = os.path.splitext(filename)[0]
        extension = '.jpg'  # Change to your desired output format
        unique_filename = generate_unique_filename(base_name, extension, output_dir)
        output_image_path = os.path.join(output_dir, unique_filename)

        angle_radians = row['angle']  # Angle is in radians in the CSV
        left_cut = abs(row['west'])
        top_cut = abs(row['north'])
        right_cut = abs(row['east'])
        bottom_cut = abs(row['south'])

        rotate_and_crop_image(input_image_path, output_image_path, angle_radians, left_cut, top_cut, right_cut,
                              bottom_cut)
    else:
        print(f"Image file {filename} not found in directory.")