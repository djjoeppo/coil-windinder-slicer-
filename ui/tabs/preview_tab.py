# ui/tabs/preview_tab.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Qt

class PreviewTab(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Sidebar for controls
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)

        self.lbl_title = QLabel("G-code Preview")
        self.lbl_title.setObjectName("sectionTitle")
        sidebar_layout.addWidget(self.lbl_title)

        self.btn_save = QPushButton("Save G-code")
        self.btn_save.setObjectName("sliceActionButton")
        self.btn_save.clicked.connect(self.save_gcode)
        sidebar_layout.addWidget(self.btn_save)

        sidebar_layout.addStretch()

        # Main area for G-code display
        self.gcode_display = QTextEdit()
        self.gcode_display.setReadOnly(True)
        self.gcode_display.setLineWrapMode(QTextEdit.NoWrap)
        self.gcode_display.setStyleSheet("""
            QTextEdit {
                background-color: #111;
                color: #0f0;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #333;
            }
        """)

        layout.addWidget(sidebar)
        layout.addWidget(self.gcode_display)

    def set_gcode(self, gcode):
        self.gcode_display.setPlainText(gcode)

    def save_gcode(self):
        gcode = self.gcode_display.toPlainText()
        if not gcode:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save G-code", "", "G-code files (*.gcode);;Text files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(gcode)

    def retranslate_ui(self, tx):
        self.lbl_title.setText(tx.get("nav_preview", "Preview"))
        self.btn_save.setText(tx.get("btn_save_gcode", "Save G-code"))
