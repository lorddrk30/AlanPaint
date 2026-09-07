"""
Image I/O module for AlanPaint
Handles loading and saving images with Pillow
"""

from PIL import Image, ImageOps
from PIL.Image import Resampling
from PySide6.QtGui import QImage, QColor
import os


# Supported formats with Qt and Pillow
SUPPORTED_FORMATS = {
    "PNG": ("PNG Files (*.png)", ".png"),
    "JPG": ("JPEG Files (*.jpg *.jpeg)", ".jpg"),
    "WEBP": ("WebP Files (*.webp)", ".webp"),
    "BMP": ("BMP Files (*.bmp)", ".bmp"),
    "GIF": ("GIF Files (*.gif)", ".gif"),
    "TIFF": ("TIFF Files (*.tif *.tiff)", ".tif"),
}

# All supported extensions
SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"]


def load_image(path: str) -> Image.Image:
    """
    Load an image from file using Pillow
    Returns an independent RGB or RGBA image, applying EXIF orientation.
    """
    try:
        with Image.open(path) as source:
            img = ImageOps.exif_transpose(source)
            has_alpha = "A" in img.getbands() or "transparency" in img.info
            return img.convert("RGBA" if has_alpha else "RGB")
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")


def save_image(pil_image: Image.Image, path: str, quality: int = 95) -> bool:
    """
    Save PIL image to file
    Supports PNG, JPG, WEBP, BMP, GIF, TIFF
    """
    try:
        ext = os.path.splitext(path)[1].lower()
        
        save_kwargs = {}
        
        if ext in (".jpg", ".jpeg"):
            save_kwargs = {"quality": quality, "optimize": True}
        elif ext == ".webp":
            save_kwargs = {"quality": quality}
        elif ext == ".png":
            save_kwargs = {"optimize": True}
        elif ext in (".tif", ".tiff"):
            save_kwargs = {"compression": "tiff_deflate"}
        
        if ext in (".jpg", ".jpeg", ".bmp") and pil_image.mode == "RGBA":
            background = Image.new("RGB", pil_image.size, "white")
            background.paste(pil_image, mask=pil_image.getchannel("A"))
            pil_image = background
        pil_image.save(path, **save_kwargs)
        return True
    except Exception as e:
        raise ValueError(f"Failed to save image: {e}")


def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """
    Convert to an owned QImage, preserving alpha and buffer lifetime.
    """
    if pil_image.mode not in ("RGB", "RGBA"):
        pil_image = pil_image.convert("RGBA")
    
    data = pil_image.tobytes()
    width, height = pil_image.size
    
    channels = 4 if pil_image.mode == "RGBA" else 3
    fmt = QImage.Format_RGBA8888 if channels == 4 else QImage.Format_RGB888
    return QImage(data, width, height, width * channels, fmt).copy()


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """
    Convert QImage to PIL Image
    """
    # Get image data
    width = qimage.width()
    height = qimage.height()
    
    qimage = qimage.convertToFormat(QImage.Format_RGBA8888)
    return Image.frombytes("RGBA", (width, height), bytes(qimage.bits()),
                           "raw", "RGBA", qimage.bytesPerLine())


def create_blank_image(width: int, height: int, color: tuple = (255, 255, 255)) -> Image.Image:
    """
    Create a blank image with white background
    """
    return Image.new("RGB", (width, height), color)


def get_image_info(path: str) -> dict:
    """
    Get information about an image file
    """
    try:
        with Image.open(path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "size": os.path.getsize(path)
            }
    except Exception as e:
        return {"error": str(e)}
