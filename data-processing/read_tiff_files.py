from PIL import Image, TiffImagePlugin
import matplotlib.pyplot as plt

# === CONFIG ===
tiff_path = r"E:\RARE2025_FINAL_DATA\test-val-tiff\test_batch_0_99.tiff"  # adjust path as needed

# === Open the TIFF file ===
img = Image.open(tiff_path)

# === Read all frames (pages) ===
images = []
try:
    while True:
        images.append(img.copy())
        img.seek(img.tell() + 1)
except EOFError:
    pass  # Reached the last frame

# === Visualize the first 10 images ===
num_to_show = min(10, len(images))
plt.figure(figsize=(15, 6))
for i in range(num_to_show):
    plt.subplot(2, 5, i + 1)
    plt.imshow(images[i])
    plt.axis('off')
    plt.title(f"Image {i}")
plt.tight_layout()
plt.show()
