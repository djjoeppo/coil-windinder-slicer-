from __future__ import annotations

import json
import math
import serial.tools.list_ports

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QComboBox,
    QMessageBox
)
from PySide6.QtGui import QDoubleValidator, QIntValidator

from coil_winder.backend.arduino_worker import ArduinoWorker
from coil_winder.ui.tabs.machine_tabs import MachineSettingsTab, MachineControlTab
from coil_winder.ui.tabs.winden_tab import WindenTab

DATA_FILE = "materials.json"


def load_materials():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_materials(materials):
    with open(DATA_FILE, "w") as f:
        json.dump(materials, f, indent=4)


def calculate(material, inner_diameter, width, layers):
    wire_d = material["diameter"] + material["isolation"]

    if wire_d <= 0:
        raise ValueError("Draaddiameter is ongeldig")

    turns_per_layer = max(int(width / wire_d), 1)
    total_turns = turns_per_layer * layers
    total_length = 0

    for layer in range(layers):
        layer_d = inner_diameter + (wire_d * 1.866 * layer)
        circumference = math.pi * layer_d
        total_length += circumference * turns_per_layer

    total_length_m = total_length / 1000
    resistance = total_length_m * material["ohm_per_meter"]
    outer_diameter = inner_diameter + 2 * layers * wire_d

    return {
        "turns_per_layer": turns_per_layer,
        "total_turns": total_turns,
        "length": total_length_m,
        "resistance": resistance,
        "inner_diameter": inner_diameter,
        "outer_diameter": outer_diameter
    }


class MainWindow(QWidget):
    # Arduino signals
    req_connect = Signal(str, int, float)
    req_disconnect = Signal()
    req_send = Signal(str)

    # ✅ nieuw signaal om coil-data naar WindenTab te sturen
    coil_calculated = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coil Winder PRO (motion planner)")

        self.materials = load_materials()

        # Arduino worker thread
        self.worker_thread = QThread(self)
        self.arduino_worker = ArduinoWorker()
        self.arduino_worker.moveToThread(self.worker_thread)

        self.req_connect.connect(self.arduino_worker.connect_port)
        self.req_disconnect.connect(self.arduino_worker.disconnect_port)
        self.req_send.connect(self.arduino_worker.send_line)

        self.arduino_worker.connected.connect(self.on_connected)
        self.arduino_worker.disconnected.connect(self.on_disconnected)
        self.arduino_worker.connection_error.connect(self.on_connection_error)

        self.worker_thread.start()

        # UI
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tabs.addTab(self.coil_tab(), "Coil")
        self.tabs.addTab(self.material_tab(), "Materialen")
        self.tabs.addTab(self.machine_tab(), "Machine")
        # Winden tab instantiëren en signaal koppelen
        self.winden_tab = WindenTab()
        self.coil_calculated.connect(self.winden_tab.update_from_coil)
        self.tabs.addTab(self.winden_tab, "Winden")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.refresh_materials()

    def closeEvent(self, event):
        try:
            self.req_disconnect.emit()
        except Exception:
            pass
        self.worker_thread.quit()
        self.worker_thread.wait(1500)
        super().closeEvent(event)

    # --------------------- Coil tab ---------------------
    def coil_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.material_combo = QComboBox()

        # input velden
        self.inner_diameter_input = QLineEdit()
        self.outer_diameter_input = QLineEdit()
        self.width_input = QLineEdit()
        self.layers_input = QLineEdit()
        self.voltage_input = QLineEdit()
        self.resistance_input = QLineEdit()

        # validators
        validator = QDoubleValidator(0, 10000, 3)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.inner_diameter_input.setValidator(validator)
        self.outer_diameter_input.setValidator(validator)
        self.width_input.setValidator(validator)
        self.voltage_input.setValidator(validator)
        self.resistance_input.setValidator(validator)
        self.layers_input.setValidator(QIntValidator(0, 10000))

        self.result = QLabel("Resultaten verschijnen hier")

        calc_btn = QPushButton("Bereken")
        calc_btn.clicked.connect(self.calculate_coil)

        layout.addWidget(QLabel("Materiaal"))
        layout.addWidget(self.material_combo)

        layout.addWidget(QLabel("Binnen diameter (mm, optioneel)"))
        layout.addWidget(self.inner_diameter_input)

        layout.addWidget(QLabel("Buiten diameter (mm, optioneel)"))
        layout.addWidget(self.outer_diameter_input)

        layout.addWidget(QLabel("Spoel breedte (mm)"))
        layout.addWidget(self.width_input)

        layout.addWidget(QLabel("Aantal lagen (optioneel)"))
        layout.addWidget(self.layers_input)

        layout.addWidget(QLabel("Spanning V (optioneel)"))
        layout.addWidget(self.voltage_input)

        layout.addWidget(QLabel("Weerstand Ω (optioneel)"))
        layout.addWidget(self.resistance_input)

        layout.addWidget(calc_btn)
        layout.addWidget(self.result)

        tab.setLayout(layout)
        return tab

    def calculate_coil(self):
        try:
            if not self.materials:
                raise ValueError("Geen materialen beschikbaar")

            # Pak alleen de naam uit de combo (alles vóór de eerste " (")
            selected_name = self.material_combo.currentText().split(" (")[0]

            # Zoek het dict-object in de lijst
            material = next((m for m in self.materials if m["name"] == selected_name), None)

            if material is None:
                 QMessageBox.warning(self, "Fout", "Geselecteerd materiaal niet gevonden")
                 return

            inner_d_text = self.inner_diameter_input.text()
            outer_d_text = self.outer_diameter_input.text()
            width = float(self.width_input.text()) if self.width_input.text() else 0
            layers = int(self.layers_input.text()) if self.layers_input.text() else 0
            voltage = float(self.voltage_input.text()) if self.voltage_input.text() else None
            resistance_input = float(self.resistance_input.text()) if self.resistance_input.text() else None

            wire_d = material["diameter"] + material["isolation"]

            inner_diameter = float(inner_d_text) if inner_d_text else None
            outer_diameter = float(outer_d_text) if outer_d_text else None

            if layers == 0:
                if inner_diameter is not None and outer_diameter is not None:
                    layers = max(int((outer_diameter - inner_diameter) / (2 * wire_d)), 1)
                else:
                    layers = 1

            if inner_diameter is None and outer_diameter is not None:
                inner_diameter = outer_diameter - 2 * layers * wire_d
            if outer_diameter is None and inner_diameter is not None:
                outer_diameter = inner_diameter + 2 * layers * wire_d
            if inner_diameter is None and outer_diameter is None:
                inner_diameter = 10
                outer_diameter = inner_diameter + 2 * layers * wire_d

            r = calculate(material, inner_diameter, width, layers)

            if resistance_input:
                r["resistance"] = resistance_input

            if voltage:
                current = voltage / r["resistance"] if r["resistance"] > 0 else 0
                power = voltage * current
            else:
                current = None
                power = None

            text = (
                f"Windingen per laag: {r['turns_per_layer']}\n"
                f"Totaal windingen: {r['total_turns']}\n"
                f"Aantal lagen: {layers}\n"
                f"Draadlengte: {r['length']:.2f} m\n"
                f"Weerstand: {r['resistance']:.2f} Ω\n"
                f"Binnen diameter: {r['inner_diameter']:.2f} mm\n"
                f"Buiten diameter: {r['outer_diameter']:.2f} mm\n"
            )
            if voltage:
                text += f"Spanning: {voltage:.2f} V\n"
            if current is not None:
                text += f"Stroom: {current:.2f} A\n"
            if power is not None:
                text += f"Vermogen: {power:.2f} W\n"

            self.result.setText(text)
            # ✅ stuur data naar WindenTab
            self.coil_calculated.emit(r)

        except Exception as e:
            QMessageBox.warning(self, "Fout", str(e))

    # --------------------- Material tab ---------------------
    def material_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()
        self.diam_input = QLineEdit()
        self.iso_input = QLineEdit()
        self.ohm_input = QLineEdit()
        self.current_input = QLineEdit()
        self.voltage_input_mat = QLineEdit()
        self.min_spool_input = QLineEdit()
        self.material_list = QListWidget()
        self.material_list.clicked.connect(self.load_selected_material)

        form = QVBoxLayout()

        self.name_input = QLineEdit()
        self.diam_input = QLineEdit()
        self.iso_input = QLineEdit()
        self.ohm_input = QLineEdit()
        self.current_input = QLineEdit()
        self.voltage_input_mat = QLineEdit()
        self.min_spool_input = QLineEdit()

        validator = QDoubleValidator(0, 10000, 3)
        validator.setNotation(QDoubleValidator.StandardNotation)

        self.diam_input.setValidator(validator)
        self.iso_input.setValidator(validator)
        self.ohm_input.setValidator(validator)
        self.current_input.setValidator(validator)
        self.voltage_input_mat.setValidator(validator)
        self.min_spool_input.setValidator(validator)

        for label, widget in [
            ("Naam", self.name_input),
            ("Diameter mm", self.diam_input),
            ("Isolatie mm", self.iso_input),
            ("Ohm per meter", self.ohm_input),
            ("Max stroom A", self.current_input),
            ("Max spanning V", self.voltage_input_mat),
            ("Minimale spoel diameter mm", self.min_spool_input),
        ]:
            form.addWidget(QLabel(label))
            form.addWidget(widget)

        add_btn = QPushButton("Nieuw")
        save_btn = QPushButton("Opslaan")
        del_btn = QPushButton("Verwijder")
        add_btn.clicked.connect(self.add_material)
        save_btn.clicked.connect(self.save_material)
        del_btn.clicked.connect(self.delete_material)

        form.addWidget(add_btn)
        form.addWidget(save_btn)
        form.addWidget(del_btn)

        layout.addWidget(self.material_list)
        layout.addLayout(form)

        tab.setLayout(layout)
        return tab

    def refresh_materials(self):
        self.material_list.clear()
        self.material_combo.clear()
        for m in self.materials:
            display_name = f"{m['name']} ({m['diameter'] + m['isolation']:.2f} mm)"
            self.material_list.addItem(display_name)
            self.material_combo.addItem(display_name)

    def load_selected_material(self):
        i = self.material_list.currentRow()
        if i < 0 or i >= len(self.materials):
            return
        m = self.materials[i]
        self.name_input.setText(m["name"])
        self.diam_input.setText(str(m["diameter"]))
        self.iso_input.setText(str(m["isolation"]))
        self.ohm_input.setText(str(m["ohm_per_meter"]))
        self.current_input.setText(str(m.get("max_current", "")))
        self.voltage_input_mat.setText(str(m.get("max_voltage", "")))
        self.min_spool_input.setText(str(m.get("min_spool", 0)))

    def add_material(self):
        self.materials.append({
            "name": "Nieuw",
            "diameter": 0.5,
            "isolation": 0.05,
            "ohm_per_meter": 0.1,
            "max_current": 1,
            "max_voltage": 5,
            "min_spool": 0
        })
        save_materials(self.materials)
        self.refresh_materials()

    def save_material(self):
        i = self.material_list.currentRow()
        if i < 0:
            return
        self.materials[i] = {
            "name": self.name_input.text(),
            "diameter": float(self.diam_input.text()),
            "isolation": float(self.iso_input.text()),
            "ohm_per_meter": float(self.ohm_input.text()),
            "max_current": float(self.current_input.text()) if self.current_input.text() else None,
            "max_voltage": float(self.voltage_input_mat.text()) if self.voltage_input_mat.text() else None,
            "min_spool": float(self.min_spool_input.text()) if self.min_spool_input.text() else 0
        }
        save_materials(self.materials)
        self.refresh_materials()

    def delete_material(self):
        i = self.material_list.currentRow()
        if i >= 0:
            del self.materials[i]
        save_materials(self.materials)
        self.refresh_materials()

    # --------------------- Machine tab ---------------------
    def machine_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        row = QHBoxLayout()
        self.com_combo = QComboBox()
        self._refresh_ports()
        row.addWidget(QLabel("COM poort"))
        row.addWidget(self.com_combo)

        self.refresh_ports_btn = QPushButton("Refresh")
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        row.addWidget(self.refresh_ports_btn)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        row.addWidget(self.connect_btn)

        layout.addLayout(row)

        self.machine_status = QLabel("Status: disconnected")
        layout.addWidget(self.machine_status)

        self.machine_tabs = QTabWidget()
        self.settings_tab = MachineSettingsTab()
        self.control_tab = MachineControlTab(self.settings_tab, self.arduino_worker)

        self.machine_tabs.addTab(self.settings_tab, "Settings")
        self.machine_tabs.addTab(self.control_tab, "Control")
        layout.addWidget(self.machine_tabs)

        tab.setLayout(layout)
        return tab

    def _refresh_ports(self):
        self.com_combo.clear()
        for p in serial.tools.list_ports.comports():
            self.com_combo.addItem(p.device)

    def on_connect_clicked(self):
        port = self.com_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Fout", "Geen COM poort geselecteerd")
            return

        if self.connect_btn.text() == "Disconnect":
            self.connect_btn.setEnabled(False)
            self.req_disconnect.emit()
            return

        self.connect_btn.setEnabled(False)
        self.req_connect.emit(port, 115200, 2.0)

    def on_connected(self, msg: str):
        self.machine_status.setText(f"Status: {msg}")
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setEnabled(True)

    def on_disconnected(self):
        self.machine_status.setText("Status: disconnected")
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)

    def on_connection_error(self, err: str):
        QMessageBox.warning(self, "Connect fout", err)
        self.machine_status.setText("Status: disconnected")
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)