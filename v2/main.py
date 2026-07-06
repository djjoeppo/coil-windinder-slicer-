# main.py
import sys
import os

# Set some environment variables that might speed up startup or improve compatibility
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QSurfaceFormat

def pre_flight_check():
    """Phase 4: Verify critical assets and environment before startup."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    critical_files = [
        os.path.join(base_dir, "assets/languages.json"),
        os.path.join(base_dir, "assets/materials.json"),
        os.path.join(base_dir, "assets/machine_settings.json")
    ]

    missing = [f for f in critical_files if not os.path.exists(f)]
    if missing:
        # Show only relative path for readability in dialog
        rel_missing = [os.path.relpath(f, base_dir) for f in missing]
        raise FileNotFoundError(f"Kritieke bestanden ontbreken: {', '.join(rel_missing)}")

    # Check for basic dependencies (NumPy is critical for math)
    try:
        import numpy
        import pyqtgraph
        import OpenGL
        import serial
    except ImportError as e:
        raise ImportError(f"Ontbrekende afhankelijkheid: {e.name}. Installeer alle vereisten via requirements.txt.")

def main():
    # Set default surface format for better performance and anti-aliasing
    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)

    try:
        # 1. Run diagnostics
        pre_flight_check()

        # 2. Launch Main Window (Deferred import to catch startup crashes in GUI)
        from ui.main_window import CoilAppLayout
        window = CoilAppLayout()
        window.setWindowTitle("CoilMaster Pro - Unified G-Code Generator")
        window.resize(1450, 900)
        window.show()
        sys.exit(app.exec())

    except Exception as e:
        # 3. Graceful Error Catching
        error_msg = f"Fataal opstartprobleem:\n\n{str(e)}"
        print(f"CRITICAL ERROR: {e}")

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Opstartfout")
        msg_box.setText(error_msg)
        msg_box.setInformativeText("Controleer of alle bibliotheken en asset-bestanden aanwezig zijn.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
        sys.exit(1)

if __name__ == "__main__":
    main()
