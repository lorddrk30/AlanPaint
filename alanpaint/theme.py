"""Local vector icons and the editor's shared visual style."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

PATHS = {
    "brush": '<path d="m14 4 6 6M5 15 16 4a3 3 0 0 1 4 4L9 19H5z"/><path d="M5 15c-4 0 0 5-3 7 5 0 7-1 7-4"/>',
    "eraser": '<path d="m4 12 9-9a2 2 0 0 1 3 0l5 5a2 2 0 0 1 0 3l-9 9H8l-4-4a3 3 0 0 1 0-4zM9 7l8 8M12 20h10"/>',
    "line": '<path d="m5 19 14-14"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="5" r="2"/>',
    "rectangle": '<rect x="4" y="5" width="16" height="14" rx="2"/>',
    "ellipse": '<ellipse cx="12" cy="12" rx="9" ry="7"/>',
    "text": '<path d="M4 6V4h16v2M12 4v16M8 20h8"/>',
    "crop": '<path d="M6 3v15h15M3 6h15v15M9 3v3M3 9h3"/>',
    "picker": '<path d="m14 4 6 6M16 2l6 6M17 7 5 19l-3 3 1-5L15 5"/>',
    "hand": '<path d="M8 12V5a2 2 0 0 1 4 0v6-8a2 2 0 0 1 4 0v9-6a2 2 0 0 1 4 0v10c0 6-9 9-13 3l-4-6c-1-3 2-4 3-2l2 3"/>',
    "open": '<path d="M3 8V5h7l2 3h9v11H3zM3 11h18"/>',
    "save": '<path d="M5 3h12l4 4v14H3V3zM7 3v6h10V3M7 21v-8h10v8"/>',
    "new": '<path d="M14 3H5v18h14V8zM14 3v5h5M8 14h8M12 10v8"/>',
    "undo": '<path d="m9 5-6 5 6 5M3 10h11a6 6 0 0 1 0 12"/>',
    "redo": '<path d="m15 5 6 5-6 5M21 10H10a6 6 0 0 0 0 12"/>',
    "rotate": '<path d="M4 10a8 8 0 1 1 1 8M4 4v6h6"/>',
    "flip": '<path d="M12 2v20M8 5 2 19h6zM16 5l6 14h-6z"/>',
    "resize": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="m8 16 8-8M11 8h5v5M8 11v5h5"/>',
    "check": '<path d="m5 12 4 4L20 5"/>',
    "close": '<path d="m6 6 12 12M6 18 18 6"/>',
    "fit": '<path d="M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6"/>',
    "spark": '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z"/>',
}


def icon(name, color="#626479", size=22):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{PATHS.get(name, PATHS["spark"])}</g></svg>'
    pixmap = QPixmap(size*2, size*2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


STYLE = """
QMainWindow, QDialog { background: #f8f9fc; }
QWidget { font-family: 'Segoe UI'; font-size: 12px; color: #303345; }
QMenuBar { background: #ffffff; padding: 4px 14px; border-bottom: 1px solid #eceef3; }
QMenuBar::item { padding: 5px 12px; border-radius: 4px; }
QMenuBar::item:selected, QMenu::item:selected { background: #eee9fd; color: #6b4ed1; }
QMenu { background: white; border: 1px solid #e2e4ed; padding: 6px; }
QMenu::item { padding: 8px 25px; }
QFrame#header, QFrame#sidebar, QFrame#inspector { background: white; border: 1px solid #e8eaf1; }
QFrame#header { border-top: none; }
QFrame#context { background: #fafbfe; border-bottom: 1px solid #e3e5ee; }
QLabel#brand { font-size: 23px; font-weight: 700; letter-spacing: -1px; color: #272937; }
QLabel#logo { background: #7960dc; color: white; font-size: 22px; font-weight: 700; border-radius: 11px; }
QLabel#section { color: #9295a7; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }
QLabel#title { font-size: 18px; font-weight: 600; color: #292d40; }
QLabel#muted { color: #8c90a2; font-size: 11px; }
QLabel#document { font-weight: 600; }
QLabel#badge { background: #f0ebfc; color: #7759d2; border-radius: 5px; padding: 4px 8px; font-size: 10px; }
QPushButton, QToolButton { background: white; border: 1px solid #e2e5ee; border-radius: 7px; padding: 8px 12px; }
QPushButton:hover, QToolButton:hover { background: #f2effb; border-color: #cfc2f0; }
QPushButton:pressed, QToolButton:pressed { background: #e5ddfa; }
QPushButton:disabled, QToolButton:disabled { color: #b5b8c7; background: #f6f7fa; border-color: #eceef4; }
QPushButton#primary { background: #7858d6; color: white; border-color: #7858d6; font-weight: 600; }
QPushButton#primary:hover { background: #6849c6; }
QPushButton#primary:disabled { background: #d1c4ef; border-color: #d1c4ef; color: white; }
QToolButton#tool { border: none; text-align: left; padding: 10px 12px; }
QToolButton#tool:checked { background: #eee9fc; color: #7151cc; font-weight: 600; }
QToolButton#filter { padding: 5px; border-color: #e8eaf1; font-size: 11px; }
QToolButton#filter:checked { border: 2px solid #8b6cde; background: #f4f0ff; padding: 4px; color: #7151cc; }
QPushButton#ghost { background: transparent; border: none; color: #777d94; }
QSlider::groove:horizontal { height: 4px; background: #e9e8f1; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #947ae0; border-radius: 2px; }
QSlider::handle:horizontal { background: white; border: 2px solid #8a6cdb; width: 12px; height: 12px; margin: -6px 0; border-radius: 8px; }
QSlider { min-height: 22px; }
QSpinBox, QComboBox, QLineEdit, QPlainTextEdit { background: white; border: 1px solid #e1e4ee; padding: 7px; border-radius: 6px; selection-background-color: #947ae0; }
QSpinBox:focus, QComboBox:focus, QLineEdit:focus { border-color: #967ade; }
QComboBox::drop-down { border: none; width: 22px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; }
QStatusBar { background: white; border-top: 1px solid #e3e5ee; color: #858a9d; }
QStatusBar::item { border: none; }
QScrollArea { border: none; background: white; }
QTabWidget::pane { border: none; border-top: 1px solid #eceaf4; }
QTabBar::tab { background: white; padding: 10px 12px; color: #8a8ca0; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #7858d6; border-bottom: 2px solid #7858d6; }
QScrollBar:vertical { width: 7px; background: transparent; }
QScrollBar::handle:vertical { background: #dedee8; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { color: #ffffff; background: #39364b; padding: 6px; border: none; }
"""
