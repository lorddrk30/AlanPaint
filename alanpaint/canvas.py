"""
Canvas module for AlanPaint
Custom widget with efficient rendering and overlay system for low RAM usage
"""

from typing import Optional, Tuple, Dict, Any
from PIL import Image
from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QCursor, QKeyEvent


class Canvas(QWidget):
    """
    Main canvas widget with overlay system for efficient drawing
    Uses single master image + preview cache approach for low RAM
    """
    
    # Signals
    image_modified = Signal()  # Emitted when image is modified
    zoom_changed = Signal(float)  # Emitted when zoom level changes
    cursor_moved = Signal(int, int)  # Emitted when cursor moves (image coords)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Master image (full resolution) - only one copy
        self._master_image: Optional[Image.Image] = None
        
        # Preview cache (scaled for display)
        self._preview_cache: Optional[QPixmap] = None
        self._preview_scale: float = 1.0
        
        # Overlay for temporary drawing (transparent layer during drag)
        self._overlay: Optional[QImage] = None
        self._overlay_visible = False
        
        # Current tool state
        self._current_tool = None
        self._tool_color = (0, 0, 0)  # RGB tuple
        self._brush_size = 5
        self._is_drawing = False
        
        # Zoom and pan
        self._zoom = 1.0
        self._offset_x = 0
        self._offset_y = 0
        
        # Panning state
        self._is_panning = False
        self._pan_start = QPoint()
        self._offset_start = QPoint()
        
        # Dirty flag - preview needs update
        self._preview_dirty = True
        
        # Mouse position tracking
        self._last_mouse_pos = None
        
        # Setup widget
        self.setMinimumSize(400, 300)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
    
    # ==================== Image Management ====================
    
    def set_image(self, image: Image.Image) -> None:
        """Set the master image"""
        self._master_image = image.copy() if image else None
        self._preview_cache = None
        self._preview_dirty = True
        self.update()
    
    def get_image(self) -> Optional[Image.Image]:
        """Get the master image"""
        return self._master_image
    
    def get_image_size(self) -> Tuple[int, int]:
        """Get current image dimensions"""
        if self._master_image:
            return (self._master_image.width, self._master_image.height)
        return (0, 0)
    
    # ==================== Preview Cache ====================
    
    def _update_preview_cache(self) -> None:
        """Update the preview cache scaled for viewport"""
        if self._master_image is None:
            self._preview_cache = None
            return
        
        # Get viewport size
        viewport_size = self.size()
        
        # Calculate scaled size
        img_w, img_h = self._master_image.width, self._master_image.height
        
        if viewport_size.width() > 0 and viewport_size.height() > 0:
            # Scale to fit viewport while maintaining aspect ratio
            scale_w = viewport_size.width() / img_w
            scale_h = viewport_size.height() / img_h
            scale = min(scale_w, scale_h, 1.0)  # Don't scale up
            
            scaled_w = int(img_w * scale)
            scaled_h = int(img_h * scale)
        else:
            scaled_w = img_w
            scaled_h = img_h
        
        # Scale image using Pillow (efficient)
        if scale != 1.0:
            scaled_image = self._master_image.resize(
                (scaled_w, scaled_h), 
                Image.Resampling.LANCZOS
            )
        else:
            scaled_image = self._master_image
        
        # Convert to QPixmap
        from alanpaint.io import pil_to_qimage
        qimage = pil_to_qimage(scaled_image)
        self._preview_cache = QPixmap.fromImage(qimage)
        self._preview_scale = scale
        
        self._preview_dirty = False
    
    def get_preview_pixmap(self) -> Optional[QPixmap]:
        """Get the preview pixmap for display"""
        if self._preview_dirty:
            self._update_preview_cache()
        return self._preview_cache
    
    # ==================== Coordinate Conversion ====================
    
    def display_to_image(self, x: int, y: int) -> Tuple[int, int]:
        """Convert display coordinates to image coordinates"""
        if self._preview_cache is None:
            return (0, 0)
        
        # Account for centering
        px = (self.width() - self._preview_cache.width()) // 2 + self._offset_x
        py = (self.height() - self._preview_cache.height()) // 2 + self._offset_y
        
        img_x = int((x - px) / self._preview_scale)
        img_y = int((y - py) / self._preview_scale)
        
        # Clamp to image bounds
        if self._master_image:
            img_x = max(0, min(img_x, self._master_image.width - 1))
            img_y = max(0, min(img_y, self._master_image.height - 1))
        
        return (img_x, img_y)
    
    def image_to_display(self, x: int, y: int) -> Tuple[int, int]:
        """Convert image coordinates to display coordinates"""
        if self._preview_cache is None:
            return (0, 0)
        
        px = (self.width() - self._preview_cache.width()) // 2 + self._offset_x
        py = (self.height() - self._preview_cache.height()) // 2 + self._offset_y
        
        dx = int(x * self._preview_scale + px)
        dy = int(y * self._preview_scale + py)
        
        return (dx, dy)
    
    # ==================== Drawing Tools ====================
    
    def set_tool(self, tool) -> None:
        """Set the current drawing tool"""
        self._current_tool = tool
    
    def set_color(self, color: Tuple[int, int, int]) -> None:
        """Set the current brush color"""
        self._tool_color = color
    
    def set_brush_size(self, size: int) -> None:
        """Set the brush size"""
        self._brush_size = max(1, min(100, size))
    
    def set_zoom(self, zoom: float) -> None:
        """Set zoom level"""
        self._zoom = max(0.1, min(10.0, zoom))
        self._preview_dirty = True
        self.update()
        self.zoom_changed.emit(self._zoom)
    
    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self._zoom
    
    def zoom_in(self) -> None:
        """Zoom in"""
        self.set_zoom(self._zoom * 1.25)
    
    def zoom_out(self) -> None:
        """Zoom out"""
        self.set_zoom(self._zoom / 1.25)
    
    def zoom_fit(self) -> None:
        """Fit image to viewport"""
        if self._master_image is None:
            return
        
        viewport_w = self.width() - 20
        viewport_h = self.height() - 20
        
        scale_w = viewport_w / self._master_image.width
        scale_h = viewport_h / self._master_image.height
        
        zoom = min(scale_w, scale_h, 1.0)
        self.set_zoom(zoom)
    
    def zoom_100(self) -> None:
        """Set 100% zoom"""
        self.set_zoom(1.0)
    
    # ==================== Pan ====================
    
    def pan(self, dx: int, dy: int) -> None:
        """Pan the canvas"""
        self._offset_x += dx
        self._offset_y += dy
        self.update()
    
    # ==================== Overlay Management ====================
    
    def _create_overlay(self) -> None:
        """Create overlay matching preview cache size"""
        if self._preview_cache:
            self._overlay = QImage(
                self._preview_cache.size(),
                QImage.Format_ARGB32
            )
            self._overlay.fill(Qt.transparent)
    
    def _clear_overlay(self) -> None:
        """Clear the overlay"""
        if self._overlay:
            self._overlay.fill(Qt.transparent)
            self._overlay_visible = False
    
    def _update_overlay(self, modified_region: Image.Image, 
                        region: Tuple[int, int, int, int]) -> None:
        """Update overlay with modified region"""
        if self._overlay is None:
            self._create_overlay()
        
        # Convert PIL region to QImage and draw to overlay
        from alanpaint.io import pil_to_qimage
        
        x, y, w, h = region
        
        # Scale region to overlay coordinates
        ox = int(x * self._preview_scale)
        oy = int(y * self._preview_scale)
        ow = int(w * self._preview_scale)
        oh = int(h * self._preview_scale)
        
        # Convert PIL image to QImage
        qimg = pil_to_qimage(modified_region)
        
        # Draw scaled version to overlay
        painter = QPainter(self._overlay)
        painter.drawImage(ox, oy, qimg.scaled(ow, oh, Qt.KeepAspectRatio, Qt.FastTransformation))
        painter.end()
        
        self._overlay_visible = True
        self.update()
    
    # ==================== Drawing Operations ====================
    
    def _commit_drawing(self, modified_region: Image.Image, 
                        region: Tuple[int, int, int, int]) -> None:
        """Commit drawing to master image"""
        if self._master_image is None:
            return
        
        x, y, w, h = region
        
        # Ensure bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, self._master_image.width - x)
        h = min(h, self._master_image.height - y)
        
        if w <= 0 or h <= 0:
            return
        
        # Paste modified region to master
        self._master_image.paste(modified_region, (x, y))
        
        # Mark preview as dirty
        self._preview_dirty = True
        self.update()
        
        # Emit signal
        self.image_modified.emit()
    
    # ==================== Mouse Events ====================
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press"""
        if event.button() == Qt.MiddleButton or \
           (event.button() == Qt.LeftButton and self._current_tool is None):
            # Start panning
            self._is_panning = True
            self._pan_start = event.pos()
            self._offset_start = QPoint(self._offset_x, self._offset_y)
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            return
        
        if self._current_tool is None or self._master_image is None:
            return
        
        # Start drawing
        x, y = self.display_to_image(event.pos().x(), event.pos().y())
        self._is_drawing = True
        
        self._current_tool.start(x, y, self._tool_color, self._brush_size)
        self._clear_overlay()
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move"""
        # Handle panning
        if self._is_panning:
            dx = event.pos().x() - self._pan_start.x()
            dy = event.pos().y() - self._pan_start.y()
            self._offset_x = self._offset_start.x() + dx
            self._offset_y = self._offset_start.y() + dy
            self.update()
            return
        
        # Track cursor position for status bar
        x, y = self.display_to_image(event.pos().x(), event.pos().y())
        self.cursor_moved.emit(x, y)
        self._last_mouse_pos = event.pos()
        
        # Handle drawing
        if self._is_drawing and self._current_tool:
            x, y = self.display_to_image(event.pos().x(), event.pos().y())
            
            modified = self._current_tool.move(x, y)
            
            if modified:
                # Get region from tool
                region = getattr(self._current_tool, 'region', 
                                (0, 0, modified.width, modified.height))
                self._update_overlay(modified, region)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release"""
        if self._is_panning:
            self._is_panning = False
            self.setCursor(QCursor(Qt.CrossCursor))
            return
        
        if not self._is_drawing or not self._current_tool:
            return
        
        # Finish drawing and commit
        x, y = self.display_to_image(event.pos().x(), event.pos().y())
        modified = self._current_tool.end(x, y)
        
        if modified:
            region = getattr(self._current_tool, 'region',
                            (0, 0, modified.width, modified.height))
            self._commit_drawing(modified, region)
        
        self._clear_overlay()
        self._is_drawing = False
    
    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for zoom"""
        if event.modifiers() == Qt.ControlModifier:
            # Zoom with Ctrl+wheel
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Pan with wheel (horizontal) or scroll
            if event.angleDelta().x() != 0:
                self.pan(-event.angleDelta().x() // 4, 0)
            if event.angleDelta().y() != 0:
                self.pan(0, -event.angleDelta().y() // 4)
    
    # ==================== Painting ====================
    
    def paintEvent(self, event) -> None:
        """Custom paint event for efficient rendering"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(64, 64, 64))
        
        # Update preview if needed
        if self._preview_dirty:
            self._update_preview_cache()
        
        # Draw preview
        if self._preview_cache and self._master_image:
            # Center the preview
            x = (self.width() - self._preview_cache.width()) // 2 + self._offset_x
            y = (self.height() - self._preview_cache.height()) // 2 + self._offset_y
            
            painter.drawPixmap(x, y, self._preview_cache)
        
        # Draw overlay (for temporary drawing)
        if self._overlay_visible and self._overlay:
            x = (self.width() - self._overlay.width()) // 2 + self._offset_x
            y = (self.height() - self._overlay.height()) // 2 + self._offset_y
            painter.drawImage(x, y, self._overlay)
        
        # Draw cursor crosshair
        if self._last_mouse_pos and not self._is_panning:
            mx, my = self._last_mouse_pos.x(), self._last_mouse_pos.y()
            painter.setPen(QColor(128, 128, 128, 128))
            painter.drawLine(mx - 10, my, mx + 10, my)
            painter.drawLine(mx, my - 10, mx, my + 10)
    
    # ==================== Keyboard Events ====================
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Space:
            # Space for temporary pan
            if not self._is_panning:
                self._is_panning = True
                self._pan_start = self.mapFromGlobal(QCursor.pos())
                self._offset_start = QPoint(self._offset_x, self._offset_y)
                self.setCursor(QCursor(Qt.OpenHandCursor))
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release"""
        if event.key() == Qt.Key_Space and self._is_panning:
            self._is_panning = False
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            super().keyReleaseEvent(event)
