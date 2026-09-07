"""Viewport canvas with zoom, transparent drawing patches and crop overlay."""
import math
from PIL import Image
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import QWidget
from alanpaint.io import pil_to_qimage
from alanpaint.tools import BrushTool, TextTool
from alanpaint.commands import DrawCommand


class Canvas(QWidget):
    image_modified = Signal()
    command_requested = Signal(object)
    zoom_changed = Signal(float)
    cursor_moved = Signal(int, int)
    crop_changed = Signal(object)
    crop_accepted = Signal()
    crop_cancelled = Signal()
    color_picked = Signal(object)
    text_requested = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 240)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self._master_image = None
        self._display_image = None
        self._preview_active = False
        self._patch = None
        self._current_tool = BrushTool()
        self._tool_id = "brush"
        self._tool_color = (35, 38, 51)
        self._brush_size = 8
        self._zoom = 1.0
        self._fit_mode = True
        self._offset = QPointF()
        self._space = self._is_panning = self._is_drawing = False
        self._last_mouse_pos = None
        self.crop_rect = None
        self.crop_ratio = None
        self.setCursor(Qt.CrossCursor)

    def set_image(self, image):
        # Commands depend on stable image identity. Ownership passes to canvas.
        self._master_image = image
        self.cancel_interaction()
        self.refresh()

    def get_image(self):
        return self._master_image

    def get_image_size(self):
        return self._master_image.size if self._master_image else (0, 0)

    def refresh(self):
        self._preview_active = False
        self._display_image = pil_to_qimage(self._master_image) if self._master_image else None
        self.update()

    def set_preview(self, image):
        self._preview_active = True
        self._display_image = pil_to_qimage(image)
        self.update()

    def image_rect(self):
        w, h = self.get_image_size()
        w, h = w*self._zoom, h*self._zoom
        return QRectF((self.width()-w)/2+self._offset.x(),
                      (self.height()-h)/2+self._offset.y(), w, h)

    def display_to_image(self, x, y, boundary=False):
        rect = self.image_rect()
        w, h = self.get_image_size()
        limit = 0 if boundary else 1
        return (max(0, min(w-limit, math.floor((x-rect.x()) / self._zoom))),
                max(0, min(h-limit, math.floor((y-rect.y()) / self._zoom))))

    def image_to_display(self, x, y):
        rect = self.image_rect()
        return (round(rect.x()+x*self._zoom), round(rect.y()+y*self._zoom))

    def set_tool(self, tool, tool_id=None):
        self.cancel_interaction()
        self._current_tool = tool
        self._tool_id = tool_id or type(tool).__name__.replace("Tool", "").lower()
        self.setCursor(Qt.OpenHandCursor if self._tool_id == "hand" else Qt.CrossCursor)

    def set_color(self, color):
        self._tool_color = color

    def set_brush_size(self, size):
        self._brush_size = size

    def set_zoom(self, zoom, anchor=None):
        self._fit_mode = False
        old = self._zoom
        self._zoom = max(0.01, min(16.0, zoom))
        if anchor is not None:
            center = QPointF(self.width()/2, self.height()/2)
            self._offset = anchor-center-(anchor-center-self._offset)*(self._zoom/old)
        self.zoom_changed.emit(self._zoom)
        self.update()

    def get_zoom(self):
        return self._zoom

    def zoom_in(self):
        self.set_zoom(self._zoom*1.25)

    def zoom_out(self):
        self.set_zoom(self._zoom/1.25)

    def zoom_100(self):
        self._offset = QPointF()
        self.set_zoom(1)

    def zoom_fit(self):
        w, h = self.get_image_size()
        if w and h:
            self._offset = QPointF()
            self.set_zoom(min(max(1, self.width()-80)/w, max(1, self.height()-80)/h, 1))
            self._fit_mode = True

    def resizeEvent(self, event):
        if self._fit_mode:
            self.zoom_fit()
        super().resizeEvent(event)

    def cancel_interaction(self):
        self._patch = None
        self._is_drawing = self._is_panning = False
        self.crop_rect = None
        self.crop_changed.emit(None)
        self.update()

    def set_crop_ratio(self, ratio):
        self.crop_ratio = ratio
        self.cancel_interaction()

    def _update_crop(self, x, y):
        sx, sy = self._crop_start
        dx, dy = x-sx, y-sy
        width, height = abs(dx), abs(dy)
        if self.crop_ratio:
            # Constrain the rectangle inside the pointer's bounding box.
            if height and width/height > self.crop_ratio:
                width = round(height*self.crop_ratio)
            else:
                height = round(width/self.crop_ratio)
        ex, ey = sx + (width if dx >= 0 else -width), sy + (height if dy >= 0 else -height)
        self.crop_rect = (min(sx, ex), min(sy, ey), max(sx, ex), max(sy, ey)) if width and height else None
        self.crop_changed.emit(self.crop_rect)
        self.update()

    def commit_patch(self, patch, region):
        if patch is None or self._master_image is None:
            return
        x, y, w, h = region
        left, top = max(0, x), max(0, y)
        right, bottom = min(self._master_image.width, x+w), min(self._master_image.height, y+h)
        if right <= left or bottom <= top:
            return
        patch = patch.crop((left-x, top-y, right-x, bottom-y)).convert("RGBA")
        before = self._master_image.crop((left, top, right, bottom))
        after = Image.alpha_composite(before.convert("RGBA"), patch).convert(self._master_image.mode)
        if before.tobytes() != after.tobytes():
            self.command_requested.emit(DrawCommand(self._master_image, after, (left, top, right-left, bottom-top)))

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and (self._space or self._tool_id == "hand")):
            self._is_panning = True
            self._pan_start, self._offset_start = event.position(), QPointF(self._offset)
            self.setCursor(Qt.ClosedHandCursor)
            return
        if event.button() != Qt.LeftButton or self._master_image is None or self._preview_active:
            return
        if not self.image_rect().contains(event.position()):
            return
        x, y = self.display_to_image(event.position().x(), event.position().y(), self._tool_id == "crop")
        if self._tool_id == "picker":
            self.color_picked.emit(self._master_image.getpixel((x, y))[:3])
        elif self._tool_id == "text":
            self.text_requested.emit(x, y)
        elif self._tool_id == "crop":
            self._crop_start = (x, y)
            self._is_drawing = True
            self._update_crop(x, y)
        elif self._current_tool:
            self._is_drawing = True
            self._current_tool.start(x, y, self._tool_color, self._brush_size)
            self._patch = self._current_tool.move(x, y)
            self.update()

    def mouseMoveEvent(self, event):
        if self._is_panning:
            self._offset = self._offset_start + event.position()-self._pan_start
            self.update()
            return
        self._last_mouse_pos = event.position()
        if self._master_image is None:
            return
        x, y = self.display_to_image(event.position().x(), event.position().y(), self._tool_id == "crop")
        self.cursor_moved.emit(x, y)
        if self._is_drawing:
            if self._tool_id == "crop":
                self._update_crop(x, y)
            elif self._current_tool:
                self._patch = self._current_tool.move(x, y)
        self.update()

    def mouseReleaseEvent(self, event):
        if self._is_panning:
            if event.button() in (Qt.LeftButton, Qt.MiddleButton):
                self._is_panning = False
                self.setCursor(Qt.OpenHandCursor if self._space or self._tool_id == "hand" else Qt.CrossCursor)
            return
        if event.button() != Qt.LeftButton or not self._is_drawing:
            return
        x, y = self.display_to_image(event.position().x(), event.position().y(), self._tool_id == "crop")
        self._is_drawing = False
        if self._tool_id == "crop":
            self._update_crop(x, y)
        elif self._current_tool:
            patch = self._current_tool.end(x, y)
            self._patch = None
            self.commit_patch(patch, self._current_tool.region)
        self.update()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.set_zoom(self._zoom*(1.2 if event.angleDelta().y() > 0 else 1/1.2), event.position())
        else:
            self._offset += QPointF(event.angleDelta().x()/3, event.angleDelta().y()/3)
            self.update()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self._space = True
            self.setCursor(Qt.OpenHandCursor)
        elif event.key() == Qt.Key_Escape:
            self.cancel_interaction()
            self.crop_cancelled.emit()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self._tool_id == "crop":
            self.crop_accepted.emit()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space = False
            self.setCursor(Qt.OpenHandCursor if self._tool_id == "hand" else Qt.CrossCursor)
        else:
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        self._space = False
        if self._is_drawing:
            self.cancel_interaction()
        self._is_panning = False
        super().focusOutEvent(event)

    def leaveEvent(self, event):
        self._last_mouse_pos = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#edeef3"))
        painter.setPen(QColor("#d8dbe5"))
        for x in range(16, self.width(), 24):
            for y in range(16, self.height(), 24):
                painter.drawPoint(x, y)
        if self._display_image is None:
            return
        rect = self.image_rect()
        painter.fillRect(rect.translated(0, 5).adjusted(-3, -3, 3, 3), QColor(32, 35, 55, 12))
        painter.fillRect(rect, QColor("white"))
        painter.save()
        painter.setClipRect(rect)
        if self._master_image.mode == "RGBA":
            visible = rect.intersected(QRectF(self.rect()))
            for x in range(int(visible.left())//12*12, int(visible.right())+12, 12):
                for y in range(int(visible.top())//12*12, int(visible.bottom())+12, 12):
                    if (x//12+y//12) % 2 == 0:
                        painter.fillRect(x, y, 12, 12, QColor("#e5e7eb"))
        painter.setRenderHint(QPainter.SmoothPixmapTransform, self._zoom < 2)
        painter.drawImage(rect, self._display_image)
        if self._patch is not None:
            x, y, w, h = self._current_tool.region
            painter.drawImage(QRectF(rect.x()+x*self._zoom, rect.y()+y*self._zoom, w*self._zoom, h*self._zoom), pil_to_qimage(self._patch))
        if self.crop_rect:
            x1, y1, x2, y2 = self.crop_rect
            selection = QRectF(rect.x()+x1*self._zoom, rect.y()+y1*self._zoom, (x2-x1)*self._zoom, (y2-y1)*self._zoom)
            shade = QPainterPath()
            shade.addRect(rect)
            shade.addRect(selection)
            painter.fillPath(shade, QColor(20, 20, 40, 135))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawRect(selection)
            painter.setPen(QPen(QColor(255, 255, 255, 130), 1, Qt.DashLine))
            for n in (1, 2):
                xx, yy = selection.x()+selection.width()*n/3, selection.y()+selection.height()*n/3
                painter.drawLine(QPointF(xx, selection.top()), QPointF(xx, selection.bottom()))
                painter.drawLine(QPointF(selection.left(), yy), QPointF(selection.right(), yy))
            for point in (selection.topLeft(), selection.topRight(), selection.bottomLeft(), selection.bottomRight()):
                painter.fillRect(QRectF(point.x()-4, point.y()-4, 8, 8), QColor("#7760dc"))
        painter.restore()
        if self._last_mouse_pos and self._tool_id in ("brush", "eraser") and not self._preview_active:
            radius = max(2, self._brush_size*self._zoom/2)
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(self._last_mouse_pos, radius, radius)
            painter.setPen(QPen(QColor("#45405d"), 1))
            painter.drawEllipse(self._last_mouse_pos, radius, radius)
