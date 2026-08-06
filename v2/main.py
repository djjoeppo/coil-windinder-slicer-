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
    
    # 1. Run diagnostics
    try:
        pre_flight_check()
    except Exception as e:
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

    # 2. Splash Screen with progress & custom logo with fallback checking
    from PySide6.QtWidgets import QSplashScreen
    from PySide6.QtGui import QPixmap, QIcon
    from PySide6.QtCore import Qt, QTimer
    from core.config import get_resource_path

    # Check for logo in assets (both .png and .jpg/jpeg)
    logo_path = None
    possible_extensions = ["logo.png", "logo.jpg", "logo.jpeg"]
    for ext in possible_extensions:
        try:
            path = get_resource_path(ext)
            if os.path.exists(path):
                logo_path = path
                break
        except Exception:
            pass

    # If logo doesn't exist, we must trigger a dismissible debugging dialog as requested
    if not logo_path:
        expected_path = os.path.join(str(Path(__file__).resolve().parent / "assets"), "logo.png")
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Afbeelding/Icoontje mist!")
        msg_box.setText(f"Waarschuwing: Het opstart-logo kon niet worden gevonden.\n\nVerwachte locatie:\n{expected_path}")
        msg_box.setInformativeText("U kunt gewoon doorklikken om de applicatie op te starten.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

        # Use an empty fallback pixmap for splash
        splash_pix = QPixmap(400, 300)
        splash_pix.fill(Qt.darkGray)
    else:
        splash_pix = QPixmap(logo_path)

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("CoilMaster Pro aan het laden...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)

    # Simulate loading process on progress bar / splash
    for progress in range(1, 101, 15):
        splash.showMessage(f"CoilMaster Pro aan het laden... {progress}%", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()
        QTimer.singleShot(50, lambda: None) # brief delay

    try:
        # 3. Launch Main Window (Deferred import to catch startup crashes in GUI)
        from ui.main_window import CoilAppLayout
        window = CoilAppLayout()
        window.setWindowTitle("CoilMaster Pro - Unified G-Code Generator")

        # Set Window Desktop Icon
        icon_path = None
        for ext in ["icon.png", "logo.png", "icon.ico"]:
            try:
                p = get_resource_path(ext)
                if os.path.exists(p):
                    icon_path = p
                    break
            except Exception:
                pass

        if icon_path:
            window.setWindowIcon(QIcon(icon_path))
            app.setWindowIcon(QIcon(icon_path))
        else:
            # Try setting standard fallback if any icon found
            pass

        window.resize(1450, 900)
        splash.finish(window)
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
