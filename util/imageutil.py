import re
import shutil

import requests
from PIL import Image
import pillow_heif
import os

pillow_heif.register_heif_opener()

def download_image(url: str, dest: str):
    headers = {
        "Referer": "https://manganato.com/"
    }

    res = requests.get(url, headers=headers, stream=True)

    if res.status_code == 200:
        with open(dest, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
    else:
        print('Image Couldn\'t be retrieved: ' + url)

def convert_to_heif(input_path: str, output_path: str, quality: int = 90):
    """
    Converts an image to HEIF format with specified quality.

    Parameters:
        input_path (str): Path to the input image.
        output_path (str): Destination path for the HEIF image (should end with .heif or .heic).
        quality (int): Compression quality (0-100). Higher means better quality.
    """
    try:
        img = Image.open(input_path)

        img.save(output_path, format="HEIF", quality=quality)
    except Exception as e:
        print(f"Error converting to HEIF: {e}")


def convert_to_webp(input_path: str, output_path: str, quality: int = 90, lossless: bool = False, method: int = 6,
                    icc_profile: bool = True):
    """
    Converts an image to WebP format with specified quality and additional options.

    Parameters:
        input_path (str): Path to the input image.
        output_path (str): Destination path for the WebP image (should end with .webp).
        quality (int): Compression quality (0-100). Higher means better quality.
        lossless (bool): Whether to use lossless compression. Default is False (lossy compression).
        method (int): Compression method (0-6), where 0 is fastest and 6 is best compression.
        icc_profile (bool): Whether to embed the ICC color profile in the image. Default is True.
    """
    try:
        img = Image.open(input_path)

        # Convert to WebP with the specified parameters
        save_options = {
            'quality': quality,
            'lossless': lossless,
            'method': method,
            'icc_profile': img.info.get('icc_profile') if icc_profile else None
        }

        img.save(output_path, format="WebP", **save_options)
    except Exception as e:
        print(f"Error converting to WebP: {e}")


if __name__ == "__main__":
    url = "https://avt.mkklcdnv6temp.com/9/w/25-1638293846.jpg"
    dest = "../thumbnail.jpg"

    download_image(url, dest)
    convert_to_heif(dest, "../thumbnail.heif", quality=40)

