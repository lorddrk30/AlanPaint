"""
UI module for AlanPaint
Main window with menus, toolbar, and canvas
"""

import os
from typing import Optional, Tuple
from PIL import Image
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QToolButton, QLabel, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QColorDialog, QSlider, QDialog, QDialogButtonBox,
    QVBoxLayout as DialogLayout, QFormLayout, QSpinBox, QComboBox,
    QMessageBox, QInputDialog, QLineEdit, QGraphicsView, QGraphicsScene,
    QGraphicsTextItem
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QColor, QFont, QKeySequence

from alanpaint.canvas import Canvas
from alanpaint.tools import BrushTool, EraserTool, LineTool, RectangleTool, EllipseTool, TextTool, TOOL_NAMES
from alanpaint.commands import CommandManager, DrawCommand, FilterCommand
from alanpaint.filters import apply_filter, FILTER_DEFINITIONS
from alanpaint.io import load_image, save_image, SUPPORTED_FORMATS


class MainWindow(QMainWindow):
    """Main window for AlanPaint application"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("AlanPaint")
        self.resize(1024, 768)
        
        # Data
        self._current_file: Optional[str] = None
        self._modified = False
        
        # Command manager for undo/redo
        self._command_manager = CommandManager(max_undo=20)
        
        # Current tool
        self._current_tool = BrushTool()
        self._tool_color = (0, 0, 0)
        self._brush_size = 5
        
        # Setup UI
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()
        
        # Connect signals
        self._connect_signals()
        
        # Create new blank image
        self._new_image(800, 600)
    
    # ==================== UI Setup ====================
    
    def _setup_menubar(self) -> None:
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self, shortcut=QKeySequence.New,
                            triggered=self._new_image)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open...", self, shortcut=QKeySequence.Open,
                             triggered=self._open_image)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save", self, shortcut=QKeySequence.Save,
                             triggered=self._save_image)
        save_action.setEnabled(False)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self, 
                                  shortcut=QKeySequence("Ctrl+Shift+S"),
                                  triggered=self._save_image_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self, shortcut=QKeySequence.Quit,
                             triggered=self.close)
        file_menu.addAction(exit_action)
        
        self._save_action = save_action
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self, shortcut=QKeySequence.Undo,
                             triggered=self._undo)
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self, shortcut=QKeySequence.Redo,
                             triggered=self._redo)
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)
        
        self._undo_action = undo_action
        self._redo_action = redo_action
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self, shortcut=QKeySequence("Ctrl++"),
                                 triggered=self._zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self, shortcut=QKeySequence("Ctrl+-"),
                                 triggered=self._zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_fit_action = QAction("&Fit to Window", self,
                                 triggered=self._zoom_fit)
        view_menu.addAction(zoom_fit_action)
        
        zoom_100_action = QAction("&100%", self,
                                 triggered=self._zoom_100)
        view_menu.addAction(zoom_100_action)
        
        # Filters menu
        filters_menu = menubar.addMenu("&Filters")
        
        for name, info in FILTER_DEFINITIONS.items():
            action = QAction(name, self, triggered=lambda checked, n=name, i=info: self._apply_filter(n, i))
            filters_menu.addAction(action)
        
        # Tools menu (for filled shapes)
        tools_menu = menubar.addMenu("&Tools")
        
        self._filled_action = QAction("&Filled Shapes", self, checkable=True)
        self._filled_action.setChecked(False)
        self._filled_action.toggled.connect(self._update_filled_shapes)
        tools_menu.addAction(self._filled_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self, triggered=self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self) -> None:
        """Setup tool bar"""
        toolbar = QToolBar("Tools")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Tool buttons
        tools = [
            ("brush", "Brush", "B"),
            ("eraser", "Eraser", "E"),
            ("line", "Line", "L"),
            ("rectangle", "Rectangle", "R"),
            ("ellipse", "Ellipse", "O"),
            ("text", "Text", "T"),
        ]
        
        self._tool_buttons = {}
        
        for tool_id, tooltip, shortcut in tools:
            btn = QToolButton()
            btn.setText(shortcut)
            btn.setToolTip(f"{tooltip} ({shortcut})")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tool_id: self._select_tool(t))
            toolbar.addWidget(btn)
            self._tool_buttons[tool_id] = btn
        
        # Select brush by default
        self._tool_buttons["brush"].setChecked(True)
        
        toolbar.addSeparator()
        
        # Color button
        self._color_btn = QToolButton()
        self._color_btn.setText("■")
        self._color_btn.setToolTip("Color")
        self._color_btn.setFixedSize(32, 32)
        self._color_btn.clicked.connect(self._select_color)
        self._update_color_button()
        toolbar.addWidget(self._color_btn)
        
        toolbar.addSeparator()
        
        # Brush size slider
        size_label = QLabel("Size:")
        toolbar.addWidget(size_label)
        
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setMinimum(1)
        self._size_slider.setMaximum(50)
        self._size_slider.setValue(5)
        self._size_slider.setFixedWidth(100)
        self._size_slider.valueChanged.connect(self._brush_size_changed)
        toolbar.addWidget(self._size_slider)
        
        self._size_label = QLabel("5")
        toolbar.addWidget(self._size_label)
    
    def _setup_central_widget(self) -> None:
        """Setup central widget with canvas and scroll area"""
        # Create scroll area
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create canvas
        self._canvas = Canvas()
        scroll_area.setWidget(self._canvas)
        
        # Set as central widget
        self.setCentralWidget(scroll_area)
    
    def _setup_statusbar(self) -> None:
        """Setup status bar"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # Image size label
        self._size_status = QLabel("0 x 0")
        statusbar.addPermanentWidget(self._size_status)
        
        # Zoom label
        self._zoom_status = QLabel("100%")
        statusbar.addPermanentWidget(self._zoom_status)
        
        # Tool label
        self._tool_status = QLabel("Brush")
        statusbar.addPermanentWidget(self._tool_status)
        
        # Position label
        self._pos_status = QLabel("0, 0")
        statusbar.addPermanentWidget(self._pos_status)
    
    def _connect_signals(self) -> None:
        """Connect canvas signals"""
        self._canvas.image_modified.connect(self._on_image_modified)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        self._canvas.cursor_moved.connect(self._on_cursor_moved)
    
    # ==================== Image Operations ====================
    
    def _new_image(self, width: int = 800, height: int = 600) -> None:
        """Create a new blank image"""
        from alanpaint.io import create_blank_image
        
        self._current_file = None
        self._modified = False
        
        # Create blank image
        img = create_blank_image(width, height, (255, 255, 255))
        self._canvas.set_image(img)
        
        # Reset command manager
        self._command_manager.clear()
        
        # Update UI
        self._update_title()
        self._update_status()
        self._update_undo_redo()
    
    def _open_image(self) -> None:
        """Open an image file"""
        # Build filter string
        filters = []
        for fmt, (desc, ext) in SUPPORTED_FORMATS.items():
            filters.append(desc)
        filters.append("All Files (*.*)")
        filter_str = ";;".join(filters)
        
        # Show file dialog
        path, selected_filter = QFileDialog.getOpenFileName(
            self, "Open Image", "", filter_str
        )
        
        if not path:
            return
        
        try:
            # Load image
            img = load_image(path)
            
            self._current_file = path
            self._modified = False
            
            # Set image to canvas
            self._canvas.set_image(img)
            
            # Reset command manager
            self._command_manager.clear()
            
            # Update UI
            self._update_title()
            self._update_status()
            self._update_undo_redo()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open image:\n{str(e)}")
    
    def _save_image(self) -> bool:
        """Save the current image"""
        if not self._current_file:
            return self._save_image_as()
        
        try:
            img = self._canvas.get_image()
            if img:
                save_image(img, self._current_file)
                self._modified = False
                self._update_title()
                return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")
        
        return False
    
    def _save_image_as(self) -> bool:
        """Save image with a new name/format"""
        # Build filter string
        filters = []
        for fmt, (desc, ext) in SUPPORTED_FORMATS.items():
            filters.append(desc)
        filters.append("All Files (*.*)")
        filter_str = ";;".join(filters)
        
        # Show file dialog
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Image As", "", filter_str
        )
        
        if not path:
            return False
        
        # Check format support
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_FORMATS:
            # Try to add appropriate extension
            if "png" in selected_filter.lower():
                path = path if path.endswith(".png") else path + ".png"
            elif "jpg" in selected_filter.lower():
                path = path if path.endswith(".jpg") else path + ".jpg"
            elif "webp" in selected_filter.lower():
                path = path if path.endswith(".webp") else path + ".webp"
        
        try:
            img = self._canvas.get_image()
            if img:
                save_image(img, path)
                self._current_file = path
                self._modified = False
                self._update_title()
                self._save_action.setEnabled(True)
                return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")
        
        return False
    
    # ==================== Tool Operations ====================
    
    def _select_tool(self, tool_id: str) -> None:
        """Select a drawing tool"""
        tools = {
            "brush": BrushTool,
            "eraser": EraserTool,
            "line": LineTool,
            "rectangle": lambda: RectangleTool(self._filled_action.isChecked()),
            "ellipse": lambda: EllipseTool(self._filled_action.isChecked()),
            "text": TextTool,
        }
        
        if tool_id not in tools:
            return
        
        self._current_tool = tools[tool_id]()
        self._canvas.set_tool(self._current_tool)
        
        # Update button states
        for tid, btn in self._tool_buttons.items():
            btn.setChecked(tid == tool_id)
        
        # Update status
        self._tool_status.setText(TOOL_NAMES.get(tool_id, tool_id))
    
    def _update_filled_shapes(self, checked: bool) -> None:
        """Update shape tools for filled mode"""
        # Recreate current shape tool if needed
        tool_name = type(self._current_tool).__name__
        if tool_name in ("RectangleTool", "EllipseTool"):
            self._select_tool(tool_name.lower().replace("tool", ""))
    
    def _select_color(self) -> None:
        """Open color dialog"""
        color = QColorDialog.getColor(
            QColor(*self._tool_color), 
            self, 
            "Select Color"
        )
        
        if color.isValid():
            self._tool_color = (color.red(), color.green(), color.blue())
            self._update_color_button()
    
    def _update_color_button(self) -> None:
        """Update color button appearance"""
        self._color_btn.setStyleSheet(
            f"background-color: rgb({self._tool_color[0]}, "
            f"{self._tool_color[1]}, {self._tool_color[2]});"
        )
    
    def _brush_size_changed(self, value: int) -> None:
        """Handle brush size change"""
        self._brush_size = value
        self._size_label.setText(str(value))
        self._canvas.set_brush_size(value)
    
    # ==================== Filter Operations ====================
    
    def _apply_filter(self, name: str, info: dict) -> None:
        """Apply a filter to the image"""
        img = self._canvas.get_image()
        if img is None:
            return
        
        try:
            # Create filter kwargs
            kwargs = {}
            for key in ["factor", "radius", "bits"]:
                if key in info:
                    kwargs[key] = info[key]
            
            # Apply filter
            filtered = apply_filter(img.copy(), info["name"], **kwargs)
            
            # Create and execute command
            cmd = FilterCommand(img, filtered)
            self._command_manager.execute(cmd)
            
            self._canvas.set_image(img)
            self._update_status()
            self._update_undo_redo()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply filter:\n{str(e)}")
    
    # ==================== Undo/Redo ====================
    
    def _undo(self) -> None:
        """Undo last action"""
        if self._command_manager.undo():
            img = self._canvas.get_image()
            self._canvas.set_image(img)
            self._update_undo_redo()
    
    def _redo(self) -> None:
        """Redo last undone action"""
        if self._command_manager.redo():
            img = self._canvas.get_image()
            self._canvas.set_image(img)
            self._update_undo_redo()
    
    def _update_undo_redo(self) -> None:
        """Update undo/redo action states"""
        self._undo_action.setEnabled(self._command_manager.can_undo())
        self._redo_action.setEnabled(self._command_manager.can_redo())
    
    # ==================== Zoom Operations ====================
    
    def _zoom_in(self) -> None:
        """Zoom in"""
        self._canvas.zoom_in()
    
    def _zoom_out(self) -> None:
        """Zoom out"""
        self._canvas.zoom_out()
    
    def _zoom_fit(self) -> None:
        """Fit image to window"""
        self._canvas.zoom_fit()
    
    def _zoom_100(self) -> None:
        """Set 100% zoom"""
        self._canvas.zoom_100()
    
    # ==================== Event Handlers ====================
    
    def _on_image_modified(self) -> None:
        """Handle image modification"""
        self._modified = True
        self._update_title()
        self._save_action.setEnabled(True)
    
    def _on_zoom_changed(self, zoom: float) -> None:
        """Handle zoom change"""
        self._zoom_status.setText(f"{int(zoom * 100)}%")
    
    def _on_cursor_moved(self, x: int, y: int) -> None:
        """Handle cursor movement"""
        self._pos_status.setText(f"{x}, {y}")
    
    def _update_title(self) -> None:
        """Update window title"""
        filename = os.path.basename(self._current_file) if self._current_file else "Untitled"
        title = f"{filename}" + (" *" if self._modified else "") + " - AlanPaint"
        self.setWindowTitle(title)
    
    def _update_status(self) -> None:
        """Update status bar"""
        width, height = self._canvas.get_image_size()
        self._size_status.setText(f"{width} x {height}")
    
    def closeEvent(self, event) -> None:
        """Handle close event"""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before exiting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if not self._save_image():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        event.accept()
    
    def _show_about(self) -> None:
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AlanPaint",
            "<h1>AlanPaint</h1>"
            "<p><b>Created by Erik Ala Álvarez</b></p>"
            "<p>Created with VibeCode</p>"
            "<p>An open source application designed for computers with limited RAM.</p>"
            "<p>Fast image viewer and basic editor.</p>"
            "<p><i>Version 1.0.0</i></p>"
        )
    
    # ==================== Keyboard Shortcuts ====================
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts"""
        # Tool shortcuts
        if event.key() == Qt.Key_B:
            self._select_tool("brush")
        elif event.key() == Qt.Key_E:
            self._select_tool("eraser")
        elif event.key() == Qt.Key_L:
            self._select_tool("line")
        elif event.key() == Qt.Key_R:
            self._select_tool("rectangle")
        elif event.key() == Qt.Key_O:
            self._select_tool("ellipse")
        elif event.key() == Qt.Key_T:
            self._select_tool("text")
        else:
            super().keyPressEvent(event)
