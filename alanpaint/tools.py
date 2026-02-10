"""
Drawing tools module for AlanPaint
Implements brush, eraser, shapes, and text tools
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtGui import QColor


class Tool(ABC):
    """Abstract base class for drawing tools"""
    
    @abstractmethod
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        """Start drawing at position"""
        pass
    
    @abstractmethod
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        """Continue drawing to position, returns modified region if any"""
        pass
    
    @abstractmethod
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        """Finish drawing at position, returns final modified region"""
        pass
    
    @abstractmethod
    def get_cursor_pos(self) -> Tuple[int, int]:
        """Get current cursor position"""
        pass


class BrushTool(Tool):
    """Freehand brush tool"""
    
    def __init__(self):
        self._start_x = 0
        self._start_y = 0
        self._last_x = 0
        self._last_y = 0
        self._color: Tuple[int, int, int] = (0, 0, 0)
        self._brush_size = 1
        self._image: Optional[Image.Image] = None
        self._draw: Optional[ImageDraw.ImageDraw] = None
    
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        self._start_x = x
        self._start_y = y
        self._last_x = x
        self._last_y = y
        self._color = color
        self._brush_size = brush_size
        self._image = None
    
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        if self._image is None:
            # Initialize a small image around the stroke
            margin = self._brush_size * 2
            self._image = Image.new("RGB", (margin * 2 + 1, margin * 2 + 1), 
                                    (255, 255, 255))
            self._draw = ImageDraw.Draw(self._image)
        
        # Draw line from last position to current
        self._draw.line(
            [(self._last_x - self._start_x + self._brush_size, 
              self._last_y - self._start_y + self._brush_size),
             (x - self._start_x + self._brush_size, 
              y - self._start_y + self._brush_size)],
            fill=self._color,
            width=self._brush_size
        )
        
        self._last_x = x
        self._last_y = y
        return self._image
    
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        self.move(x, y)
        return self._image
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        return (self._last_x, self._last_y)


class EraserTool(Tool):
    """Eraser tool (brush with white color)"""
    
    def __init__(self):
        self._brush = BrushTool()
    
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        self._brush.start(x, y, (255, 255, 255), brush_size)
    
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        return self._brush.move(x, y)
    
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        return self._brush.end(x, y)
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        return self._brush.get_cursor_pos()


class LineTool(Tool):
    """Line drawing tool"""
    
    def __init__(self):
        self._start_x = 0
        self._start_y = 0
        self._color: Tuple[int, int, int] = (0, 0, 0)
        self._brush_size = 1
    
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        self._start_x = x
        self._start_y = y
        self._color = color
        self._brush_size = brush_size
    
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        # Calculate bounding box
        min_x = min(self._start_x, x) - self._brush_size
        min_y = min(self._start_y, y) - self._brush_size
        max_x = max(self._start_x, x) + self._brush_size
        max_y = max(self._start_y, y) + self._brush_size
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        if width <= 0 or height <= 0:
            return None
        
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw line
        draw.line(
            [(self._start_x - min_x, self._start_y - min_y), 
             (x - min_x, y - min_y)],
            fill=self._color,
            width=self._brush_size
        )
        
        return img
    
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        return self.move(x, y)
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        return (self._start_x, self._start_y)
    
    @property
    def region(self) -> Tuple[int, int, int, int]:
        """Get the bounding box of the line"""
        min_x = min(self._start_x, self._last_x) - self._brush_size if hasattr(self, '_last_x') else self._start_x
        min_y = min(self._start_y, self._last_y) - self._brush_size if hasattr(self, '_last_y') else self._start_y
        max_x = max(self._start_x, self._last_x) + self._brush_size if hasattr(self, '_last_x') else self._start_x
        max_y = max(self._start_y, self._last_y) + self._brush_size if hasattr(self, '_last_y') else self._start_y
        return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


class RectangleTool(Tool):
    """Rectangle drawing tool"""
    
    def __init__(self, filled: bool = False):
        self._start_x = 0
        self._start_y = 0
        self._color: Tuple[int, int, int] = (0, 0, 0)
        self._brush_size = 1
        self._filled = filled
        self._last_x = 0
        self._last_y = 0
    
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        self._start_x = x
        self._start_y = y
        self._last_x = x
        self._last_y = y
        self._color = color
        self._brush_size = brush_size
    
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        self._last_x = x
        self._last_y = y
        
        # Calculate bounding box
        min_x = min(self._start_x, x) - self._brush_size
        min_y = min(self._start_y, y) - self._brush_size
        max_x = max(self._start_x, x) + self._brush_size
        max_y = max(self._start_y, y) + self._brush_size
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        if width <= 0 or height <= 0:
            return None
        
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        rect = (self._brush_size, self._brush_size, 
                width - self._brush_size, height - self._brush_size)
        
        if self._filled:
            draw.rectangle(rect, fill=self._color, outline=self._color)
        else:
            draw.rectangle(rect, fill=None, outline=self._color, 
                          width=self._brush_size)
        
        return img
    
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        return self.move(x, y)
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        return (self._last_x, self._last_y)


class EllipseTool(Tool):
    """Ellipse drawing tool"""
    
    def __init__(self, filled: bool = False):
        self._start_x = 0
        self._start_y = 0
        self._color: Tuple[int, int, int] = (0, 0, 0)
        self._brush_size = 1
        self._filled = filled
        self._last_x = 0
        self._last_y = 0
    
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        self._start_x = x
        self._start_y = y
        self._last_x = x
        self._last_y = y
        self._color = color
        self._brush_size = brush_size
    
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        self._last_x = x
        self._last_y = y
        
        # Calculate bounding box
        min_x = min(self._start_x, x) - self._brush_size
        min_y = min(self._start_y, y) - self._brush_size
        max_x = max(self._start_x, x) + self._brush_size
        max_y = max(self._start_y, y) + self._brush_size
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        if width <= 0 or height <= 0:
            return None
        
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        ellipse = (self._brush_size, self._brush_size, 
                   width - self._brush_size, height - self._brush_size)
        
        if self._filled:
            draw.ellipse(ellipse, fill=self._color, outline=self._color)
        else:
            draw.ellipse(ellipse, fill=None, outline=self._color, 
                        width=self._brush_size)
        
        return img
    
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        return self.move(x, y)
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        return (self._last_x, self._last_y)


class TextTool(Tool):
    """Text insertion tool"""
    
    def __init__(self):
        self._x = 0
        self._y = 0
        self._color: Tuple[int, int, int] = (0, 0, 0)
        self._font_size = 16
        self._text = ""
    
    def start(self, x: int, y: int, color: Tuple[int, int, int], 
              brush_size: int) -> None:
        self._x = x
        self._y = y
        self._color = color
        self._font_size = brush_size * 4  # Scale font with brush size
    
    def move(self, x: int, y: int) -> Optional[Image.Image]:
        return None
    
    def end(self, x: int, y: int) -> Optional[Image.Image]:
        return None
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        return (self._x, self._y)
    
    def set_text(self, text: str) -> None:
        """Set the text to insert"""
        self._text = text
    
    def create_text_image(self, font: ImageFont.ImageFont = None) -> Optional[Image.Image]:
        """Create an image with the text"""
        if not self._text:
            return None
        
        try:
            if font is None:
                font = ImageFont.load_default()
            
            # Get text size
            bbox = font.getbbox(self._text)
            width = bbox[2] - bbox[0] + 4
            height = bbox[3] - bbox[1] + 4
            
            img = Image.new("RGB", (width, height), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            draw.text((2, 2), self._text, fill=self._color, font=font)
            
            return img
        except Exception:
            return None


# Tool factory
def create_tool(tool_type: str, filled: bool = False) -> Tool:
    """
    Create a tool by type name
    """
    tools = {
        "brush": BrushTool,
        "eraser": EraserTool,
        "line": LineTool,
        "rectangle": lambda: RectangleTool(filled),
        "ellipse": lambda: EllipseTool(filled),
        "text": TextTool,
    }
    
    if tool_type not in tools:
        raise ValueError(f"Unknown tool: {tool_type}")
    
    return tools[tool_type]()


# Tool names for UI
TOOL_NAMES = {
    "brush": "Brush",
    "eraser": "Eraser",
    "line": "Line",
    "rectangle": "Rectangle",
    "ellipse": "Ellipse",
    "text": "Text",
}

# Default tool
DEFAULT_TOOL = "brush"
