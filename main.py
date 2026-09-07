"""
AlanPaint - Lightweight Paint-like editor focused on low RAM usage
Entry point for the application
"""
import sys
from PySide6.QtWidgets import QApplication
from alanpaint.ui import MainWindow


def main():
    """Main entry point for AlanPaint"""
    app = QApplication(sys.argv)
    app.setApplicationName("AlanPaint")
    app.setApplicationVersion("2.0.0")
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    if len(sys.argv) > 1:
        window._open_path(sys.argv[1])
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
