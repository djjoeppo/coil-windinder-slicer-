import sys
from PySide6.QtWidgets import QApplication
from coil_winder.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(820, 620)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
