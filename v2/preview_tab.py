# ui/tabs/preview_tab.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QPushButton, QFileDialog, QSlider, QSplitter, QFrame
from PySide6.QtCore import Qt, Signal, QTimer
from ui.viewer_3d import Coil3DViewer

class PreviewTab(QWidget):
    timeline_changed = Signal(int)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.animate)
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # Center: 3D Viewer + Timeline
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.viewer = Coil3DViewer()
        center_layout.addWidget(self.viewer, 1)

        # Timeline
        self.timeline_container = QFrame()
        self.timeline_container.setFixedHeight(60)
        self.timeline_container.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #333;")
        timeline_layout = QHBoxLayout(self.timeline_container)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setCheckable(True)
        self.btn_play.toggled.connect(self.toggle_play)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(1000)
        self.slider.valueChanged.connect(self.on_slider_changed)

        timeline_layout.addWidget(self.btn_play)
        timeline_layout.addWidget(self.slider)
        center_layout.addWidget(self.timeline_container)

        # Right: G-code display + Controls
        right_panel = QWidget()
        right_panel.setMinimumWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_title = QLabel("G-code Preview")
        self.lbl_title.setObjectName("sectionTitle")
        right_layout.addWidget(self.lbl_title)
        
        self.gcode_display = QTextEdit()
        self.gcode_display.setReadOnly(True)
        self.gcode_display.setLineWrapMode(QTextEdit.NoWrap)
        self.gcode_display.setStyleSheet("""
            QTextEdit {
                background-color: #111;
                color: #0f0;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #333;
            }
        """)
        right_layout.addWidget(self.gcode_display)

        self.btn_save = QPushButton("Save G-code")
        self.btn_save.setObjectName("sliceActionButton")
        self.btn_save.clicked.connect(self.save_gcode)
        right_layout.addWidget(self.btn_save)

        # Add to splitter
        self.splitter.addWidget(center_widget)
        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(0, 1)

    def on_slider_changed(self, value):
        self.timeline_changed.emit(value)

    def toggle_play(self, checked):
        if checked:
            self.btn_play.setText("⏸")
            if self.slider.value() >= 1000:
                self.slider.setValue(0)
            self.timer.start()
        else:
            self.btn_play.setText("▶")
            self.timer.stop()

    def animate(self):
        val = self.slider.value() + 5
        if val >= 1000:
            val = 1000
            self.btn_play.setChecked(False)
        self.slider.setValue(val)

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
