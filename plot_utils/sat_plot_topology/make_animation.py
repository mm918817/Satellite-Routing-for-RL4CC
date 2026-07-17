import os
from PIL import Image
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGE_FOLDER = BASE_DIR / "plots_full"
OUTPUT_GIF = BASE_DIR / "topology_animation.gif"

# How long each frame is shown (milliseconds)
DURATION = 200
LOOP = 0  # 0 = infinite loop

def create_gif(image_folder, output_gif):
    # Get image files and sort them
    images_files = sorted(
        IMAGE_FOLDER.glob("*.png")
    )


    if not images_files:
        raise ValueError("No images found in folder")

    # Load images
    frames = [Image.open(p) for p in images_files]


    # Save GIF
    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION,
        loop=LOOP
    )

    print(f"GIF created: {output_gif}")

if __name__ == "__main__":
    create_gif(IMAGE_FOLDER, OUTPUT_GIF)
