# main.py
import sys
import os
from pathlib import Path

# Phase 4: Ensure the application root is in sys.path for reliable module resolution
app_root = Path(__file__).resolve().parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

# Set some environment variables that might speed up startup or improve compatibility
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QSurfaceFormat

def pre_flight_check():
    """Phase 4: Verify critical assets and environment before startup."""
    # Robust asset discovery (Bolt optimization)
    base_dir = Path(__file__).resolve().parent
    assets_dir = base_dir / "assets"

    # Fallback search for assets (e.g., if running from a different directory)
    if not assets_dir.exists():
        assets_dir = Path.cwd() / "v2" / "assets"
        if not assets_dir.exists():
             assets_dir = Path.cwd() / "assets"

    critical_files = ["languages.json", "materials.json", "machine_settings.json"]
    missing = [f for f in critical_files if not (assets_dir / f).exists()]

    if missing:
        raise FileNotFoundError(
            f"Kritieke bestanden ontbreken in {assets_dir.resolve()}:\n{', '.join(missing)}"
        )

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
