from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget,
    QComboBox, QMessageBox, QCheckBox, QTextEdit
)

from coil_winder.backend.arduino_worker import ArduinoWorker

AXIS_INDEX = {
    "Rotatie As 1": 0,
    "X As 2": 1,
    "Y As 3": 2,
    "Z As 4": 3,
}


# =========================
# SETTINGS TAB
# =========================
class MachineSettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Axis list
        self.axis_list = QListWidget()
        self.axis_list.addItems(list(AXIS_INDEX.keys()))
        self.axis_list.clicked.connect(self.load_selected_axis)
        layout.addWidget(self.axis_list)

        # Form layout
        form_layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.unit_mode_combo = QComboBox()
        self.unit_mode_combo.addItems(["mm", "deg"])
        self.unit_mode_combo.currentTextChanged.connect(self.update_unit_labels)

        self.step_unit_label = QLabel("Steps per unit")
        self.step_unit_input = QLineEdit()
        self.max_speed_label = QLabel("Max speed (steps/s)")
        self.max_speed_input = QLineEdit()
        self.max_accel_label = QLabel("Max acceleration (steps/s²)")
        self.max_accel_input = QLineEdit()
        self.max_travel_label = QLabel("Max travel (mm)")
        self.max_travel_input = QLineEdit()
        self.homing_checkbox = QCheckBox("Homing enabled")

        # Add widgets
        form_layout.addWidget(QLabel("As naam"))
        form_layout.addWidget(self.name_input)

        form_layout.addWidget(QLabel("Unit mode"))
        form_layout.addWidget(self.unit_mode_combo)

        form_layout.addWidget(self.step_unit_label)
        form_layout.addWidget(self.step_unit_input)

        form_layout.addWidget(self.max_speed_label)
        form_layout.addWidget(self.max_speed_input)

        form_layout.addWidget(self.max_accel_label)
        form_layout.addWidget(self.max_accel_input)

        form_layout.addWidget(self.max_travel_label)
        form_layout.addWidget(self.max_travel_input)

        form_layout.addWidget(self.homing_checkbox)

        self.save_btn = QPushButton("Opslaan")
        form_layout.addWidget(self.save_btn)

        self.status_label = QLabel("Status: niets opgeslagen")
        form_layout.addWidget(self.status_label)

        layout.addLayout(form_layout)

        # Axis data defaults (indexed)
        self.axis_data = {
            0: {"name": "Rotatie As 1", "unit_mode": "deg", "steps_per_unit": "100",
                "speed": "800", "accel": "400", "max_travel": "360", "homing_enabled": True},
            1: {"name": "X As 2", "unit_mode": "mm", "steps_per_unit": "200",
                "speed": "800", "accel": "400", "max_travel": "200", "homing_enabled": True},
            2: {"name": "Y As 3", "unit_mode": "mm", "steps_per_unit": "200",
                "speed": "800", "accel": "400", "max_travel": "200", "homing_enabled": True},
            3: {"name": "Z As 4", "unit_mode": "mm", "steps_per_unit": "100",
                "speed": "800", "accel": "400", "max_travel": "150", "homing_enabled": True},
        }

        self.save_btn.clicked.connect(self.save_axis_data)

        if self.axis_list.count() > 0:
            self.axis_list.setCurrentRow(0)
        self.load_selected_axis()

    def load_selected_axis(self):
        row = self.axis_list.currentRow()
        if row < 0:
            return

        data = self.axis_data.get(row, {})

        self.name_input.setText(data.get("name", ""))
        self.unit_mode_combo.setCurrentText(data.get("unit_mode", "mm"))
        self.step_unit_input.setText(data.get("steps_per_unit", ""))
        self.max_speed_input.setText(data.get("speed", "800"))
        self.max_accel_input.setText(data.get("accel", "400"))
        self.max_travel_input.setText(data.get("max_travel", "0"))
        self.homing_checkbox.setChecked(data.get("homing_enabled", True))

        self.update_unit_labels()

    def save_axis_data(self):
        row = self.axis_list.currentRow()
        if row < 0:
            return

        unit_mode = self.unit_mode_combo.currentText()

        self.axis_data[row] = {
            "name": self.name_input.text(),
            "unit_mode": unit_mode,
            "steps_per_unit": self.step_unit_input.text(),
            "speed": self.max_speed_input.text(),
            "accel": self.max_accel_input.text(),
            "max_travel": self.max_travel_input.text(),
            "homing_enabled": self.homing_checkbox.isChecked()
        }

        self.axis_list.currentItem().setText(self.axis_data[row]["name"])
        self.status_label.setText(f"As {self.axis_data[row]['name']} opgeslagen")
        self.update_unit_labels()

    def update_unit_labels(self):
        mode = self.unit_mode_combo.currentText()
        if mode == "mm":
            self.step_unit_label.setText("Steps per mm")
            self.max_travel_label.setText("Max travel (mm)")
        else:
            self.step_unit_label.setText("Steps per deg")
            self.max_travel_label.setText("Max travel (deg)")
        self.max_speed_label.setText("Max speed (steps/sec)")
        self.max_accel_label.setText("Max acceleration (steps/sec²)")


# =========================
# CONTROL TAB
# =========================
class MachineControlTab(QWidget):
    req_send = Signal(str)

    def __init__(self, settings_tab: MachineSettingsTab, worker: ArduinoWorker):
        super().__init__()
        self.settings_tab = settings_tab
        self.worker = worker

        self.req_send.connect(self.worker.send_line)
        self.worker.line_received.connect(self.on_line_received)

        layout = QVBoxLayout()
        self.setLayout(layout)

        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("As"))
        self.axis_combo = QComboBox()
        for axis in AXIS_INDEX.keys():
            self.axis_combo.addItem(axis)
        axis_row.addWidget(self.axis_combo)
        layout.addLayout(axis_row)

        grid = QHBoxLayout()
        left = QVBoxLayout()

        self.position_input = QLineEdit("0")
        left.addWidget(QLabel("Positie (units)"))
        left.addWidget(self.position_input)

        self.speed_input = QLineEdit()
        left.addWidget(QLabel("Speed (steps/s)"))
        left.addWidget(self.speed_input)

        self.accel_input = QLineEdit()
        left.addWidget(QLabel("Accel (steps/s²)"))
        left.addWidget(self.accel_input)

        grid.addLayout(left)

        right = QVBoxLayout()
        right.addWidget(QLabel("Console"))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(160)
        right.addWidget(self.console)

        grid.addLayout(right)
        layout.addLayout(grid)

        btns = QHBoxLayout()
        self.start_btn = QPushButton("Start (MOVE)")
        self.stop_btn = QPushButton("Stop")
        self.estop_btn = QPushButton("E-STOP")
        self.resume_btn = QPushButton("Resume")
        self.status_btn = QPushButton("Status")
        self.setspu_btn = QPushButton("Set SPU")
        self.home_btn = QPushButton("Home")

        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.estop_btn)
        btns.addWidget(self.resume_btn)
        btns.addWidget(self.status_btn)
        btns.addWidget(self.setspu_btn)
        btns.addWidget(self.home_btn)

        layout.addLayout(btns)

        self.state_label = QLabel("State: idle")
        layout.addWidget(self.state_label)

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(lambda: self.req_send.emit("STOP"))
        self.estop_btn.clicked.connect(lambda: self.req_send.emit("ESTOP"))
        self.resume_btn.clicked.connect(lambda: self.req_send.emit("RESUME"))
        self.status_btn.clicked.connect(lambda: self.req_send.emit("STATUS"))
        self.setspu_btn.clicked.connect(self.on_setspu)
        self.home_btn.clicked.connect(self.on_home)

        self.axis_combo.currentTextChanged.connect(self._load_defaults_for_axis)
        self._load_defaults_for_axis(self.axis_combo.currentText())

    def _axis_index(self) -> int:
        return AXIS_INDEX[self.axis_combo.currentText()]

    def _load_defaults_for_axis(self, axis_name: str):
        row = self._axis_index()
        data = self.settings_tab.axis_data.get(row, {})
        self.speed_input.setText(data.get("speed", "800"))
        self.accel_input.setText(data.get("accel", "400"))

        axis = self._axis_index()
        if self.worker.is_connected:
            self.req_send.emit(f"DIR,{axis},1")

    def on_start(self):
        try:
            axis = self._axis_index()
            pos = float(self.position_input.text())
            speed = float(self.speed_input.text())
            accel = float(self.accel_input.text())
            max_travel = float(self.settings_tab.axis_data[self._axis_index()].get("max_travel", 0))

            # absolute travel check
            current_pos = 0  # later kan je actuele positie van Arduino ophalen
            target = current_pos + pos
            if target > max_travel or target < 0:
                QMessageBox.warning(self, "Error", f"Positie overschrijdt max travel ({max_travel})")
                return

            self.req_send.emit(f"MOVE,{axis},{pos},{speed},{accel}")
        except Exception as e:
            QMessageBox.warning(self, "MOVE fout", str(e))

    def on_setspu(self):
        try:
            axis = self._axis_index()
            row = self._axis_index()
            spu = float(self.settings_tab.axis_data.get(row, {}).get("steps_per_unit", "0"))
            self.req_send.emit(f"SETSPU,{axis},{spu}")
        except Exception as e:
            QMessageBox.warning(self, "SETSPU fout", str(e))

    def on_home(self):
        try:
            axis = self._axis_index()
            row = self._axis_index()
            homing_enabled = self.settings_tab.axis_data.get(row, {}).get("homing_enabled", True)

            if not homing_enabled:
                QMessageBox.information(self, "Homing uitgeschakeld",
                                        f"Homing voor {self.axis_combo.currentText()} staat uit.")
                return

            self.req_send.emit(f"HOME,{axis}")
        except Exception as e:
            QMessageBox.warning(self, "HOME fout", str(e))

    def on_line_received(self, line: str):
        self.console.append(line)
        self.console.ensureCursorVisible()  # auto scroll

        if line.startswith("ACK,MOVE"):
            self.state_label.setText("State: running")
        elif line.startswith("DONE,MOVE"):
            self.state_label.setText("State: done")
        elif line.startswith("ACK,HOME"):
            self.state_label.setText("State: homing")
        elif line.startswith("DONE,HOME"):
            self.state_label.setText("State: homed")
        elif line.startswith("OK,STOPPING"):
            self.state_label.setText("State: stopping")
        elif line.startswith("OK,ESTOP"):
            self.state_label.setText("State: ESTOP")
        elif line.startswith("OK,RESUME"):
            self.state_label.setText("State: idle")
        elif line.startswith("ERR,"):
            self.state_label.setText(f"State: error ({line})")