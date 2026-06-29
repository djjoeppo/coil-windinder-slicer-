# ui/tabs/device_tab.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class DeviceTab(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        layout = QHBoxLayout(self)
        self.lbl = QLabel("Machine Verbinding & Live Wikkelen Status.")
        self.lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl)
        
    def retranslate_ui(self, tx):
        pass