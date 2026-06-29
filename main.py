# main.py
import sys
import os

# Set some environment variables that might speed up startup or improve compatibility
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat
from ui.main_window import CoilAppLayout

def main():
    # Set default surface format for better performance and anti-aliasing
    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = CoilAppLayout()
    window.setWindowTitle("CoilMaster Pro - Unified G-Code Generator")
    window.resize(1450, 900)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
