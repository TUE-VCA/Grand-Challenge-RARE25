import os
import random
from collections import defaultdict
from shutil import copy2

# Set paths
data_root = r'E:\RARE2025_FINAL_DATA\test-all'
output_root = r'E:\RARE2025_FINAL_DATA\test-val-split'
folders = ['neo', 'ndbe']

# Build dictionary: {class: {patient_id: [file1, file2, ...]}}
patient_images = {'neo': defaultdict(list), 'ndbe': defaultdict(list)}

for folder in folders:
    class_path = os.path.join(data_root, folder)
    for filename in os.listdir(class_path):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            parts = filename.split('_')
            if len(parts) >= 2:
                patient_id = '_'.join(parts[:2])
                patient_images[folder][patient_id].append(os.path.join(class_path, filename))

# Shuffle patient IDs
random.seed(42)
neo_patients = list(patient_images['neo'].keys())
ndbe_patients = list(patient_images['ndbe'].keys())
random.shuffle(neo_patients)
random.shuffle(ndbe_patients)

# Select validation set by including entire patients (even if we exceed the target count)
val_patients = {'neo': [], 'ndbe': []}
val_counts = {'neo': 0, 'ndbe': 0}
target_counts = {'neo': 100, 'ndbe': 1000}

for cls in ['neo', 'ndbe']:
    patients = neo_patients if cls == 'neo' else ndbe_patients
    for pid in patients:
        images = patient_images[cls][pid]
        val_patients[cls].append(pid)
        val_counts[cls] += len(images)
        if val_counts[cls] >= target_counts[cls]:
            break

# Determine test patients (remaining ones not in validation)
test_patients = {
    'neo': [pid for pid in neo_patients if pid not in val_patients['neo']],
    'ndbe': [pid for pid in ndbe_patients if pid not in val_patients['ndbe']]
}

# Copy files and collect test info
test_image_paths = []

def copy_images(patients, split):
    for cls in ['neo', 'ndbe']:
        for pid in patients[cls]:
            for filepath in patient_images[cls][pid]:
                rel_path = os.path.join(split, cls)
                dest_dir = os.path.join(output_root, rel_path)
                os.makedirs(dest_dir, exist_ok=True)
                copy2(filepath, dest_dir)
                if split == 'test':
                    test_image_paths.append(filepath)

# Copy images
copy_images(val_patients, 'val')
copy_images(test_patients, 'test')

# Count final images
val_image_count = {
    cls: sum(len(patient_images[cls][pid]) for pid in val_patients[cls])
    for cls in ['neo', 'ndbe']
}
test_image_count = {
    cls: sum(len(patient_images[cls][pid]) for pid in test_patients[cls])
    for cls in ['neo', 'ndbe']
}

# Print summary
print(f"\nValidation set: {val_image_count['neo']} neo, {val_image_count['ndbe']} ndbe")
print(f"Validation patients: {len(val_patients['neo'])} neo, {len(val_patients['ndbe'])} ndbe")

print(f"\nTest set: {test_image_count['neo']} neo, {test_image_count['ndbe']} ndbe")
print(f"Test patients: {len(test_patients['neo'])} neo, {len(test_patients['ndbe'])} ndbe")

print("\nTest patient IDs:")
print("NEO:", test_patients['neo'])
print("NDBE:", test_patients['ndbe'])
