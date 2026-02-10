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
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
