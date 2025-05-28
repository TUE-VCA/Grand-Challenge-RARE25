import os
import json
from PIL import Image
from tqdm import tqdm

# === CONFIG ===
output_root = r'E:\RARE2025_FINAL_DATA\test-val-split'  # Same as before
tiff_output_dir = r'E:\RARE2025_FINAL_DATA\test-val-tiff'  # New folder to store TIFF batches
os.makedirs(tiff_output_dir, exist_ok=True)
batch_size = 384
resize_dim = (512, 512)

def extract_patient_id(filename):
    parts = os.path.basename(filename).split('_')
    return '_'.join(parts[:2]) if len(parts) >= 2 else 'unknown'

def create_batches(split):
    image_dir = os.path.join(output_root, split)
    metadata = {}
    batch = []
    batch_info = []
    batch_start = 0
    batch_num = 0

    all_images = []
    for cls in ['neo', 'ndbe']:
        cls_dir = os.path.join(image_dir, cls)
        for fname in os.listdir(cls_dir):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                all_images.append({
                    'path': os.path.join(cls_dir, fname),
                    'class': cls
                })

    for img_data in tqdm(all_images, desc=f"Processing {split} images"):
        img_path = img_data['path']
        cls = img_data['class']
        try:
            img = Image.open(img_path).convert('RGB')
            img = img.resize(resize_dim, Image.LANCZOS)
        except Exception as e:
            print(f"Error opening image {img_path}: {e}")
            continue

        batch.append(img)
        batch_info.append({
            'filename': os.path.basename(img_path),
            'class': cls,
            'index_in_batch': len(batch) - 1,
            'patient_id': extract_patient_id(img_path)
        })

        if len(batch) == batch_size:
            batch_end = batch_start + len(batch) - 1
            batch_filename = f"batch_{batch_start}_{batch_end}.tiff"
            batch_path = os.path.join(tiff_output_dir, f"{split}_{batch_filename}")
            dpi = (300, 300)  # Example: 300 DPI = 0.085 mm/pixel, adjust as needed
            tiff_tags = {
                'dpi': dpi,  # This sets XResolution and YResolution
            }

            batch[0].save(batch_path, save_all=True, append_images=batch[1:], dpi=dpi)

            batch_key = f"{split}_{batch_filename}"
            if batch_key not in metadata:
                metadata[batch_key] = []

            for info in batch_info:
                metadata[batch_key].append({
                    'filename': info['filename'],
                    'index': info['index_in_batch'],
                    'class': info['class'],
                    'patient_id': info['patient_id']
                })

            batch = []
            batch_info = []
            batch_start = batch_end + 1
            batch_num += 1

    # Last batch
    if batch:
        batch_end = batch_start + len(batch) - 1
        batch_filename = f"batch_{batch_start}_{batch_end}.tiff"
        batch_path = os.path.join(tiff_output_dir, f"{split}_{batch_filename}")
        batch[0].save(batch_path, save_all=True, append_images=batch[1:], dpi=dpi)

        batch_key = f"{split}_{batch_filename}"
        if batch_key not in metadata:
            metadata[batch_key] = []

        for info in batch_info:
            metadata[batch_key].append({
                'filename': info['filename'],
                'index': info['index_in_batch'],
                'class': info['class'],
                'patient_id': info['patient_id']
            })

    # Save metadata
    json_path = os.path.join(tiff_output_dir, f"{split}_metadata.json")
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved {split} metadata to: {json_path}")


# === Run for both sets ===
create_batches('val')
create_batches('test')