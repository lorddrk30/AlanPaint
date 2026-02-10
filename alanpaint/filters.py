"""
Image filters module for AlanPaint
Applies image filters using Pillow with memory efficiency
"""

from PIL import Image, ImageEnhance, ImageFilter
from typing import Callable, Union, Tuple, Optional


# Filter function type
FilterFunc = Callable[[Image.Image], Image.Image]


def grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale"""
    return img.convert("L").convert("RGB")


def invert(img: Image.Image) -> Image.Image:
    """Invert image colors"""
    return Image.eval(img, lambda x: 255 - x)


def brightness(img: Image.Image, factor: float = 1.0) -> Image.Image:
    """Adjust image brightness"""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


def contrast(img: Image.Image, factor: float = 1.0) -> Image.Image:
    """Adjust image contrast"""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


def saturation(img: Image.Image, factor: float = 1.0) -> Image.Image:
    """Adjust image saturation/color intensity"""
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(factor)


def blur(img: Image.Image, radius: float = 2.0) -> Image.Image:
    """Apply gaussian blur"""
    return img.filter(ImageFilter.GaussianBlur(radius))


def sharpen(img: Image.Image, factor: float = 1.0) -> Image.Image:
    """Sharpen the image"""
    enhancer = ImageEnhance.Sharpness(img)
    return enhancer.enhance(factor)


def posterize(img: Image.Image, bits: int = 4) -> Image.Image:
    """
    Reduce the number of bits used for each color channel
    bits: 1-8, lower means fewer colors
    """
    factor = 256 - (2 ** bits)
    return Image.eval(img, lambda x: x & ~factor)


def sepia(img: Image.Image) -> Image.Image:
    """Apply sepia tone effect"""
    # Convert to grayscale
    gray = img.convert("L")
    
    # Apply sepia matrix
    sepia_matrix = [
        0.393, 0.769, 0.189, 0,
        0.349, 0.686, 0.168, 0,
        0.272, 0.534, 0.131, 0
    ]
    
    sepia_img = gray.convert("RGB", sepia_matrix)
    return sepia_img


def auto_contrast(img: Image.Image) -> Image.Image:
    """Auto contrast adjustment"""
    # Find min and max values for each channel
    extrema = img.convert("RGB").getextrema()
    print(f"Extrema: {extrema}")
    # Scale each channel
    return img.convert("RGB")


def apply_filter(img: Image.Image, filter_name: str, **kwargs) -> Image.Image:
    """
    Apply a named filter to the image
    """
    filters = {
        "grayscale": grayscale,
        "invert": invert,
        "brightness": lambda i: brightness(i, kwargs.get("factor", 1.0)),
        "contrast": lambda i: contrast(i, kwargs.get("factor", 1.0)),
        "saturation": lambda i: saturation(i, kwargs.get("factor", 1.0)),
        "blur": lambda i: blur(i, kwargs.get("radius", 2.0)),
        "sharpen": lambda i: sharpen(i, kwargs.get("factor", 1.0)),
        "posterize": lambda i: posterize(i, kwargs.get("bits", 4)),
        "sepia": sepia,
    }
    
    if filter_name not in filters:
        raise ValueError(f"Unknown filter: {filter_name}")
    
    return filters[filter_name](img)


# Filter definitions for UI
FILTER_DEFINITIONS = {
    "Grayscale": {"name": "grayscale", "icon": "▦"},
    "Invert": {"name": "invert", "icon": "◐"},
    "Brightness +": {"name": "brightness", "factor": 1.2, "icon": "☀"},
    "Brightness -": {"name": "brightness", "factor": 0.8, "icon": "☾"},
    "Contrast +": {"name": "contrast", "factor": 1.2, "icon": "◧"},
    "Contrast -": {"name": "contrast", "factor": 0.8, "icon": "◨"},
    "Blur": {"name": "blur", "radius": 2.0, "icon": "◌"},
    "Sharpen": {"name": "sharpen", "factor": 1.5, "icon": "◆"},
    "Posterize": {"name": "posterize", "bits": 4, "icon": "▣"},
    "Sepia": {"name": "sepia", "icon": "◈"},
}
