
import os
from google import genai
from google.genai import types
from models.config import GEMINI_API_KEY
from PIL import Image



def gen_images(model_id, prompt, negative_prompt, number_of_images, aspect_ratio, is_enhance):
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
    print(f"model_id: {model_id}, prompt: {prompt}, negative_prompt: {negative_prompt}, number_of_images: {number_of_images}, aspect_ratio: {aspect_ratio}, is_enhance: {is_enhance}")
    if is_enhance=="yes":
        enhance_prompt = True
    else:
        enhance_prompt = False

    response = client.models.generate_images(
        model=model_id,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            # negative_prompt =negative_prompt,
            number_of_images= number_of_images,
            aspect_ratio = aspect_ratio,
            # enhance_prompt=enhance_prompt,
            person_generation = "ALLOW_ADULT"
        )
    )
    return response.generated_images


def resize_image_aspect_ratio(image_path, output_path, new_width=None, new_height=None, quality=95):
    """
    Resizes an image while maintaining its aspect ratio.

    Args:
        image_path (str): Path to the input image file.
        output_path (str): Path to save the resized image file.
        new_width (int, optional): The desired new width. If provided, height is calculated.
        new_height (int, optional): The desired new height. If provided, width is calculated.
                                   If both new_width and new_height are None, no resizing happens.
                                   If both are provided, new_width takes precedence.
        quality (int): The quality for saving JPEG images (1-100). Ignored for other formats like PNG.

    Returns:
        bool: True if resizing was successful, False otherwise.
    """
    try:
        img = Image.open(image_path)
        original_width, original_height = img.size
        print(f"Original dimensions: {original_width}x{original_height}")

        if new_width is None and new_height is None:
            print("Error: You must provide either new_width or new_height.")
            # Optionally, just save a copy without resizing if desired
            # img.save(output_path, quality=quality)
            # return True
            return False

        # Calculate new dimensions while maintaining aspect ratio
        aspect_ratio = original_width / original_height

        if new_width is None and new_height is not None:
            target_width = new_width
            target_height = new_height
        else:
            if new_width is not None:
                calculated_height = int(new_width / aspect_ratio)
                target_width = new_width
                target_height = calculated_height
            elif new_height is not None: # new_width is None if we reach here
                calculated_width = int(new_height * aspect_ratio)
                target_width = calculated_width
                target_height = new_height

        print(f"Target dimensions: {target_width}x{target_height}")

        # --- Choose the Resampling Filter ---
        # Image.Resampling.LANCZOS: High-quality downscaling (recommended)
        # Image.Resampling.BICUBIC: Good quality for upscaling/downscaling
        # Image.Resampling.BILINEAR: Faster, decent quality
        # Image.Resampling.NEAREST: Fastest, lowest quality (pixelated)
        # Use LANCZOS for best quality, especially when making images smaller.
        resample_filter = Image.Resampling.LANCZOS

        # Resize the image
        resized_img = img.resize((target_width, target_height), resample=resample_filter)

        # --- Save the Resized Image ---
        # Ensure the output directory exists (optional)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save with appropriate options
        save_options = {}
        # Optimize and set quality for JPEGs
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            save_options['quality'] = quality
            save_options['optimize'] = True
        # Use lossless compression for PNGs
        elif output_path.lower().endswith('.png'):
             save_options['optimize'] = True # Can sometimes reduce filesize

        resized_img.save(output_path, **save_options)
        print(f"Resized image saved to: {output_path}")
        return True

    except FileNotFoundError:
        print(f"Error: Input image not found at {image_path}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False