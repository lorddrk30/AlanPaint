"""
Demo image generator for AlanPaint
Creates a test image with various shapes and colors
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_demo_image(path: str = "demo.png", width: int = 800, height: int = 600) -> None:
    """Create a demo image with shapes and text"""
    
    # Create blank white image
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw background
    draw.rectangle([0, 0, width, height], fill=(240, 240, 240))
    
    # Draw some shapes
    # Red rectangle
    draw.rectangle([50, 50, 200, 150], fill=(220, 80, 80), outline=(0, 0, 0))
    
    # Green ellipse
    draw.ellipse([250, 50, 450, 200], fill=(80, 200, 80), outline=(0, 0, 0))
    
    # Blue circle
    draw.ellipse([500, 80, 600, 180], fill=(80, 80, 220), outline=(0, 0, 0))
    
    # Yellow triangle
    draw.polygon([(400, 250), (300, 400), (500, 400)], fill=(255, 220, 50))
    
    # Lines
    draw.line([(50, 450), (200, 550)], fill=(0, 0, 0), width=3)
    draw.line([(200, 450), (50, 550)], fill=(0, 0, 0), width=3)
    
    # Add some text
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((60, 420), "AlanPaint Demo", fill=(50, 50, 50), font=font)
    draw.text((60, 470), "Test Image", fill=(80, 80, 80), font=font)
    
    # Colorful circles pattern
    colors = [
        (255, 100, 100),  # Red
        (100, 255, 100),  # Green
        (100, 100, 255),  # Blue
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
        (100, 255, 255),  # Cyan
    ]
    
    for i, color in enumerate(colors):
        x = 600 + (i % 3) * 40
        y = 350 + (i // 3) * 40
        draw.ellipse([x, y, x + 30, y + 30], fill=color)
    
    # Save
    img.save(path, "PNG")
    print(f"Demo image saved to: {os.path.abspath(path)}")


if __name__ == "__main__":
    create_demo_image()
