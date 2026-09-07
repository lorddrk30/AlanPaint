"""Pillow filters shared by thumbnails, previews and full-resolution edits."""
from PIL import ImageEnhance, ImageFilter, ImageOps


def apply_filter(img, filter_name, **kwargs):
    alpha = img.getchannel("A") if img.mode == "RGBA" else None
    rgb = img.convert("RGB")
    factor = kwargs.get("factor", 1.0)
    filters = {
        "original": lambda: rgb,
        "grayscale": lambda: ImageOps.grayscale(rgb).convert("RGB"),
        "invert": lambda: ImageOps.invert(rgb),
        "brightness": lambda: ImageEnhance.Brightness(rgb).enhance(factor),
        "contrast": lambda: ImageEnhance.Contrast(rgb).enhance(factor),
        "saturation": lambda: ImageEnhance.Color(rgb).enhance(factor),
        "blur": lambda: rgb.filter(ImageFilter.GaussianBlur(kwargs.get("radius", 2.0))),
        "sharpen": lambda: ImageEnhance.Sharpness(rgb).enhance(kwargs.get("factor", 2.0)),
        "posterize": lambda: ImageOps.posterize(rgb, kwargs.get("bits", 4)),
        "sepia": lambda: ImageOps.colorize(ImageOps.grayscale(rgb), "#30201b", "#f3dfb5"),
        "auto_contrast": lambda: ImageOps.autocontrast(rgb, cutoff=1),
    }
    if filter_name not in filters:
        raise ValueError(f"Filtro desconocido: {filter_name}")
    result = filters[filter_name]()
    if alpha is not None:
        result.putalpha(alpha)
    return result


def apply_adjustments(img, brightness=100, contrast=100, saturation=100):
    for name, value in [("brightness", brightness), ("contrast", contrast), ("saturation", saturation)]:
        if value != 100:
            img = apply_filter(img, name, factor=value / 100)
    return img


FILTER_DEFINITIONS = {
    "Original": {"name": "original"},
    "Blanco y negro": {"name": "grayscale"},
    "Sepia": {"name": "sepia"},
    "Invertir": {"name": "invert"},
    "Suave": {"name": "blur", "radius": 2.0},
    "Nítido": {"name": "sharpen", "factor": 2.0},
    "Póster": {"name": "posterize", "bits": 3},
    "Auto contraste": {"name": "auto_contrast"},
}
