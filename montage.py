import os
import moviepy.editor as mp
from PIL import Image # Used for basic image handling if needed, though moviepy can resize

def create_photo_montage(
    image_folder: str,
    output_filename: str = "photo_montage.mp4",
    photo_duration_seconds: float = 0.2, # Default: 0.2 seconds per photo (5 photos/second)
    output_resolution: tuple = (1280, 720), # Default: 720p HD resolution
    output_fps: int = 30 # Frames per second for the output video
):
    """
    Creates a video montage from a folder of photos.

    Args:
        image_folder (str): Path to the folder containing image files.
        output_filename (str): Name of the output video file (e.g., "my_montage.mp4").
        photo_duration_seconds (float): Duration (in seconds) each photo will be displayed.
                                        Can be a fraction (e.g., 0.1 for 10 photos/second).
        output_resolution (tuple): (width, height) for the output video. All images will be
                                   resized to fit this resolution.
        output_fps (int): Frames per second for the output video. Higher values result in
                          smoother video, but larger file sizes.
    """

    if not os.path.isdir(image_folder):
        print(f"Error: Image folder '{image_folder}' not found.")
        return

    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

    # Get all image files from the folder, sorted alphabetically
    image_files = sorted([
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(image_extensions)
    ])

    if not image_files:
        print(f"No image files found in '{image_folder}'. Supported formats: {', '.join(image_extensions)}")
        return

    print(f"Found {len(image_files)} images in '{image_folder}'.")
    print(f"Each photo will be displayed for {photo_duration_seconds} seconds.")
    print(f"Output video resolution: {output_resolution[0]}x{output_resolution[1]} at {output_fps} FPS.")

    clips = []
    for img_path in image_files:
        try:
            # Create an ImageClip from the image file
            # moviepy's ImageClip can handle resizing directly
            clip = mp.ImageClip(img_path, duration=photo_duration_seconds)

            # Resize the clip to the desired output resolution.
            # 'resize' method can take a tuple (width, height).
            # If aspect ratios differ, it will stretch. For more advanced fitting
            # (e.g., fit with black bars or crop to fill), you'd need more logic here
            # or pre-process images with PIL.
            clip = clip.resize(newsize=output_resolution)

            clips.append(clip)
            print(f"Added {os.path.basename(img_path)} to montage.")
        except Exception as e:
            print(f"Warning: Could not process image {os.path.basename(img_path)}: {e}")

    if not clips:
        print("No valid image clips could be created. Montage not generated.")
        return

    # Concatenate all image clips into a single video clip
    final_clip = mp.concatenate_videoclips(clips)

    print(f"Writing video to '{output_filename}'...")
    try:
        # Write the final video file
        # codec='libx264' is a common and efficient codec for MP4
        final_clip.write_videofile(
            output_filename,
            fps=output_fps,
            codec='libx264',
            audio_codec='aac' # Include audio codec even if no audio, for compatibility
        )
        print(f"Montage successfully created: '{output_filename}'")
    except Exception as e:
        print(f"Error writing video file: {e}")
        print("Please ensure FFmpeg is installed and accessible in your system's PATH.")
        print("You can download FFmpeg from: https://ffmpeg.org/download.html")


if __name__ == "__main__":
    # --- Configuration ---
    # IMPORTANT: Replace 'path/to/your/photos' with the actual path to your image folder.
    # Example: 'C:/Users/YourUser/Pictures/MyVacationPhotos' or '/home/user/images'
    PHOTO_FOLDER = "images_for_montage" # Create a folder named 'images_for_montage' in the same directory as this script
                                       # and put some test photos inside it.

    OUTPUT_VIDEO_NAME = "my_photo_montage.mp4"

    # Duration each photo is shown (in seconds).
    # 0.5 means 2 photos per second.
    # 0.1 means 10 photos per second.
    PHOTO_DURATION = 0.15 # Example: ~6.6 photos per second

    # Resolution of the output video
    VIDEO_RESOLUTION = (1920, 1080) # Full HD

    # Frames per second of the output video
    VIDEO_FPS = 30 # Standard for smooth video

    # --- Create a dummy folder and some dummy images for testing ---
    if not os.path.exists(PHOTO_FOLDER):
        os.makedirs(PHOTO_FOLDER)
        print(f"Created dummy folder: {PHOTO_FOLDER}")
        # Create some dummy images
        for i in range(1, 6):
            dummy_img_path = os.path.join(PHOTO_FOLDER, f"image_{i}.png")
            try:
                img = Image.new('RGB', (800, 600), color = (i*50 % 255, i*100 % 255, i*150 % 255))
                img.save(dummy_img_path)
                print(f"Created dummy image: {dummy_img_path}")
            except Exception as e:
                print(f"Could not create dummy image {dummy_img_path}: {e}")
        print("\n--- Please replace dummy images with your actual photos in the folder ---")
        print(f"    '{PHOTO_FOLDER}' before running for real results.\n")
        utime.sleep(2) # Give user time to read

    # --- Run the montage creation ---
    create_photo_montage(
        image_folder=PHOTO_FOLDER,
        output_filename=OUTPUT_VIDEO_NAME,
        photo_duration_seconds=PHOTO_DURATION,
        output_resolution=VIDEO_RESOLUTION,
        output_fps=VIDEO_FPS
    )
