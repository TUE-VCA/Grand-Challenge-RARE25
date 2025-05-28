import os
import uuid
import pandas as pd
from pathlib import Path
from shutil import copy2

# Configuration
root_dir = r"E:\RARE2025_FINAL_DATA\train"  # original dataset
anonymized_root = r"E:\RARE2025_FINAL_DATA\train_anoniem"  # where anonymized copies will go
output_excel = "anonymized_mapping.xlsx"

# Ensure output directory exists
os.makedirs(anonymized_root, exist_ok=True)

# Collect mapping
mappings = []

for center in os.listdir(root_dir):
    center_path = os.path.join(root_dir, center)
    if os.path.isdir(center_path):
        for label in os.listdir(center_path):
            label_path = os.path.join(center_path, label)
            if os.path.isdir(label_path):
                for fname in os.listdir(label_path):
                    fpath = os.path.join(label_path, fname)
                    if os.path.isfile(fpath):
                        ext = os.path.splitext(fname)[-1]
                        new_name = f"{uuid.uuid4().hex}{ext}"

                        # Create corresponding output directory
                        out_dir = os.path.join(anonymized_root, center, label)
                        os.makedirs(out_dir, exist_ok=True)

                        new_path = os.path.join(out_dir, new_name)

                        # Copy instead of rename
                        copy2(fpath, new_path)

                        # Save mapping
                        mappings.append({
                            "original_path": os.path.relpath(fpath, root_dir),
                            "anonymized_path": os.path.relpath(new_path, anonymized_root)
                        })

# Save to Excel
df = pd.DataFrame(mappings)
df.to_excel(output_excel, index=False)

print(f"Anonymized copies created in: {anonymized_root}")
print(f"Mapping saved to: {output_excel}")
