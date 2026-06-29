# ui/tabs/preview_tab.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class PreviewTab(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        layout = QHBoxLayout(self)
        self.lbl = QLabel("Hier configureer je de G-code en spoel-snelheden.")
        self.lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl)
        
    def retranslate_ui(self, tx):
        # Voeg hier vertalingen toe zodra deze tab groeit
        pass