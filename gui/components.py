# ui/components.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class Dummy3DViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1a1a1a; border-left: 1px solid #2d2f31;")
        layout = QVBoxLayout(self)
        
        self.lbl = QLabel("3D TELEWERK VENSTER\n(OrcaSlicer Stijl)", self)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("color: #555; font-weight: bold; font-size: 16px; font-family: 'Segoe UI';")
        layout.addWidget(self.lbl)
        
    def setBackgroundColor(self, color): pass
    def set_spool_visibility(self, visible): pass