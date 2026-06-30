# ui/tabs/preview_tab.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QPushButton, QFileDialog, QSlider, QSplitter, QFrame, QLineEdit
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

        # Left: Settings Sidebar
        self.sidebar_left = QWidget()
        self.sidebar_left.setMinimumWidth(250)
        self.sidebar_left.setObjectName("sidebarContainer")
        lay_sidebar = QVBoxLayout(self.sidebar_left)

        card_params = QFrame()
        card_params.setObjectName("sectionCard")
        lay_card_params = QVBoxLayout(card_params)

        self.lbl_sidebar_title = QLabel("MODIFIERS")
        self.lbl_sidebar_title.setObjectName("sectionTitle")
        lay_card_params.addWidget(self.lbl_sidebar_title)

        self.lbl_z_force = QLabel("Z-axis Force (kg):")
        self.input_z_force = QLineEdit("0.5")
        lay_card_params.addWidget(self.create_form_row(self.input_z_force, self.lbl_z_force))

        self.lbl_x_nozzle_offset = QLabel("X Nozzle Offset:")
        self.input_x_nozzle_offset = QLineEdit("0.0")
        lay_card_params.addWidget(self.create_form_row(self.input_x_nozzle_offset, self.lbl_x_nozzle_offset))

        self.lbl_x_spool_offset = QLabel("X Spool Offset:")
        self.input_x_spool_offset = QLineEdit("0.0")
        lay_card_params.addWidget(self.create_form_row(self.input_x_spool_offset, self.lbl_x_spool_offset))

        self.lbl_y_offset = QLabel("Y Offset:")
        self.input_y_offset = QLineEdit("0.0")
        lay_card_params.addWidget(self.create_form_row(self.input_y_offset, self.lbl_y_offset))

        lay_sidebar.addWidget(card_params)

        self.btn_generate_gcode = QPushButton("Generate G-code")
        self.btn_generate_gcode.setObjectName("sliceActionButton")
        lay_sidebar.addWidget(self.btn_generate_gcode)

        self.btn_machine_limits = QPushButton("Machine Limieten")
        self.btn_machine_limits.setObjectName("secondaryActionButton")
        lay_sidebar.addWidget(self.btn_machine_limits)

        lay_sidebar.addStretch()

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

        # G-code Customization (moved from settings)
        card_gcode = QFrame()
        card_gcode.setObjectName("sectionCard")
        lay_card_gcode = QVBoxLayout(card_gcode)
        lay_card_gcode.setContentsMargins(10, 10, 10, 10)
        lay_card_gcode.setSpacing(10)

        self.lbl_gcode_custom = QLabel("G-CODE CUSTOMIZATION")
        self.lbl_gcode_custom.setObjectName("sectionTitle")
        lay_card_gcode.addWidget(self.lbl_gcode_custom)

        self.lbl_start_gcode = QLabel("Start G-code:")
        self.txt_start_gcode = QTextEdit()
        self.txt_start_gcode.setPlainText("G28 ; Home all axes")
        self.txt_start_gcode.setMaximumHeight(80)

        self.lbl_end_gcode = QLabel("End G-code:")
        self.txt_end_gcode = QTextEdit()
        self.txt_end_gcode.setPlainText("M30 ; Program end")
        self.txt_end_gcode.setMaximumHeight(80)

        lay_card_gcode.addWidget(self.lbl_start_gcode)
        lay_card_gcode.addWidget(self.txt_start_gcode)
        lay_card_gcode.addWidget(self.lbl_end_gcode)
        lay_card_gcode.addWidget(self.txt_end_gcode)

        right_layout.addWidget(card_gcode)

        # Add to splitter
        self.splitter.addWidget(self.sidebar_left)
        self.splitter.addWidget(center_widget)
        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(1, 1)

    def create_form_row(self, widget_right, text_label):
        row = QWidget(); lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 2, 0, 2)
        text_label.setObjectName("formLabel")
        widget_right.setFixedWidth(80)
        lay.addWidget(text_label)
        lay.addStretch()
        lay.addWidget(widget_right)
        return row

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
        self.lbl_gcode_custom.setText(tx.get("lbl_gcode_custom", "G-CODE CUSTOMIZATION"))
        self.lbl_start_gcode.setText(tx.get("lbl_start_gcode", "Start G-code:"))
        self.lbl_end_gcode.setText(tx.get("lbl_end_gcode", "End G-code:"))

        self.lbl_sidebar_title.setText(tx.get("lbl_modifiers", "MODIFIERS"))
        self.lbl_z_force.setText(tx.get("lbl_z_force", "Z-axis Force (kg):"))
        self.lbl_x_nozzle_offset.setText(tx.get("lbl_x_nozzle_offset", "X Nozzle Offset:"))
        self.lbl_x_spool_offset.setText(tx.get("lbl_x_spool_offset", "X Spool Offset:"))
        self.lbl_y_offset.setText(tx.get("lbl_y_offset", "Y Offset:"))
        self.btn_generate_gcode.setText(tx.get("btn_generate_gcode", "Generate G-code"))
        self.btn_machine_limits.setText(tx.get("btn_machine_limits", "Machine Limieten"))
