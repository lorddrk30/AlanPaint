"""Drawing tools produce transparent patches in image coordinates."""
from PIL import Image, ImageDraw, ImageFont
import os


class BrushTool:
    def start(self, x, y, color, brush_size):
        self.points = [(x, y)]
        self.color = color
        self.size = brush_size

    def move(self, x, y):
        if self.points[-1] != (x, y):
            self.points.append((x, y))
        return self.render()

    def end(self, x, y):
        return self.move(x, y)

    def render(self):
        margin = self.size // 2 + 1
        xs, ys = zip(*self.points)
        left, top = min(xs) - margin, min(ys) - margin
        width, height = max(xs) - left + margin + 1, max(ys) - top + margin + 1
        self.region = (left, top, width, height)
        patch = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(patch)
        points = [(x - left, y - top) for x, y in self.points]
        draw.line(points, fill=self.color, width=self.size, joint="curve")
        radius = (self.size - 1) / 2
        for x, y in points:
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=self.color)
        return patch

    def get_cursor_pos(self):
        return self.points[-1]


class EraserTool(BrushTool):
    """White eraser, matching the paper background."""
    def start(self, x, y, color, brush_size):
        super().start(x, y, (255, 255, 255), brush_size)


class LineTool(BrushTool):
    shape = "line"

    def __init__(self, filled=False):
        self.filled = filled

    def move(self, x, y):
        self.points = [self.points[0], (x, y)]
        return self.render()

    def render(self):
        (x1, y1), (x2, y2) = self.points[0], self.points[-1]
        margin = self.size
        left, top = min(x1, x2) - margin, min(y1, y2) - margin
        width, height = abs(x2-x1) + 2*margin + 1, abs(y2-y1) + 2*margin + 1
        self.region = (left, top, width, height)
        patch = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(patch)
        if self.shape == "line":
            draw.line([(x1-left, y1-top), (x2-left, y2-top)], fill=self.color, width=self.size)
        else:
            bounds = (margin, margin, width-margin-1, height-margin-1)
            getattr(draw, self.shape)(bounds, outline=self.color,
                                     fill=self.color if self.filled else None, width=self.size)
        return patch


class RectangleTool(LineTool):
    shape = "rectangle"


class EllipseTool(LineTool):
    shape = "ellipse"


class TextTool:
    def start(self, x, y, color, brush_size):
        self.x, self.y, self.color = x, y, color
        self.font_size = brush_size

    def set_text(self, text):
        self.text = text

    def create_text_image(self, font=None):
        if not getattr(self, "text", ""):
            return None
        if font is None:
            for name in [os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "segoeui.ttf"), "DejaVuSans.ttf"]:
                try:
                    font = ImageFont.truetype(name, self.font_size)
                    break
                except OSError:
                    continue
            else:
                font = ImageFont.load_default(size=self.font_size)
        measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        box = measure.multiline_textbbox((0, 0), self.text, font=font)
        width, height = max(1, box[2]-box[0]+4), max(1, box[3]-box[1]+4)
        patch = Image.new("RGBA", (width, height))
        ImageDraw.Draw(patch).multiline_text((2-box[0], 2-box[1]), self.text, font=font, fill=self.color)
        self.region = (self.x, self.y, width, height)
        return patch


def create_tool(tool_type, filled=False):
    return {"brush": BrushTool, "eraser": EraserTool, "line": LineTool,
            "rectangle": lambda: RectangleTool(filled),
            "ellipse": lambda: EllipseTool(filled), "text": TextTool}[tool_type]()


TOOL_NAMES = {"brush": "Pincel", "eraser": "Borrador", "line": "Línea",
              "rectangle": "Rectángulo", "ellipse": "Elipse", "text": "Texto",
              "crop": "Recortar", "picker": "Cuentagotas", "hand": "Mover"}
DEFAULT_TOOL = "brush"
