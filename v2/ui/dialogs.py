# ui/dialogs.py
import os
import json
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QWidget, QFrame,
                             QListWidget, QListWidgetItem, QLabel, QLineEdit, QPushButton, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from core.config import TRANSLATIONS, get_resource_path

class MachineLimitsDialog(QDialog):
    """Dialog for configuring machine travel and force limits."""
    def __init__(self, parent=None, current_limits=None):
        super().__init__(parent)
        self.setWindowTitle("Machine Limieten")
        self.setFixedWidth(350)
        self.limits = current_limits or {
            "max_x": 200.0,
            "max_y": 100.0,
            "max_z": 15.0,
            "max_z_force": 10.0
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        grid = QGridLayout()
        layout.addLayout(grid)

        self.inputs = {}

        fields = [
            ("max_x", "Maximale travel X (mm):"),
            ("max_y", "Maximale travel Y (mm):"),
            ("max_z", "Maximale travel Z (mm):"),
            ("max_z_force", "Maximale Z-kracht (kg):")
        ]

        for i, (key, label) in enumerate(fields):
            lbl = QLabel(label)
            edit = QLineEdit(str(self.limits[key]))
            grid.addWidget(lbl, i, 0)
            grid.addWidget(edit, i, 1)
            self.inputs[key] = edit

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Opslaan")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Annuleren")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def get_values(self):
        try:
            return {
                "max_x": float(self.inputs["max_x"].text().replace(',', '.')),
                "max_y": float(self.inputs["max_y"].text().replace(',', '.')),
                "max_z": float(self.inputs["max_z"].text().replace(',', '.')),
                "max_z_force": float(self.inputs["max_z_force"].text().replace(',', '.'))
            }
        except ValueError:
            return self.limits

class MaterialsPopUp(QDialog):
    """Het pop-up scherm voor uitgebreid Materialenbeheer met JSON-koppeling"""
    def __init__(self, parent=None, is_light_theme=False, lang="NL"):
        super().__init__(parent)
        self.lang = lang
        self.is_light_theme = is_light_theme
        self.setWindowTitle("Materialenbeheer" if lang == "NL" else "Material Management")
        self.resize(750, 500)  
        self.setWindowModality(Qt.WindowModal)
        
        # JSON Database pad bepalen
        self.json_path = get_resource_path("materials.json")
        
        self.materials_data = []
        self.current_index = -1
        self.inputs = {}
        
        self.init_ui()
        self.apply_theme()
        self.load_materials_from_json()

    def get_current_unit(self):
        """Dynamic unit discovery from application tabs/parent."""
        try:
            if self.parent():
                p = self.parent()
                # PrepareTab or SettingsTab is our parent
                if hasattr(p, 'main_window'):
                    return p.main_window.tab_settings.combo_units.currentText()
                if hasattr(p, 'tab_settings'):
                    return p.tab_settings.combo_units.currentText()
        except Exception:
            pass
        return "mm"

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 1. LINKERZIJDE: De Materialenlijst
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_list_title = QLabel("Materialenbeheer" if self.lang == "NL" else "Material Management")
        lbl_list_title.setObjectName("sectionTitle")
        left_layout.addWidget(lbl_list_title)
        
        self.material_list = QListWidget()
        self.material_list.setObjectName("materialList")
        self.material_list.currentRowChanged.connect(self.on_material_selected)
        left_layout.addWidget(self.material_list)
        
        main_layout.addWidget(left_container, 2)

        # 2. RECHTERZIJDE: Het Invoerformulier (Card-styling)
        right_card = QFrame()
        right_card.setObjectName("sectionCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        double_validator = QDoubleValidator(0.0, 10000.0, 4, self)
        double_validator.setNotation(QDoubleValidator.StandardNotation)

        unit = self.get_current_unit()
        unit_suffix = "inch" if unit == "inch" else "MM"

        fields = [
            ("name", "Naam" if self.lang == "NL" else "Name", None),
            ("diameter", f"Diameter {unit_suffix}", double_validator),
            ("insulation", f"Isolatie {unit_suffix}" if self.lang == "NL" else f"Insulation {unit_suffix}", double_validator),
            ("ohm", "Ohm per meter" if self.lang == "NL" else "Ohm per meter", double_validator),
            ("max_current", "Max stroom A" if self.lang == "NL" else "Max current A", double_validator),
            ("max_voltage", "Max spanning V" if self.lang == "NL" else "Max voltage V", double_validator),
            ("min_spool_d", f"Minimale spoel diameter {unit_suffix}" if self.lang == "NL" else f"Minimum spool diameter {unit_suffix}", double_validator)
        ]

        for key, label_text, validator in fields:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            
            lbl = QLabel(label_text)
            lbl.setObjectName("formLabel")
            
            le = QLineEdit()
            if validator:
                le.setValidator(validator)
                le.setAlignment(Qt.AlignRight)
                
            row_layout.addWidget(lbl)
            row_layout.addWidget(le)
            right_layout.addWidget(row_widget)
            
            self.inputs[key] = le

        right_layout.addStretch()

        # 3. ACTIEKNOPPEN
        self.btn_new = QPushButton("Nieuw" if self.lang == "NL" else "New")
        self.btn_new.setObjectName("actionBtnNew")
        self.btn_new.clicked.connect(self.add_new_material)
        right_layout.addWidget(self.btn_new)

        self.btn_save = QPushButton("Opslaan" if self.lang == "NL" else "Save")
        self.btn_save.setObjectName("actionBtnSave")
        self.btn_save.clicked.connect(self.save_current_material)
        right_layout.addWidget(self.btn_save)

        self.btn_delete = QPushButton("Verwijder" if self.lang == "NL" else "Delete")
        self.btn_delete.setObjectName("actionBtnDelete")
        self.btn_delete.clicked.connect(self.delete_current_material)
        right_layout.addWidget(self.btn_delete)

        main_layout.addWidget(right_card, 3)

    def load_materials_from_json(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self.materials_data = json.load(f)
            except Exception as e:
                print(f"Fout bij laden materialen: {e}")
                self.materials_data = []
        else:
            self.materials_data = [
                {"name": "Koperdraad", "diameter": 0.500, "insulation": 0.050, "ohm": 0.085, "max_current": 2.5, "max_voltage": 500, "min_spool_d": 20.0},
                {"name": "Aluminiumdraad", "diameter": 0.800, "insulation": 0.060, "ohm": 0.054, "max_current": 4.0, "max_voltage": 600, "min_spool_d": 35.0}
            ]
            self.save_to_json_file()

        self.update_list_widget()

    def save_to_json_file(self):
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.materials_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Fout bij wegschrijven JSON: {e}")

    def update_list_widget(self, select_index=0):
        self.material_list.blockSignals(True)
        self.material_list.clear()
        
        unit = self.get_current_unit()

        for mat in self.materials_data:
            d = float(mat.get("diameter", 0.0))
            i = float(mat.get("insulation", 0.0))
            total_d = d + i

            if unit == "inch":
                from core.config import mm_to_awg
                awg_val = mm_to_awg(total_d)
                display_text = f"{mat['name']} {awg_val} gage"
            else:
                display_text = f"{mat['name']} {total_d:.2f} MM"
            
            item = QListWidgetItem(display_text)
            self.material_list.addItem(item)
            
        self.material_list.blockSignals(False)
        
        if self.materials_data and select_index < len(self.materials_data):
            self.material_list.setCurrentRow(select_index)
        else:
            self.clear_form_fields()

    def on_material_selected(self, index):
        if index < 0 or index >= len(self.materials_data):
            self.current_index = -1
            self.clear_form_fields()
            return
            
        self.current_index = index
        mat = self.materials_data[index]
        
        unit = self.get_current_unit()
        scale = 1.0 / 25.4 if unit == "inch" else 1.0

        d_val = float(mat.get("diameter", 0.0)) * scale
        i_val = float(mat.get("insulation", 0.0)) * scale
        min_spool_val = float(mat.get("min_spool_d", 0.0)) * scale

        self.inputs["name"].setText(str(mat["name"]))
        self.inputs["diameter"].setText(f"{d_val:.4f}".replace('.', ',') if unit == "inch" else f"{d_val:.3f}".replace('.', ','))
        self.inputs["insulation"].setText(f"{i_val:.4f}".replace('.', ',') if unit == "inch" else f"{i_val:.3f}".replace('.', ','))
        self.inputs["min_spool_d"].setText(f"{min_spool_val:.3f}".replace('.', ',') if unit == "inch" else f"{min_spool_val:.2f}".replace('.', ','))

        self.inputs["ohm"].setText(str(mat.get("ohm", 0.0)).replace('.', ','))
        self.inputs["max_current"].setText(str(mat.get("max_current", 0.0)).replace('.', ','))
        self.inputs["max_voltage"].setText(str(mat.get("max_voltage", 0.0)).replace('.', ','))

    def clear_form_fields(self):
        for le in self.inputs.values():
            le.clear()

    def parse_float(self, text):
        try:
            return float(text.replace(',', '.'))
        except ValueError:
            return 0.0

    def add_new_material(self):
        new_mat = {
            "name": "Nieuw" if self.lang == "NL" else "New",
            "diameter": 0.500,
            "insulation": 0.050,
            "ohm": 0.000,
            "max_current": 0.0,
            "max_voltage": 0.0,
            "min_spool_d": 0.0
        }
        self.materials_data.append(new_mat)
        self.save_to_json_file()
        self.update_list_widget(select_index=len(self.materials_data) - 1)

    def save_current_material(self):
        if self.current_index < 0 or self.current_index >= len(self.materials_data):
            return
            
        name_text = self.inputs["name"].text().strip()
        if not name_text:
            name_text = "Naamloos" if self.lang == "NL" else "Unnamed"

        unit = self.get_current_unit()
        scale_back = 25.4 if unit == "inch" else 1.0

        d_parsed = self.parse_float(self.inputs["diameter"].text()) * scale_back
        i_parsed = self.parse_float(self.inputs["insulation"].text()) * scale_back
        min_spool_parsed = self.parse_float(self.inputs["min_spool_d"].text()) * scale_back

        self.materials_data[self.current_index] = {
            "name": name_text,
            "diameter": d_parsed,
            "insulation": i_parsed,
            "ohm": self.parse_float(self.inputs["ohm"].text()),
            "max_current": self.parse_float(self.inputs["max_current"].text()),
            "max_voltage": self.parse_float(self.inputs["max_voltage"].text()),
            "min_spool_d": min_spool_parsed
        }
        self.save_to_json_file()
        self.update_list_widget(select_index=self.current_index)

    def delete_current_material(self):
        if self.current_index < 0 or self.current_index >= len(self.materials_data):
            return
            
        del self.materials_data[self.current_index]
        self.save_to_json_file()
        
        new_idx = max(0, self.current_index - 1)
        if not self.materials_data:
            new_idx = -1
            
        self.update_list_widget(select_index=new_idx)

    def apply_theme(self):
        if self.is_light_theme:
            self.setStyleSheet("""
                QDialog { background-color: #f8f9fa; }
                QLabel#sectionTitle { color: #000000; font-weight: bold; font-size: 14px; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; margin-bottom: 5px; }
                QLabel#formLabel { color: #495057; font-weight: 500; }
                QListWidget#materialList { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 4px; color: #212529; padding: 5px; }
                QListWidget#materialList::item { padding: 6px; border-bottom: 1px solid #f1f3f5; }
                QListWidget#materialList::item:hover { background-color: #dee2e6; border-radius: 3px; }
                QListWidget#materialList::item:selected { background-color: #007edc; color: white; border-radius: 3px; }
                QFrame#sectionCard { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 6px; }
                QLineEdit { background-color: #ffffff; color: #212529; border: 1px solid #ced4da; border-radius: 3px; padding: 4px; }
                QLineEdit:focus { border: 1px solid #007edc; }
                QPushButton { background-color: #f1f3f5; color: #212529; border: 1px solid #ced4da; border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background-color: #dee2e6; }
                QPushButton#actionBtnSave { background-color: #007edc; color: white; border: none; }
                QPushButton#actionBtnSave:hover { background-color: #0096ff; }
                QPushButton#actionBtnDelete { background-color: #dc3545; color: white; border: none; }
                QPushButton#actionBtnDelete:hover { background-color: #ff4d5e; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #1e2022; }
                QLabel#sectionTitle { color: #ffffff; font-weight: bold; font-size: 14px; border-bottom: 1px solid #383b3d; padding-bottom: 4px; margin-bottom: 5px; }
                QLabel#formLabel { color: #9da3a8; font-weight: 500; }
                QListWidget#materialList { background-color: #111213; border: 1px solid #383b3d; border-radius: 4px; color: #e3e4e5; padding: 5px; }
                QListWidget#materialList::item { padding: 6px; border-bottom: 1px solid #1a1c1d; }
                QListWidget#materialList::item:hover { background-color: #242628; border-radius: 3px; }
                QListWidget#materialList::item:selected { background-color: #007edc; color: white; border-radius: 3px; }
                QFrame#sectionCard { background-color: #222527; border: 1px solid #2d2f31; border-radius: 6px; }
                QLineEdit { background-color: #111213; color: #ffffff; border: 1px solid #383b3d; border-radius: 3px; padding: 4px; }
                QLineEdit:focus { border: 1px solid #007edc; }
                QPushButton { background-color: #2c2f31; color: #e3e4e5; border: 1px solid #383b3d; border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background-color: #383b3d; }
                QPushButton#actionBtnSave { background-color: #007edc; color: white; border: none; }
                QPushButton#actionBtnSave:hover { background-color: #0096ff; }
                QPushButton#actionBtnDelete { background-color: #b22222; color: white; border: none; }
                QPushButton#actionBtnDelete:hover { background-color: #dc3545; }
            """)
