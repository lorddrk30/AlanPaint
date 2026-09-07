"""AlanPaint desktop editor: drawing, cropping and non-destructive previews."""
import os
from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QToolButton, QSlider, QSpinBox,
    QComboBox, QCheckBox, QScrollArea, QFileDialog, QColorDialog,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QInputDialog,
    QLineEdit, QStackedWidget, QSizePolicy, QTabWidget,
)
from alanpaint.canvas import Canvas
from alanpaint.commands import CommandManager, FilterCommand, ReplaceImageCommand
from alanpaint.tools import create_tool, TextTool, TOOL_NAMES
from alanpaint.filters import apply_filter, apply_adjustments, FILTER_DEFINITIONS
from alanpaint.io import load_image, save_image, pil_to_qimage, SUPPORTED_FORMATS, SUPPORTED_EXTENSIONS
from alanpaint.theme import STYLE, icon


def label(text, name=None):
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    return widget


def button(text, callback, glyph=None, primary=False):
    widget = QPushButton(text)
    if glyph:
        widget.setIcon(icon(glyph, "#ffffff" if primary else "#73778c"))
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


class DimensionsDialog(QDialog):
    def __init__(self, parent, size, resizing=False):
        super().__init__(parent)
        self.setWindowTitle("Cambiar tamaño" if resizing else "Nuevo lienzo")
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        layout.addWidget(label(self.windowTitle(), "title"))
        layout.addWidget(label("Define las dimensiones en píxeles.", "muted"))
        form = QFormLayout()
        self.width_box, self.height_box = QSpinBox(), QSpinBox()
        for spin, value in zip((self.width_box, self.height_box), size):
            spin.setRange(1, 12000)
            spin.setValue(value)
            spin.setSuffix(" px")
        form.addRow("Ancho", self.width_box)
        form.addRow("Alto", self.height_box)
        self.lock = QCheckBox("Mantener proporción")
        self.lock.setChecked(resizing)
        self.ratio = size[0]/size[1]
        form.addRow(self.lock)
        self.width_box.valueChanged.connect(lambda value: self._sync(value, True))
        self.height_box.valueChanged.connect(lambda value: self._sync(value, False))
        self.lock.toggled.connect(lambda checked: setattr(self, "ratio", self.width_box.value()/self.height_box.value()))
        self.transparent = QCheckBox("Fondo transparente")
        if not resizing:
            form.addRow(self.transparent)
        layout.addLayout(form)
        actions = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        actions.button(QDialogButtonBox.Ok).setText("Cambiar tamaño" if resizing else "Crear lienzo")
        actions.button(QDialogButtonBox.Cancel).setText("Cancelar")
        actions.accepted.connect(self.accept)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)

    def _sync(self, value, width_changed):
        if self.lock.isChecked():
            target = self.height_box if width_changed else self.width_box
            target.blockSignals(True)
            target.setValue(max(1, round(value/self.ratio if width_changed else value*self.ratio)))
            target.blockSignals(False)

    def dimensions(self):
        return self.width_box.value(), self.height_box.value()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1280, 850)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(icon("brush", "#7858d6", 32))
        self.setAcceptDrops(True)
        self._current_file = None
        self._modified = False
        self._command_manager = CommandManager()
        self._tool_color, self._brush_size = (35, 38, 51), 8
        self._tool_id = "brush"
        self._selected_filter = "Original"
        self._preview_source = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(100)
        self._preview_timer.timeout.connect(self._render_preview)
        self._thumbnail_timer = QTimer(self)
        self._thumbnail_timer.setSingleShot(True)
        self._thumbnail_timer.setInterval(160)
        self._thumbnail_timer.timeout.connect(self._update_thumbnails)
        self._setup_actions()
        self._setup_ui()
        self._canvas.command_requested.connect(self._execute)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        self._canvas.cursor_moved.connect(lambda x, y: self._pos_status.setText(f"X {x}  Y {y}"))
        self._canvas.crop_changed.connect(self._crop_changed)
        self._canvas.crop_accepted.connect(self._apply_crop)
        self._canvas.crop_cancelled.connect(lambda: self._select_tool("brush"))
        self._canvas.color_picked.connect(self._set_color)
        self._canvas.text_requested.connect(self._insert_text)
        self._new_image(1000, 700)
        self._select_tool("brush")
        self._inspector_tabs.setCurrentIndex(1)
        QTimer.singleShot(0, self._canvas.zoom_fit)

    def _action(self, text, callback, shortcut=None, glyph=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if glyph:
            action.setIcon(icon(glyph))
        action.triggered.connect(lambda checked=False: callback())
        return action

    def _setup_actions(self):
        self._new_action = self._action("Nuevo lienzo…", self._new_dialog, "Ctrl+N", "new")
        self._open_action = self._action("Abrir imagen…", self._open_image, "Ctrl+O", "open")
        self._save_action = self._action("Guardar", self._save_image, "Ctrl+S", "save")
        self._save_as_action = self._action("Guardar como…", self._save_image_as, "Ctrl+Shift+S")
        self._undo_action = self._action("Deshacer", self._undo, "Ctrl+Z", "undo")
        self._redo_action = self._action("Rehacer", self._redo, "Ctrl+Y", "redo")
        self._redo_action.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        file_menu = self.menuBar().addMenu("Archivo")
        file_menu.addActions([self._new_action, self._open_action])
        file_menu.addSeparator()
        file_menu.addActions([self._save_action, self._save_as_action])
        file_menu.addSeparator()
        file_menu.addAction(self._action("Salir", self.close, "Alt+F4"))
        self.menuBar().addMenu("Editar").addActions([self._undo_action, self._redo_action])
        view_menu = self.menuBar().addMenu("Vista")
        for text, callback, shortcut in [
            ("Acercar", lambda: self._canvas.zoom_in(), "Ctrl++"),
            ("Alejar", lambda: self._canvas.zoom_out(), "Ctrl+-"),
            ("Ajustar a ventana", lambda: self._canvas.zoom_fit(), "Ctrl+0"),
            ("Tamaño real", lambda: self._canvas.zoom_100(), "Ctrl+1")]:
            view_menu.addAction(self._action(text, callback, shortcut))
        image_menu = self.menuBar().addMenu("Imagen")
        image_menu.addAction(self._action("Recortar", lambda: self._select_tool("crop"), "C"))
        image_menu.addAction(self._action("Girar 90° a la derecha", self._rotate))
        image_menu.addAction(self._action("Voltear horizontalmente", self._flip))
        image_menu.addAction(self._action("Cambiar tamaño…", self._resize_image))
        self.menuBar().addMenu("Ayuda").addAction(self._action("Acerca de AlanPaint", self._show_about))

    def _setup_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QFrame()
        header.setObjectName("header")
        row = QHBoxLayout(header)
        row.setContentsMargins(22, 14, 22, 14)
        mark = label("a", "logo")
        mark.setAlignment(Qt.AlignCenter)
        mark.setFixedSize(38, 38)
        row.addWidget(mark)
        row.addWidget(label("AlanPaint", "brand"))
        row.addSpacing(12)
        row.addWidget(label("TU ESPACIO CREATIVO", "section"))
        row.addStretch()
        row.addWidget(button("Nuevo", self._new_dialog, "new"))
        row.addWidget(button("Abrir imagen", self._open_image, "open"))
        row.addWidget(button("Guardar", self._save_image, "save", True))
        layout.addWidget(header)
        body = QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        center = QVBoxLayout()
        center.setSpacing(0)
        context = QFrame()
        context.setObjectName("context")
        context_row = QHBoxLayout(context)
        context_row.setContentsMargins(18, 10, 18, 10)
        self._document_label = label("Sin título", "document")
        context_row.addWidget(self._document_label)
        self._saved_label = label("Sin cambios", "muted")
        context_row.addWidget(self._saved_label)
        context_row.addStretch()
        for action in (self._undo_action, self._redo_action):
            tool = QToolButton()
            tool.setDefaultAction(action)
            tool.setFixedSize(32, 30)
            context_row.addWidget(tool)
        center.addWidget(context)
        self._canvas = Canvas()
        center.addWidget(self._canvas, 1)
        footer = QFrame()
        footer.setObjectName("context")
        footer_row = QHBoxLayout(footer)
        footer_row.setContentsMargins(15, 7, 15, 7)
        self._hint = label("Arrastra para dibujar · Espacio para mover", "muted")
        footer_row.addWidget(self._hint, 1)
        minus = button("−", lambda: self._canvas.zoom_out())
        minus.setFixedSize(30, 28)
        footer_row.addWidget(minus)
        self._zoom_status = button("100%", lambda: self._canvas.zoom_100())
        self._zoom_status.setToolTip("Ver al 100% · Ctrl+1")
        self._zoom_status.setFixedSize(66, 28)
        footer_row.addWidget(self._zoom_status)
        plus = button("+", lambda: self._canvas.zoom_in())
        plus.setFixedSize(30, 28)
        footer_row.addWidget(plus)
        fit = button("", lambda: self._canvas.zoom_fit(), "fit")
        fit.setToolTip("Ajustar a ventana · Ctrl+0")
        fit.setFixedSize(30, 28)
        footer_row.addWidget(fit)
        center.addWidget(footer)
        body.addLayout(center, 1)
        body.addWidget(self._build_inspector())
        layout.addLayout(body, 1)
        self.setCentralWidget(root)
        self._size_status = label("", "muted")
        self._pos_status = label("", "muted")
        self._tool_status = label("Pincel", "muted")
        self.statusBar().addWidget(label("  HECHO PARA CREAR", "section"))
        self.statusBar().addPermanentWidget(self._tool_status)
        self.statusBar().addPermanentWidget(self._pos_status)
        self.statusBar().addPermanentWidget(self._size_status)

    def _build_sidebar(self):
        panel = QFrame()
        panel.setObjectName("sidebar")
        panel.setFixedWidth(194)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(5)
        layout.addWidget(label("HERRAMIENTAS", "section"))
        layout.addSpacing(10)
        self._tool_buttons = {}
        shortcuts = {"brush": "B", "eraser": "E", "line": "L", "rectangle": "R", "ellipse": "O", "text": "T", "crop": "C", "picker": "I", "hand": "H"}
        for tool_id, name in TOOL_NAMES.items():
            tool = QToolButton()
            tool.setObjectName("tool")
            tool.setText(name)
            tool.setIcon(icon(tool_id))
            tool.setIconSize(QSize(20, 20))
            tool.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            tool.setCheckable(True)
            tool.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tool.setToolTip(f"{name} · {shortcuts[tool_id]}")
            tool.clicked.connect(lambda checked=False, t=tool_id: self._select_tool(t))
            if tool_id != "crop":
                self.addAction(self._action(name, lambda t=tool_id: self._select_tool(t), shortcuts[tool_id]))
            layout.addWidget(tool)
            self._tool_buttons[tool_id] = tool
        layout.addSpacing(20)
        layout.addWidget(label("COLOR", "section"))
        color_row = QHBoxLayout()
        self._color_btn = button("", self._select_color)
        self._color_btn.setFixedSize(32, 32)
        self._color_hex = QLineEdit("#232633")
        self._color_hex.setMaxLength(7)
        self._color_hex.setToolTip("Color hexadecimal · #RRGGBB")
        self._color_hex.editingFinished.connect(self._hex_changed)
        color_row.addWidget(self._color_btn)
        color_row.addWidget(self._color_hex)
        layout.addLayout(color_row)
        palette = QGridLayout()
        palette.setSpacing(5)
        colors = ["#232633", "#ffffff", "#9298ad", "#7858d6", "#ed6585", "#f0a94b", "#f5d966", "#65ba93", "#59acc9", "#5684e8", "#ab79d6", "#be8270"]
        for n, color in enumerate(colors):
            swatch = button("", lambda checked=False, c=color: self._set_color(QColor(c).getRgb()[:3]))
            swatch.setFixedSize(22, 22)
            swatch.setToolTip(color)
            swatch.setStyleSheet(f"background: {color}; border: 1px solid #dcdde7; border-radius: 6px; padding: 0;")
            palette.addWidget(swatch, n//6, n%6)
        layout.addLayout(palette)
        layout.addStretch()
        layout.addWidget(label("Una idea. Infinitas posibilidades.", "muted"))
        return panel

    def _build_inspector(self):
        panel = QFrame()
        panel.setObjectName("inspector")
        panel.setFixedWidth(270)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(12, 20, 12, 12)
        outer.addWidget(label("Hazlo tuyo", "title"))
        outer.addWidget(label("Pequeños cambios, grandes ideas.", "muted"))
        self._inspector_tabs = QTabWidget()
        outer.addWidget(self._inspector_tabs, 1)
        editing = QWidget()
        tool_layout = QVBoxLayout(editing)
        tool_layout.setContentsMargins(6, 14, 6, 14)
        tool_layout.setSpacing(14)
        self._inspector_tabs.addTab(editing, "Herramienta")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setStyleSheet("background: white;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 14, 4, 8)
        layout.setSpacing(7)
        self._tool_options = QStackedWidget()
        drawing = QWidget()
        drawing_layout = QVBoxLayout(drawing)
        drawing_layout.setContentsMargins(0, 8, 0, 0)
        size_row = QHBoxLayout()
        size_row.addWidget(label("Tamaño del pincel"))
        self._size_label = label("8 px", "muted")
        size_row.addStretch()
        size_row.addWidget(self._size_label)
        drawing_layout.addLayout(size_row)
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(1, 100)
        self._size_slider.setValue(8)
        self._size_slider.valueChanged.connect(self._brush_size_changed)
        drawing_layout.addWidget(self._size_slider)
        self._filled = QCheckBox("Rellenar figuras")
        self._filled.toggled.connect(self._filled_changed)
        drawing_layout.addWidget(self._filled)
        text_row = QHBoxLayout()
        text_row.addWidget(label("Tamaño del texto"))
        self._font_size = QSpinBox()
        self._font_size.setRange(8, 300)
        self._font_size.setValue(32)
        self._font_size.setSuffix(" px")
        text_row.addWidget(self._font_size)
        drawing_layout.addLayout(text_row)
        self._tool_options.addWidget(drawing)
        crop = QWidget()
        crop_layout = QVBoxLayout(crop)
        crop_layout.setContentsMargins(0, 8, 0, 0)
        crop_layout.addWidget(label("PROPORCIÓN DEL RECORTE", "section"))
        self._crop_ratio = QComboBox()
        for text, ratio in [("Libre", None), ("Cuadrado · 1:1", 1), ("Fotografía · 4:3", 4/3), ("Panorámico · 16:9", 16/9), ("Vertical · 9:16", 9/16)]:
            self._crop_ratio.addItem(text, ratio)
        self._crop_ratio.currentIndexChanged.connect(lambda: self._canvas.set_crop_ratio(self._crop_ratio.currentData()))
        crop_layout.addWidget(self._crop_ratio)
        self._crop_dimensions = label("Arrastra sobre la imagen.", "muted")
        crop_layout.addWidget(self._crop_dimensions)
        self._crop_apply = button("Aplicar recorte", self._apply_crop, "check", True)
        self._crop_apply.setEnabled(False)
        crop_layout.addWidget(self._crop_apply)
        crop_layout.addWidget(button("Cancelar · Esc", lambda: self._select_tool("brush")))
        self._tool_options.addWidget(crop)
        tool_layout.addWidget(self._tool_options)
        tool_layout.addSpacing(4)
        tool_layout.addWidget(label("TRANSFORMAR", "section"))
        transforms = QHBoxLayout()
        for name, glyph, callback in [("Girar", "rotate", self._rotate), ("Voltear", "flip", self._flip), ("Tamaño", "resize", self._resize_image)]:
            tool = QToolButton()
            tool.setText(name)
            tool.setIcon(icon(glyph))
            tool.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tool.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tool.clicked.connect(callback)
            tool.setToolTip({"Girar": "Girar 90° a la derecha", "Voltear": "Voltear horizontalmente", "Tamaño": "Cambiar dimensiones de la imagen"}[name])
            transforms.addWidget(tool)
        tool_layout.addLayout(transforms)
        tool_layout.addStretch()
        tips = label("A tu ritmo.\n\nCtrl+Z para deshacer\nCtrl+rueda para acercar\nEspacio + arrastrar para mover\n\nTambién puedes soltar una imagen\naquí para abrirla.", "muted")
        tool_layout.addWidget(tips)
        layout.addWidget(label("FILTROS", "section"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self._filter_buttons = {}
        for n, name in enumerate(FILTER_DEFINITIONS):
            tool = QToolButton()
            tool.setObjectName("filter")
            tool.setText(name)
            tool.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tool.setIconSize(QSize(94, 37))
            tool.setFixedSize(108, 66)
            tool.setCheckable(True)
            tool.setChecked(n == 0)
            tool.clicked.connect(lambda checked=False, name=name: self._choose_filter(name))
            self._filter_buttons[name] = tool
            grid.addWidget(tool, n//2, n%2)
        layout.addLayout(grid)
        layout.addWidget(label("AJUSTES", "section"))
        self._adjustments = {}
        for key, name in [("brightness", "Brillo"), ("contrast", "Contraste"), ("saturation", "Saturación")]:
            row = QHBoxLayout()
            row.addWidget(label(name))
            value_label = label("100%", "muted")
            row.addStretch()
            row.addWidget(value_label)
            layout.addLayout(row)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 200)
            slider.setValue(100)
            slider.setAccessibleName(name)
            slider.valueChanged.connect(lambda value, target=value_label: target.setText(f"{value}%"))
            slider.valueChanged.connect(self._queue_preview)
            self._adjustments[key] = slider
            layout.addWidget(slider)
        self._preview_note = label("Vista previa antes de aplicar.", "muted")
        outer.addWidget(self._preview_note)
        self._apply_button = button("Aplicar cambios", self._apply_effects, "check", True)
        self._apply_button.setEnabled(False)
        outer.addWidget(self._apply_button)
        reset = button("Restablecer", self._reset_effects)
        reset.setObjectName("ghost")
        outer.addWidget(reset)
        layout.addStretch()
        scroll.setWidget(content)
        self._inspector_tabs.addTab(scroll, "Filtros y ajustes")
        return panel

    def _select_tool(self, tool_id):
        if self._effects_pending():
            self._reset_effects()
        self._tool_id = tool_id
        tool = create_tool(tool_id, self._filled.isChecked()) if tool_id in ("brush", "eraser", "line", "rectangle", "ellipse", "text") else None
        self._canvas.set_tool(tool, tool_id)
        self._canvas.set_color(self._tool_color)
        self._canvas.set_brush_size(self._brush_size)
        for name, widget in self._tool_buttons.items():
            widget.setChecked(name == tool_id)
            widget.setIcon(icon(name, "#7858d6" if name == tool_id else "#73778c"))
        self._tool_options.setCurrentIndex(1 if tool_id == "crop" else 0)
        self._inspector_tabs.setCurrentIndex(0)
        self._tool_status.setText(TOOL_NAMES[tool_id])
        hints = {"crop": "Arrastra para seleccionar · Enter aplica · Esc cancela", "text": "Haz clic donde quieras escribir", "picker": "Haz clic para tomar un color de la imagen", "hand": "Arrastra para mover el lienzo"}
        self._hint.setText(hints.get(tool_id, "Arrastra para dibujar · Espacio para mover"))
        self._canvas.setFocus()
        self._update_color_button()

    def _filled_changed(self):
        if self._tool_id in ("rectangle", "ellipse"):
            self._select_tool(self._tool_id)

    def _brush_size_changed(self, value):
        self._brush_size = value
        self._size_label.setText(f"{value} px")
        self._canvas.set_brush_size(value)

    def _select_color(self):
        color = QColorDialog.getColor(QColor(*self._tool_color), self, "Elige un color")
        if color.isValid():
            self._set_color(color.getRgb()[:3])

    def _hex_changed(self):
        text = self._color_hex.text().strip()
        color = QColor(text if text.startswith("#") else "#"+text)
        if color.isValid():
            self._set_color(color.getRgb()[:3])
        else:
            self._update_color_button()

    def _set_color(self, color):
        self._tool_color = tuple(color)
        self._canvas.set_color(self._tool_color)
        self._update_color_button()

    def _update_color_button(self):
        value = QColor(*self._tool_color).name()
        self._color_btn.setStyleSheet(f"background: {value}; border: 1px solid #d8dbe6; border-radius: 7px;")
        self._color_hex.setText(value.upper())

    def _insert_text(self, x, y):
        text, ok = QInputDialog.getMultiLineText(self, "Añadir texto", "Escribe tu texto:")
        if ok and text.strip():
            tool = TextTool()
            tool.start(x, y, self._tool_color, self._font_size.value())
            tool.set_text(text)
            patch = tool.create_text_image()
            self._canvas.commit_patch(patch, tool.region)

    def _effects_pending(self):
        return self._selected_filter != "Original" or any(s.value() != 100 for s in self._adjustments.values())

    def _choose_filter(self, name):
        self._selected_filter = name
        for key, widget in self._filter_buttons.items():
            widget.setChecked(key == name)
        self._queue_preview()

    def _queue_preview(self):
        self._canvas.cancel_interaction()
        pending = self._effects_pending()
        self._canvas._preview_active = pending
        self._apply_button.setEnabled(pending)
        self._preview_note.setText("Vista previa · aplica para conservar." if pending else "Vista previa antes de aplicar.")
        self._preview_timer.start()

    def _effect_result(self, image, preview=False):
        info = dict(FILTER_DEFINITIONS[self._selected_filter])
        name = info.pop("name")
        if preview and "radius" in info:
            info["radius"] *= image.width/self._canvas.get_image().width
        result = apply_filter(image, name, **info)
        return apply_adjustments(result, **{key: slider.value() for key, slider in self._adjustments.items()})

    def _render_preview(self):
        if not self._effects_pending():
            self._canvas.refresh()
            return
        if self._preview_source is None:
            self._preview_source = self._canvas.get_image().copy()
            self._preview_source.thumbnail((1200, 900), Image.Resampling.LANCZOS)
        self._canvas.set_preview(self._effect_result(self._preview_source, preview=True))

    def _reset_effects(self):
        self._preview_timer.stop()
        self._selected_filter = "Original"
        for name, widget in self._filter_buttons.items():
            widget.setChecked(name == "Original")
        for slider in self._adjustments.values():
            slider.setValue(100)
        self._preview_timer.stop()
        self._preview_source = None
        self._apply_button.setEnabled(False)
        self._preview_note.setText("Vista previa antes de aplicar.")
        self._canvas.refresh()

    def _apply_effects(self):
        if not self._effects_pending():
            return True
        self._preview_timer.stop()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            image = self._canvas.get_image()
            result = self._effect_result(image)
            self._reset_effects()
            self._execute(FilterCommand(image, result))
            return True
        except Exception as error:
            QMessageBox.critical(self, "No se pudo aplicar el filtro", str(error))
            return False
        finally:
            QApplication.restoreOverrideCursor()

    def _update_thumbnails(self):
        source = self._canvas.get_image()
        if source is None:
            return
        thumb = ImageOps.fit(source, (188, 74), method=Image.Resampling.LANCZOS)
        for name, info in FILTER_DEFINITIONS.items():
            args = dict(info)
            result = apply_filter(thumb, args.pop("name"), **args)
            background = Image.new("RGBA", result.size, "#edeef3")
            result = Image.alpha_composite(background, result.convert("RGBA"))
            pixmap = QPixmap.fromImage(pil_to_qimage(result))
            pixmap.setDevicePixelRatio(2)
            self._filter_buttons[name].setIcon(QIcon(pixmap))

    def _crop_changed(self, rect):
        self._crop_apply.setEnabled(rect is not None)
        self._crop_dimensions.setText(f"{rect[2]-rect[0]} × {rect[3]-rect[1]} px · Enter para aplicar" if rect else "Arrastra sobre la imagen.")

    def _apply_crop(self):
        rect = self._canvas.crop_rect
        if rect:
            self._execute(ReplaceImageCommand(self._canvas, self._canvas.get_image().crop(rect)))
            self._select_tool("brush")
            self._canvas.zoom_fit()
            self.statusBar().showMessage("Imagen recortada. Puedes deshacer con Ctrl+Z.", 4500)

    def _rotate(self):
        if not self._apply_effects():
            return
        image = self._canvas.get_image().transpose(Image.Transpose.ROTATE_270)
        self._execute(ReplaceImageCommand(self._canvas, image))
        self._canvas.zoom_fit()

    def _flip(self):
        if not self._apply_effects():
            return
        self._execute(ReplaceImageCommand(self._canvas, ImageOps.mirror(self._canvas.get_image())))

    def _resize_image(self):
        dialog = DimensionsDialog(self, self._canvas.get_image_size(), True)
        if dialog.exec() == QDialog.Accepted:
            if not self._apply_effects():
                return
            if dialog.dimensions() != self._canvas.get_image_size():
                image = self._canvas.get_image().resize(dialog.dimensions(), Image.Resampling.LANCZOS)
                self._execute(ReplaceImageCommand(self._canvas, image))
                self._canvas.zoom_fit()

    def _execute(self, command):
        self._command_manager.execute(command)
        self._after_edit()

    def _after_edit(self):
        self._preview_source = None
        self._canvas.refresh()
        self._update_document()
        self._thumbnail_timer.start()

    def _undo(self):
        if self._effects_pending():
            self._reset_effects()
            return
        self._canvas.cancel_interaction()
        old_size = self._canvas.get_image_size()
        if self._command_manager.undo():
            self._after_edit()
            if old_size != self._canvas.get_image_size():
                self._canvas.zoom_fit()

    def _redo(self):
        self._reset_effects()
        self._canvas.cancel_interaction()
        old_size = self._canvas.get_image_size()
        if self._command_manager.redo():
            self._after_edit()
            if old_size != self._canvas.get_image_size():
                self._canvas.zoom_fit()

    def _update_document(self):
        self._modified = self._command_manager.modified
        name = os.path.basename(self._current_file) if self._current_file else "Sin título"
        self.setWindowTitle(f"{name}{' *' if self._modified else ''} — AlanPaint")
        self._document_label.setText(name if len(name) <= 26 else name[:23]+"…")
        self._document_label.setToolTip(self._current_file or name)
        self._saved_label.setText("• Sin guardar" if self._modified else "Sin cambios")
        self._undo_action.setEnabled(self._command_manager.can_undo())
        self._redo_action.setEnabled(self._command_manager.can_redo())
        w, h = self._canvas.get_image_size()
        self._size_status.setText(f"   {w} × {h} px   ")

    def _on_zoom_changed(self, zoom):
        self._zoom_status.setText(f"{zoom*100:.0f}%" if zoom >= .1 else f"{zoom*100:.1f}%")

    def _new_dialog(self):
        dialog = DimensionsDialog(self, (1000, 700))
        if dialog.exec() == QDialog.Accepted and self._confirm_discard():
            self._new_image(*dialog.dimensions(), transparent=dialog.transparent.isChecked())

    def _new_image(self, width=1000, height=700, transparent=False):
        image = Image.new("RGBA" if transparent else "RGB", (width, height), (0, 0, 0, 0) if transparent else "white")
        self._load_document(image)

    def _load_document(self, image, path=None):
        self._reset_effects()
        self._command_manager.clear()
        self._current_file = path
        self._canvas.set_image(image)
        self._canvas.zoom_fit()
        self._update_document()
        self._thumbnail_timer.start()

    def _confirm_discard(self):
        if not self._command_manager.modified and not self._effects_pending():
            return True
        box = QMessageBox(self)
        box.setWindowTitle("Guardar cambios")
        box.setText("¿Quieres guardar los cambios de esta imagen?")
        box.setInformativeText("También se guardarán los filtros que estás previsualizando.")
        save = box.addButton("Guardar", QMessageBox.AcceptRole)
        discard = box.addButton("Descartar", QMessageBox.DestructiveRole)
        cancel = box.addButton("Cancelar", QMessageBox.RejectRole)
        box.setDefaultButton(save)
        box.setEscapeButton(cancel)
        box.exec()
        if box.clickedButton() == save:
            return self._save_image()
        return box.clickedButton() == discard

    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir imagen", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff);;Todos los archivos (*)")
        if path:
            self._open_path(path)

    def _open_path(self, path):
        try:
            image = load_image(path)
        except Exception as error:
            QMessageBox.critical(self, "No se pudo abrir la imagen", str(error))
            return
        if self._confirm_discard():
            self._load_document(image, path)

    def _save_image(self):
        if not self._current_file:
            return self._save_image_as()
        return self._write_file(self._current_file)

    def _save_image_as(self):
        filters = ";;".join(info[0] for info in SUPPORTED_FORMATS.values())
        path, selected = QFileDialog.getSaveFileName(self, "Guardar imagen", self._current_file or "Mi creación.png", filters)
        if not path:
            return False
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            extension = next((info[1] for info in SUPPORTED_FORMATS.values() if info[0] == selected), ".png")
            path += extension
            if os.path.exists(path):
                reply = QMessageBox.question(self, "Reemplazar archivo", f"Ya existe {os.path.basename(path)}. ¿Quieres reemplazarlo?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return False
        return self._write_file(path)

    def _write_file(self, path):
        try:
            if not self._apply_effects():
                return False
            save_image(self._canvas.get_image(), path)
            self._current_file = path
            self._command_manager.mark_saved()
            self._update_document()
            self.statusBar().showMessage("Imagen guardada correctamente.", 4000)
            return True
        except Exception as error:
            QMessageBox.critical(self, "No se pudo guardar", str(error))
            return False

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() and os.path.splitext(url.toLocalFile())[1].lower() in SUPPORTED_EXTENSIONS for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and os.path.splitext(url.toLocalFile())[1].lower() in SUPPORTED_EXTENSIONS:
                self._open_path(url.toLocalFile())
                event.acceptProposedAction()
                break

    def closeEvent(self, event):
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    def _show_about(self):
        QMessageBox.about(self, "Acerca de AlanPaint", "<h2>AlanPaint 2.0</h2><p>Tu espacio para dibujar, editar y crear.</p><p>Creado por Erik Ala Álvarez con VibeCode.</p><p>Python · PySide6 · Pillow</p>")
