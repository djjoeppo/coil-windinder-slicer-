# main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import CoilAppLayout

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoilAppLayout()
    window.setWindowTitle("Coil App - OrcaSlicer Concept Design")
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())