"""
Image I/O module for AlanPaint
Handles loading and saving images with Pillow
"""

from PIL import Image
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
    Returns PIL Image in RGB mode
    """
    try:
        img = Image.open(path)
        
        # Convert to RGB for consistent handling (remove alpha channel)
        if img.mode in ("RGBA", "LA", "P"):
            # Keep palette for GIF, otherwise convert to RGB
            if img.mode == "P" and "transparency" in img.info:
                img = img.convert("RGBA")
            elif img.mode != "P":
                img = img.convert("RGB")
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        
        return img
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
        
        pil_image.save(path, **save_kwargs)
        return True
    except Exception as e:
        raise ValueError(f"Failed to save image: {e}")


def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """
    Convert PIL Image to QImage efficiently
    Uses direct byte array conversion to avoid memory duplication
    """
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    
    data = pil_image.tobytes()
    width, height = pil_image.size
    
    return QImage(data, width, height, width * 3, QImage.Format_RGB888)


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """
    Convert QImage to PIL Image
    """
    # Get image data
    width = qimage.width()
    height = qimage.height()
    
    # Convert to RGB if needed
    if qimage.format() != QImage.Format_RGB888:
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
    
    # Get raw bytes
    ptr = qimage.bits()
    ptr.setsize(width * height * 3)
    
    return Image.frombytes("RGB", (width, height), ptr.tobytes())


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
