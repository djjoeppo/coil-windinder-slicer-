# main.py
import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QSurfaceFormat

# Verander dit in main.py:
try:
    # We proberen de modules in te laden vanuit hun nieuwe mappen
    from view.gui_layout import CoilAppLayout
    from controller.controller import CoilController

    if __name__ == "__main__":
        # Schermkwaliteit (Anti-aliasing) instellen
        fmt = QSurfaceFormat()
        fmt.setSamples(4) 
        QSurfaceFormat.setDefaultFormat(fmt)

        app = QApplication(sys.argv)
        
        # Kleurenpaletten voor de draad en spoel
        wire_colors = {
            "Koper": (0.9, 0.45, 0.2), "Goud": (0.95, 0.75, 0.1), "Zilver": (0.75, 0.75, 0.75),
            "Rood": (0.85, 0.15, 0.15), "Blauw": (0.15, 0.45, 0.75), "Groen": (0.15, 0.7, 0.3),
            "Paars": (0.5, 0.1, 0.6), "Zwart": (0.1, 0.1, 0.1), "Wit": (0.95, 0.95, 0.95)
        }
        
        spool_colors = {
            "Standaard (Donker)": (0.2, 0.2, 0.2), "Aluminium": (0.7, 0.73, 0.75),
            "Messing": (0.78, 0.66, 0.25), "Plastic Zwart": (0.08, 0.09, 0.1), "Plastic Wit": (0.9, 0.9, 0.9)
        }

        # Interface opstarten met de juiste kleuren
        window = CoilAppLayout(wire_colors, spool_colors)
        window.resize(1450, 900)
        window.setWindowTitle("CoilMaster Pro - Modular Multi-Layer GUI")
        window.apply_theme("Dark Mode")
        window.lbl_info.setText("Status: Ready. Klik op UPDATE om te berekenen.")
        
        # Het brein (Controller) koppelen aan het venster
        controller = CoilController(window)
        
        window.show()
        sys.exit(app.exec())

except Exception as error:
    # Mocht er tóch een import- of crashfout zijn, dan vangen we die hier op
    print("\n=== CRASH DETECTED ===")
    traceback.print_exc() # Print de fout details in je terminal
    print("======================\n")
    
    # Maak een nette pop-up melding zodat je direct ziet wat er misgaat
    error_app = QApplication(sys.argv)
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setWindowTitle("Opstart Fout")
    error_box.setText("De app kon niet opstarten vanwege een fout in een van de modules.")
    error_box.setDetailedText(traceback.format_exc())
    error_box.exec()