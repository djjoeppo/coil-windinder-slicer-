# ui/tabs/prepare_tab.py
import os
import json
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, QComboBox, QScrollArea, QPushButton, QSplitter, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QColor
from core.config import TRANSLATIONS, get_resource_path
from ui.components import Dummy3DViewer
from ui.dialogs import MaterialsPopUp

class PrepareTab(QWidget):
    def __init__(self, main_window, wire_colors=None, spool_colors=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.inputs = {}
        self.wire_color_combos = []

        # JSON Database pad bepalen
        self.json_path = get_resource_path("materials.json")
        self.materials_database = []

        self.wire_colors = wire_colors if wire_colors else {
            "Koper": (0.85, 0.38, 0.15), "Goud": (0.95, 0.75, 0.1), "Zilver": (0.75, 0.75, 0.75),
            "Rood": (0.85, 0.15, 0.15), "Blauw": (0.15, 0.45, 0.75), "Groen": (0.15, 0.7, 0.3),
            "Paars": (0.5, 0.1, 0.6), "Zwart": (0.1, 0.1, 0.1), "Wit": (0.95, 0.95, 0.95)
        }
        self.spool_colors = spool_colors if spool_colors else {
            "Standaard (Donker)": (0.2, 0.2, 0.2), "Aluminium": (0.7, 0.73, 0.75),
            "Messing": (0.78, 0.66, 0.25), "Plastic Zwart": (0.08, 0.09, 0.1), "Plastic Wit": (0.9, 0.9, 0.9)
        }

        self.init_ui()
        self.load_materials_into_combobox()

    def init_ui(self):
        lay_prepare = QHBoxLayout(self)
        lay_prepare.setContentsMargins(0, 0, 0, 0)
        lay_prepare.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        lay_prepare.addWidget(self.splitter)

        sidebar_container = QWidget()
        sidebar_container.setMinimumWidth(250)
        sidebar_container.setMaximumWidth(600)
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(12)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("paramScroll")
        scroll_content = QWidget()
        lay_scroll = QVBoxLayout(scroll_content)
        lay_scroll.setContentsMargins(0, 0, 0, 0)
        lay_scroll.setSpacing(15)

        # --- SECTIE: SPOEL ---
        card_spool = QFrame(); card_spool.setObjectName("sectionCard")
        lay_card_spool = QVBoxLayout(card_spool)
        self.sec_spool_title = QLabel(); self.sec_spool_title.setObjectName("sectionTitle")
        lay_card_spool.addWidget(self.sec_spool_title)

        self.lbl_inner_d = QLabel(); self.inputs["i"] = QLineEdit("35")
        self.lbl_hole_d = QLabel(); self.inputs["hole"] = QLineEdit("0")
        self.lbl_flange_d = QLabel(); self.inputs["f"] = QLineEdit("90")
        self.lbl_width = QLabel(); self.inputs["b"] = QLineEdit("50")
        self.lbl_spool_color = QLabel(); self.combo_spool_color = QComboBox()

        lay_card_spool.addWidget(self.create_form_row(self.inputs["i"], self.lbl_inner_d))
        lay_card_spool.addWidget(self.create_form_row(self.inputs["hole"], self.lbl_hole_d))
        lay_card_spool.addWidget(self.create_form_row(self.inputs["f"], self.lbl_flange_d))
        lay_card_spool.addWidget(self.create_form_row(self.inputs["b"], self.lbl_width))

        lay_card_spool.addWidget(self.lbl_spool_color)
        for c_name, rgb in self.spool_colors.items():
            pix = QPixmap(14, 14); pix.fill(QColor.fromRgbF(*rgb))
            self.combo_spool_color.addItem(QIcon(pix), c_name)
        lay_card_spool.addWidget(self.combo_spool_color)
        lay_scroll.addWidget(card_spool)

        # --- SECTIE: WIKKELING ---
        card_coil = QFrame(); card_coil.setObjectName("sectionCard")
        lay_card_coil = QVBoxLayout(card_coil)
        self.sec_coil_title = QLabel(); self.sec_coil_title.setObjectName("sectionTitle")
        lay_card_coil.addWidget(self.sec_coil_title)

        self.lbl_material = QLabel()
        self.combo_material = QComboBox()
        self.combo_material.setFixedWidth(160)

        self.btn_edit_materials = QPushButton("📝")
        self.btn_edit_materials.setObjectName("editMaterialsBtn")
        self.btn_edit_materials.setFixedSize(24, 24)
        self.btn_edit_materials.clicked.connect(self.open_materials_popup)

        self.lbl_wire_d = QLabel()
        self.input_wire_d_display = QLineEdit()
        self.input_wire_d_display.setFixedWidth(80)
        self.input_wire_d_display.setReadOnly(True)
        self.input_wire_d_display.setAlignment(Qt.AlignRight)

        self.lbl_layers = QLabel(); self.inputs["l"] = QLineEdit("2")
        self.lbl_wire_type = QLabel(); self.combo_wire_type = QComboBox()
        self.combo_wire_type.addItems(["Single Wire", "Multi-Wire"])
        self.combo_wire_type.currentIndexChanged.connect(self.toggle_multi_wire_fields)

        self.lbl_num_wires = QLabel(); self.inputs["num_wires"] = QLineEdit("5")
        self.inputs["num_wires"].textChanged.connect(self.generate_dynamic_wire_color_menus)
        self.scroll_colors = QScrollArea(); self.scroll_colors.setWidgetResizable(True)
        self.scroll_colors.setMaximumHeight(150)
        self.scroll_colors_container = QWidget(); self.scroll_colors_layout = QVBoxLayout(self.scroll_colors_container)
        self.scroll_colors.setWidget(self.scroll_colors_container)

        self.lbl_single_color = QLabel(); self.combo_wire_color = QComboBox()

        for c_name, rgb in self.wire_colors.items():
            pix = QPixmap(14, 14); pix.fill(QColor.fromRgbF(*rgb))
            self.combo_wire_color.addItem(QIcon(pix), c_name)

        self.combo_material.currentTextChanged.connect(self.on_material_dropdown_changed)

        row_mat = QWidget(); lay_m = QHBoxLayout(row_mat); lay_m.setContentsMargins(0,2,0,2)
        self.lbl_material.setObjectName("formLabel")
        lay_m.addWidget(self.lbl_material)
        lay_m.addStretch()
        lay_m.addWidget(self.combo_material)
        lay_m.addWidget(self.btn_edit_materials)
        lay_card_coil.addWidget(row_mat)

        lay_card_coil.addWidget(self.create_form_row(self.input_wire_d_display, self.lbl_wire_d))
        lay_card_coil.addWidget(self.create_form_row(self.inputs["l"], self.lbl_layers))
        lay_card_coil.addWidget(self.lbl_wire_type); lay_card_coil.addWidget(self.combo_wire_type)
        lay_card_coil.addWidget(self.create_form_row(self.inputs["num_wires"], self.lbl_num_wires))
        lay_card_coil.addWidget(self.scroll_colors)
        lay_card_coil.addWidget(self.lbl_single_color); lay_card_coil.addWidget(self.combo_wire_color)

        lay_scroll.addWidget(card_coil)
        self.lbl_num_wires.hide(); self.inputs["num_wires"].hide(); self.scroll_colors.hide()

        lay_scroll.addStretch()
        scroll_area.setWidget(scroll_content)
        sidebar_layout.addWidget(scroll_area)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        sidebar_layout.addWidget(self.progress_bar)

        self.btn_update = QPushButton()
        self.btn_update.setObjectName("sliceActionButton")
        sidebar_layout.addWidget(self.btn_update)

        self.btn_toggle_spool = QPushButton()
        self.btn_toggle_spool.setObjectName("secondaryActionButton")
        sidebar_layout.addWidget(self.btn_toggle_spool)

        self.viewer = Dummy3DViewer()

        self.splitter.addWidget(sidebar_container)
        self.splitter.addWidget(self.viewer)
        self.splitter.setStretchFactor(1, 1)

    def set_calculating(self, is_calculating):
        self.btn_update.setEnabled(not is_calculating)
        if is_calculating:
            self.progress_bar.show()
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.hide()

    def create_form_row(self, widget_right, text_label):
        row = QWidget(); lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 2, 0, 2)
        text_label.setObjectName("formLabel")
        widget_right.setFixedWidth(80)
        lay.addWidget(text_label)
        lay.addStretch()
        lay.addWidget(widget_right)
        return row

    def load_materials_into_combobox(self):
        self.combo_material.blockSignals(True)
        self.combo_material.clear()

        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self.materials_database = json.load(f)
            except Exception as e:
                print(f"Fout bij inladen dropdown JSON: {e}")
                self.materials_database = []
        else:
            self.materials_database = []

        for mat in self.materials_database:
            self.combo_material.addItem(mat["name"])

        self.combo_material.blockSignals(False)

        if self.combo_material.count() > 0:
            self.on_material_dropdown_changed(self.combo_material.currentText())
        else:
            self.input_wire_d_display.setText("0.0 mm")

    def on_material_dropdown_changed(self, selected_name):
        for mat in self.materials_database:
            if mat["name"] == selected_name:
                d = float(mat.get("diameter", 0.0))
                i = float(mat.get("insulation", 0.0))
                total_d = d + i
                self.input_wire_d_display.setText(f"{total_d:.2f} mm")
                return

    def open_materials_popup(self):
        is_light = (self.main_window.current_theme == "light")
        popup = MaterialsPopUp(self, is_light_theme=is_light, lang=self.main_window.current_lang)
        popup.exec()
        self.load_materials_into_combobox()

    def toggle_multi_wire_fields(self, index):
        if index == 1:
            self.lbl_num_wires.show(); self.inputs["num_wires"].show(); self.scroll_colors.show()
            self.lbl_single_color.hide(); self.combo_wire_color.hide()
            self.generate_dynamic_wire_color_menus()
        else:
            self.lbl_num_wires.hide(); self.inputs["num_wires"].hide(); self.scroll_colors.hide()
            self.lbl_single_color.show(); self.combo_wire_color.show()

    def generate_dynamic_wire_color_menus(self):
        if not hasattr(self, 'scroll_colors_layout') or self.scroll_colors_layout is None: return
        for i in reversed(range(self.scroll_colors_layout.count())):
            widget = self.scroll_colors_layout.itemAt(i).widget()
            if widget is not None: widget.setParent(None)
        self.wire_color_combos.clear()

        if self.combo_wire_type.currentIndex() != 1: return
        try:
            num_wires = int(self.inputs["num_wires"].text())
            if num_wires < 1: num_wires = 1
            if num_wires > 24: num_wires = 24
        except ValueError: return

        tx = TRANSLATIONS[self.main_window.current_lang]
        for idx in range(num_wires):
            row_widget = QWidget(); row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(f"{tx['wire_idx']} {idx+1}:")
            lbl.setStyleSheet("color: #9da3a8; font-size: 11px;")
            combo = QComboBox()
            for c_name, rgb in self.wire_colors.items():
                pix = QPixmap(14, 14); pix.fill(QColor.fromRgbF(*rgb))
                combo.addItem(QIcon(pix), c_name)
            combo.setCurrentIndex(idx % len(self.wire_colors))
            row_layout.addWidget(lbl); row_layout.addStretch(); row_layout.addWidget(combo)
            self.scroll_colors_layout.addWidget(row_widget)
            self.wire_color_combos.append(combo)

    def retranslate_ui(self, tx):
        self.sec_spool_title.setText(tx["sec_spool"])
        self.sec_coil_title.setText(tx["sec_coil"])
        self.lbl_inner_d.setText(tx["lbl_inner_d"])
        self.lbl_hole_d.setText(tx["lbl_hole_d"])
        self.lbl_flange_d.setText(tx["lbl_flange_d"])
        self.lbl_width.setText(tx["lbl_width"])
        self.lbl_spool_color.setText(tx["lbl_spool_color"])
        self.lbl_material.setText(tx["lbl_material"])
        self.lbl_wire_d.setText(tx["lbl_wire_d"])
        self.lbl_layers.setText(tx["lbl_layers"])
        self.lbl_wire_type.setText(tx["lbl_wire_type"])
        self.lbl_num_wires.setText(tx["lbl_num_wires"])
        self.lbl_single_color.setText(tx["lbl_single_color"])
        self.btn_update.setText(tx["btn_update"])
        self.btn_toggle_spool.setText(tx["btn_toggle_spool"])

        current_text = self.combo_material.currentText()
        self.load_materials_into_combobox()
        self.combo_material.setCurrentText(current_text)
