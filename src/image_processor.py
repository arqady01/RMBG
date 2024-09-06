import os
from rembg import remove
from PIL import Image

def process_image(input_path, output_folder, progress_callback):
    output_filename = f"processed_{os.path.basename(input_path)}"
    output_path = os.path.join(output_folder, output_filename)

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    with Image.open(input_path) as img:
        output = remove(img)
        output.save(output_path, format="PNG")

    progress_callback(100)  # Set progress to 100% when done