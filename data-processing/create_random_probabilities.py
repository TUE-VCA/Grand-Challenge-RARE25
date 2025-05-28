import os
import json
import uuid
import random
from PIL import Image

# Set your input folder
input_folder = r"E:\RARE2025_FINAL_DATA\test-val-tiff"
predictions_path = os.path.join(input_folder, "predictions.json")

# Container for all prediction entries
predictions = []

# Go through each TIFF file
for filename in os.listdir(input_folder):
    if filename.lower().endswith((".tiff", ".tif")):
        tiff_path = os.path.join(input_folder, filename)
        base_name = os.path.splitext(filename)[0]

        # Count the number of pages
        with Image.open(tiff_path) as img:
            page_count = 0
            try:
                while True:
                    img.seek(page_count)
                    page_count += 1
            except EOFError:
                pass

        # Generate random probabilities
        random_probs = [round(random.random(), 4) for _ in range(page_count)]

        # Create output folder and save the likelihoods JSON
        output_folder = os.path.join(input_folder, base_name)
        os.makedirs(output_folder, exist_ok=True)
        json_output_path = os.path.join(output_folder, "stacked-neoplastic-lesion-likelihoods.json")
        with open(json_output_path, 'w') as f:
            json.dump(random_probs, f, indent=2)

        # Create a prediction entry
        entry = {
            "pk": base_name,  # or use str(uuid.uuid4()) if you want a UUID
            "inputs": [
                {
                    "file": None,
                    "image": {
                        "name": filename
                    },
                    "value": None,
                    "interface": {
                        "slug": "stacked-barretts-esophagus-endoscopy-images",
                        "kind": "Image",
                        "super_kind": "Image",
                        "relative_path": "images/stacked-barretts-esophagus-endoscopy",
                        "example_value": None
                    }
                }
            ],
            "outputs": [
                {
                    "file": "https://grand-challenge.org/media/some-link/stacked-neoplastic-lesion-likelihoods.json",
                    "image": None,
                    "value": None,
                    "interface": {
                        "slug": "stacked-neoplastic-lesion-likelihoods",
                        "kind": "Anything",
                        "super_kind": "File",
                        "relative_path": "stacked-neoplastic-lesion-likelihoods.json",
                        "example_value": random_probs
                    }
                }
            ],
            "status": "Succeeded",
            "started_at": "2024-11-29T10:31:25.691799Z",
            "completed_at": "2024-11-29T10:31:50.691799Z"
        }

        predictions.append(entry)

# Write all predictions to predictions.json
with open(predictions_path, 'w') as f:
    json.dump(predictions, f, indent=2)

print(f"✅ Created predictions.json with {len(predictions)} entries.")
