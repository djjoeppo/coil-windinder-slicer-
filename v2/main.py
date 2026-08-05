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
    # Hyper-Robust asset discovery (Bolt Optimization v3)
    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()
    
    # Define search candidates with their absolute resolved paths
    candidates = [
        script_dir / "assets",
        cwd / "v2" / "assets",
        cwd / "assets",
        script_dir.parent / "assets"
    ]
    
    critical_files = ["languages.json", "materials.json", "machine_settings.json"]
    found_assets_dir = None
    diag_info = []

    for d in candidates:
        abs_d = d.resolve()
        if not abs_d.exists():
            diag_info.append(f"{abs_d} -> Map bestaat niet")
            continue
        if not abs_d.is_dir():
            diag_info.append(f"{abs_d} -> Is geen map")
            continue
            
        # A directory is only valid if it contains all critical files
        missing_here = [f for f in critical_files if not (abs_d / f).exists()]
        if not missing_here:
            found_assets_dir = abs_d
            break
        else:
            diag_info.append(f"{abs_d} -> Bestanden missen: {', '.join(missing_here)}")

    if not found_assets_dir:
        details = "\n".join(diag_info)
        raise FileNotFoundError(
            f"Assets map kon niet worden gelokaliseerd.\n\nDiagnose:\n{details}"
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
