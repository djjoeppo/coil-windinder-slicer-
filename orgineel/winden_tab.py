import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog
)
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtCore import Slot

class WindenTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Winden")

        layout = QVBoxLayout()

        # Input velden
        self.wire_d_input = QLineEdit()
        self.spool_width_input = QLineEdit()
        self.layers_input = QLineEdit()
        self.inner_d_input = QLineEdit()
        self.resistance_input = QLineEdit()

        double_validator = QDoubleValidator(0, 1000, 3)
        int_validator = QIntValidator(1, 1000)

        self.wire_d_input.setValidator(double_validator)
        self.spool_width_input.setValidator(double_validator)
        self.inner_d_input.setValidator(double_validator)
        self.layers_input.setValidator(int_validator)
        self.resistance_input.setValidator(double_validator)

        # Labels
        layout.addWidget(QLabel("Draaddiameter (mm)"))
        layout.addWidget(self.wire_d_input)
        layout.addWidget(QLabel("Spoelbreedte (mm)"))
        layout.addWidget(self.spool_width_input)
        layout.addWidget(QLabel("Aantal lagen (optioneel)"))
        layout.addWidget(self.layers_input)
        layout.addWidget(QLabel("Binnen diameter spoel (mm)"))
        layout.addWidget(self.inner_d_input)
        layout.addWidget(QLabel("Gewenste weerstand Ω (optioneel)"))
        layout.addWidget(self.resistance_input)

        # Buttons
        self.calc_btn = QPushButton("Bereken windingen")
        self.calc_btn.clicked.connect(self.calculate)
        self.gcode_btn = QPushButton("Genereer G-code")
        self.gcode_btn.clicked.connect(self.generate_gcode)
        layout.addWidget(self.calc_btn)
        layout.addWidget(self.gcode_btn)

        # Resultaat
        self.result_label = QLabel("Resultaten verschijnen hier")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

        # Interne opslag
        self.calc_result = None
        self.coil_data = None  # Voor ontvangst van Coil-tab

    @Slot(dict)
    def update_from_coil(self, coil_data: dict):
        """Ontvangt coil-data van Coil-tab"""
        self.coil_data = coil_data
        self.wire_d_input.setText(str(coil_data.get("wire_d", "")))
        self.spool_width_input.setText(str(coil_data.get("outer_diameter", "")))
        self.layers_input.setText(str(coil_data.get("total_turns", 1) // max(int(coil_data.get("turns_per_layer", 1)),1)))
        self.inner_d_input.setText(str(coil_data.get("inner_diameter", "")))
        self.resistance_input.setText(str(coil_data.get("resistance", "")))

        self.result_label.setText(f"Ready to wind: {coil_data.get('total_turns', '-') } windingen")

    def calculate(self):
        try:
            wire_d = float(self.wire_d_input.text().strip())
            spool_width = float(self.spool_width_input.text().strip())
            inner_d = float(self.inner_d_input.text().strip())
            layers_text = self.layers_input.text().strip()
            resistance_text = self.resistance_input.text().strip()

            # Bereken aantal lagen op basis van weerstand als die is opgegeven
            if resistance_text:
                desired_r = float(resistance_text)
                resistivity = 0.0175  # Ω*mm²/m voor koper, kan uit Coil-tab komen
                wire_area = math.pi * (wire_d/2)**2  # mm²
                # Lengte draad = R*A/ρ
                total_length = desired_r * wire_area / resistivity  # in mm
                turns_per_layer = max(int(spool_width / wire_d), 1)
                layer_circ = math.pi * inner_d
                layers = max(int(total_length / (turns_per_layer * layer_circ)), 1)
            else:
                layers = int(layers_text) if layers_text else 1
                turns_per_layer = max(int(spool_width / wire_d), 1)
                total_length = 0
                for layer in range(layers):
                    layer_d = inner_d + wire_d * 2 * layer
                    circumference = math.pi * layer_d
                    total_length += circumference * turns_per_layer

            total_turns = turns_per_layer * layers
            self.calc_result = {
                "wire_d": wire_d,
                "spool_width": spool_width,
                "layers": layers,
                "inner_d": inner_d,
                "turns_per_layer": turns_per_layer,
                "total_turns": total_turns,
                "total_length": total_length/1000  # meter
            }

            self.result_label.setText(
                f"Windingen per laag: {turns_per_layer}\n"
                f"Totaal windingen: {total_turns}\n"
                f"Aantal lagen: {layers}\n"
                f"Totale draadlengte: {total_length/1000:.2f} m"
            )

        except ValueError as e:
            QMessageBox.warning(self, "Input fout", f"Ongeldige waarde: {e}")
            self.calc_result = None

    def generate_gcode(self):
        if not self.calc_result:
            QMessageBox.warning(self, "Geen berekening", "Bereken eerst de windingen!")
            return

        try:
            gcode_lines = ["G21 ; mm", "G90 ; absolute positioning"]

            wire_d = self.calc_result["wire_d"]
            turns_per_layer = self.calc_result["turns_per_layer"]
            layers = self.calc_result["layers"]
            inner_d = self.calc_result["inner_d"]

            # Constante nozzle afstand en Z druk
            nozzle_y = 10.0  # mm, afstand nozzle -> spoel
            z_height = 0.5   # mm, druk op draad
            feedrate = 500   # mm/min, pas aan naar je machine

            # Beginpositie
            gcode_lines.append(f"G0 A0.00 X0.00 Y{nozzle_y:.2f} Z{z_height:.2f}")

            for layer in range(layers):
                y = nozzle_y  # Y blijft constant per jouw uitleg
                for turn in range(turns_per_layer):
                    x = turn * wire_d
                    a = 360 * (turn + layer * turns_per_layer)  # 360° per draai
                    gcode_lines.append(f"G1 A{a:.2f} X{x:.2f} Y{y:.2f} Z{z_height:.2f} F{feedrate}")

            path, _ = QFileDialog.getSaveFileName(self, "Opslaan als", "", "G-code files (*.gcode)")
            if not path:
                return

            with open(path, "w") as f:
                f.write("\n".join(gcode_lines))

            QMessageBox.information(self, "G-code opgeslagen", f"G-code succesvol opgeslagen:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Fout bij G-code generatie: {e}")