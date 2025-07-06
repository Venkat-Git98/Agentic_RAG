"""
Utilities for processing and handling images for multimodal LLM prompts.
"""
import os
import base64
import mimetypes
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assumes an 'images' directory exists at the root of the project at runtime.
IMAGE_DIR = "images"

def get_image_filename_from_path(full_path: str) -> Optional[str]:
    """
    Safely extracts the image filename from a full database path string.
    Example: 'D:/.../images/Chapter_16_p47_img1.jpeg' -> 'Chapter_16_p47_img1.jpeg'
    """
    if not full_path or not isinstance(full_path, str):
        return None
    try:
        return os.path.basename(full_path)
    except Exception as e:
        logger.error(f"Error parsing path '{full_path}': {e}")
        return None

def process_image_for_llm(full_path: str) -> Optional[Dict[str, str]]:
    """
    Processes an image from a given database path, returning a dictionary
    formatted for a multimodal LLM prompt (e.g., Gemini).

    Args:
        full_path: The full path to the image file as stored in the database.

    Returns:
        A dictionary containing the mime_type and base64-encoded data,
        or None if processing fails.
    """
    filename = get_image_filename_from_path(full_path)
    if not filename:
        return None

    image_path = os.path.join(IMAGE_DIR, filename)
    
    if not os.path.exists(image_path):
        logger.warning(f"Image not found at expected runtime path: {image_path}")
        return None

    try:
        # Guess the MIME type of the image (e.g., 'image/jpeg')
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image'):
            logger.warning(f"Could not determine a valid image MIME type for {image_path}")
            return None

        # Read the image file in binary mode and encode it in base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # Return in the format required by the Google Generative AI API
        return {
            "mime_type": mime_type,
            "data": encoded_string
        }

    except Exception as e:
        logger.error(f"Failed to process image {image_path}: {e}")
        return None 