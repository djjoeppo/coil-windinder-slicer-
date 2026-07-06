# main.py
import sys
import os

# Set some environment variables that might speed up startup or improve compatibility
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QSurfaceFormat
from ui.main_window import CoilAppLayout

def pre_flight_check():
    """Phase 4: Verify critical assets and environment before startup."""
    critical_files = [
        "v2/assets/languages.json",
        "v2/assets/materials.json",
        "v2/assets/machine_settings.json"
    ]

    missing = [f for f in critical_files if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(f"Kritieke bestanden ontbreken: {', '.join(missing)}")

    # Check for basic dependencies (NumPy is critical for math)
    try:
        import numpy
    except ImportError:
        raise ImportError("NumPy library is niet geïnstalleerd. De applicatie kan niet rekenen.")

def main():
    # Set default surface format for better performance and anti-aliasing
    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)

    try:
        # 1. Run diagnostics
        pre_flight_check()

        # 2. Launch Main Window
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
