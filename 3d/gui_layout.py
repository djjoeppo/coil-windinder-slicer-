# Verander dit bovenin gui_layout.py:
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTabWidget, QComboBox, QScrollArea)
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QPen
from .viewer_3d import Coil3DViewer          # <-- Punt toegevoegd voor huidige map
from .translation_db import TRANSLATIONS      # <-- Punt toegevoegd voor huidige map

# Naam veranderd naar CoilAppLayout, passend bij jouw main.py
class CoilAppLayout(QWidget):
    # Accepteert nu netjes de dictionaries uit jouw main.py
    def __init__(self, wire_colors, spool_colors):
        super().__init__()
        self.inputs = {}
        self.wire_color_combos = []
        self.current_lang = "NL"
        
        # Neem de kleuren over uit de main.py argumenten
        self.wire_colors = wire_colors
        self.spool_colors = spool_colors
        
        self.init_ui()

    def create_wire_type_icons(self):
        pix1 = QPixmap(32, 16); pix1.fill(Qt.transparent)
        p1 = QPainter(pix1); p1.setRenderHint(QPainter.Antialiasing)
        p1.setPen(QPen(QColor("#e67e22"), 5, Qt.SolidLine, Qt.RoundCap))
        p1.drawLine(4, 8, 28, 8); p1.end()
        
        pix2 = QPixmap(32, 16); pix2.fill(Qt.transparent)
        p2 = QPainter(pix2); p2.setRenderHint(QPainter.Antialiasing)
        p2.setPen(QPen(QColor("#2980b9"), 2, Qt.SolidLine, Qt.RoundCap))
        p2.drawLine(4, 3, 28, 3); p2.drawLine(4, 8, 28, 8); p2.drawLine(4, 13, 28, 13); p2.end()
        return QIcon(pix1), QIcon(pix2)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        sidebar = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # --- TAB: SPOEL ---
        self.tab_spool = QWidget(); lay_spool = QVBoxLayout(self.tab_spool)
        self.lbl_inner_d = QLabel(); self.inputs["i"] = QLineEdit("35")
        self.lbl_hole_d = QLabel(); self.inputs["hole"] = QLineEdit("0")
        self.lbl_flange_d = QLabel(); self.inputs["f"] = QLineEdit("90")
        self.lbl_width = QLabel(); self.inputs["b"] = QLineEdit("50")
        self.lbl_spool_color = QLabel(); self.combo_spool_color = QComboBox()
        for c_name, rgb in self.spool_colors.items():
            pix = QPixmap(16, 16); pix.fill(QColor.fromRgbF(*rgb))
            self.combo_spool_color.addItem(QIcon(pix), c_name)
        lay_spool.addWidget(self.lbl_inner_d); lay_spool.addWidget(self.inputs["i"])
        lay_spool.addWidget(self.lbl_hole_d); lay_spool.addWidget(self.inputs["hole"])
        lay_spool.addWidget(self.lbl_flange_d); lay_spool.addWidget(self.inputs["f"])
        lay_spool.addWidget(self.lbl_width); lay_spool.addWidget(self.inputs["b"])
        lay_spool.addWidget(self.lbl_spool_color); lay_spool.addWidget(self.combo_spool_color)
        lay_spool.addStretch(); self.tabs.addTab(self.tab_spool, "")

        # --- TAB: WIKKELING ---
        self.tab_coil = QWidget(); lay_coil = QVBoxLayout(self.tab_coil)
        self.lbl_wire_d = QLabel(); self.inputs["w"] = QLineEdit("1.0")
        self.lbl_layers = QLabel(); self.inputs["l"] = QLineEdit("2")
        self.lbl_wire_type = QLabel(); self.combo_wire_type = QComboBox()
        ico_single, ico_multi = self.create_wire_type_icons()
        self.combo_wire_type.addItem(ico_single, "Single Wire")
        self.combo_wire_type.addItem(ico_multi, "Multi-Wire")
        
        self.lbl_num_wires = QLabel(); self.inputs["num_wires"] = QLineEdit("5")
        self.scroll_colors = QScrollArea(); self.scroll_colors.setWidgetResizable(True)
        self.scroll_colors_container = QWidget(); self.scroll_colors_layout = QVBoxLayout(self.scroll_colors_container)
        self.scroll_colors.setWidget(self.scroll_colors_container)
        
        self.lbl_single_color = QLabel(); self.combo_wire_color = QComboBox()
        for c_name, rgb in self.wire_colors.items():
            pix = QPixmap(16, 16); pix.fill(QColor.fromRgbF(*rgb))
            self.combo_wire_color.addItem(QIcon(pix), c_name)
            
        lay_coil.addWidget(self.lbl_wire_d); lay_coil.addWidget(self.inputs["w"])
        lay_coil.addWidget(self.lbl_layers); lay_coil.addWidget(self.inputs["l"])
        lay_coil.addWidget(self.lbl_wire_type); lay_coil.addWidget(self.combo_wire_type)
        lay_coil.addWidget(self.lbl_num_wires); lay_coil.addWidget(self.inputs["num_wires"])
        lay_coil.addWidget(self.scroll_colors)
        lay_coil.addWidget(self.lbl_single_color); lay_coil.addWidget(self.combo_wire_color)
        lay_coil.addStretch(); self.tabs.addTab(self.tab_coil, "")
        
        self.lbl_num_wires.hide(); self.inputs["num_wires"].hide(); self.scroll_colors.hide()

        # --- TAB: SETTINGS ---
        self.tab_settings = QWidget(); lay_settings = QVBoxLayout(self.tab_settings)
        self.lbl_t_res = QLabel(); self.inputs["t_res"] = QLineEdit("32")
        self.lbl_p_res = QLabel(); self.inputs["p_res"] = QLineEdit("64")
        self.lbl_dens = QLabel(); self.inputs["dens"] = QLineEdit("8.96")
        self.lbl_theme = QLabel(); self.combo_theme = QComboBox(); self.combo_theme.addItems(["Dark Mode", "Light Mode"])
        
        self.lbl_lang = QLabel()
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Nederlands", "English"])
        self.combo_lang.currentTextChanged.connect(self.change_language)
        
        lay_settings.addWidget(self.lbl_t_res); lay_settings.addWidget(self.inputs["t_res"])
        lay_settings.addWidget(self.lbl_p_res); lay_settings.addWidget(self.inputs["p_res"])
        lay_settings.addWidget(self.lbl_dens); lay_settings.addWidget(self.inputs["dens"])
        lay_settings.addWidget(self.lbl_theme); lay_settings.addWidget(self.combo_theme)
        lay_settings.addWidget(self.lbl_lang); lay_settings.addWidget(self.combo_lang)
        lay_settings.addStretch(); self.tabs.addTab(self.tab_settings, "")

        sidebar.addWidget(self.tabs)
        self.lbl_info = QLabel(); self.lbl_info.setObjectName("infoLabel")
        sidebar.addWidget(self.lbl_info)
        
        self.btn_update = QPushButton(); self.btn_update.setObjectName("updateButton")
        sidebar.addWidget(self.btn_update)
        
        self.btn_toggle_spool = QPushButton(); self.btn_toggle_spool.setObjectName("toggleSpoolButton")
        sidebar.addWidget(self.btn_toggle_spool)
        sidebar.addStretch()

        self.viewer = Coil3DViewer()
        main_layout.addLayout(sidebar, 1); main_layout.addWidget(self.viewer, 4)
        
        self.update_ui_text()

    def change_language(self, text):
        self.current_lang = "NL" if text == "Nederlands" else "EN"
        self.update_ui_text()
        self.generate_dynamic_wire_color_menus()

    def update_ui_text(self):
        tx = TRANSLATIONS[self.current_lang]
        self.tabs.setTabText(0, tx["tab_spool"])
        self.tabs.setTabText(1, tx["tab_coil"])
        self.tabs.setTabText(2, tx["tab_settings"])
        
        self.lbl_inner_d.setText(f"<b>{tx['lbl_inner_d']}</b>")
        self.lbl_hole_d.setText(f"<b>{tx['lbl_hole_d']}</b>")
        self.lbl_flange_d.setText(f"<b>{tx['lbl_flange_d']}</b>")
        self.lbl_width.setText(f"<b>{tx['lbl_width']}</b>")
        self.lbl_spool_color.setText(f"<b>{tx['lbl_spool_color']}</b>")
        self.lbl_wire_d.setText(f"<b>{tx['lbl_wire_d']}</b>")
        self.lbl_layers.setText(f"<b>{tx['lbl_layers']}</b>")
        self.lbl_wire_type.setText(f"<b>{tx['lbl_wire_type']}</b>")
        self.lbl_num_wires.setText(f"<b>{tx['lbl_num_wires']}</b>")
        self.lbl_single_color.setText(f"<b>{tx['lbl_single_color']}</b>")
        self.lbl_t_res.setText(f"<b>{tx['lbl_t_res']}</b>")
        self.lbl_p_res.setText(f"<b>{tx['lbl_p_res']}</b>")
        self.lbl_dens.setText(f"<b>{tx['lbl_dens']}</b>")
        self.lbl_theme.setText(f"<b>{tx['lbl_theme']}</b>")
        self.lbl_lang.setText(f"<b>{tx['lbl_lang']}</b>")
        
        self.btn_update.setText(tx["btn_update"])
        self.btn_toggle_spool.setText(tx["btn_toggle_spool"])

    def toggle_multi_wire_fields(self, index):
        if index == 1:
            self.lbl_num_wires.show(); self.inputs["num_wires"].show(); self.scroll_colors.show()
            self.lbl_single_color.hide(); self.combo_wire_color.hide()
            self.generate_dynamic_wire_color_menus()
        else:
            self.lbl_num_wires.hide(); self.inputs["num_wires"].hide(); self.scroll_colors.hide()
            self.lbl_single_color.show(); self.combo_wire_color.show()

    def generate_dynamic_wire_color_menus(self):
        if not hasattr(self, 'scroll_colors_layout') or self.scroll_colors_layout is None:
            return
            
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

        tx = TRANSLATIONS[self.current_lang]
        self.scroll_colors_layout.addWidget(QLabel(f"<b>{tx['wire_each']}</b>"))
        for idx in range(num_wires):
            row_widget = QWidget(); row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(f"{tx['wire_idx']} {idx+1}:"); lbl.setMinimumWidth(55)
            combo = QComboBox()
            for c_name, rgb in self.wire_colors.items():
                pix = QPixmap(16, 16); pix.fill(QColor.fromRgbF(*rgb))
                combo.addItem(QIcon(pix), c_name)
            combo.setCurrentIndex(idx % len(self.wire_colors))
            row_layout.addWidget(lbl); row_layout.addWidget(combo)
            self.scroll_colors_layout.addWidget(row_widget)
            self.wire_color_combos.append(combo)

    def apply_theme(self, theme_name):
        if theme_name == "Light Mode":
            self.viewer.setBackgroundColor("#e0e0e0")
            self.setStyleSheet("""
                QWidget { background: #f5f5f5; color: #222; font-family: 'Segoe UI'; }
                QTabWidget::pane { border: 1px solid #ccc; background: #e9e9e9; }
                QTabBar::tab { background: #ddd; color: #222; padding: 12px; }
                QTabBar::tab:selected { background: #e67e22; color: white; }
                QLineEdit, QComboBox { background: #ffffff; color: #111; border: 1px solid #bbb; padding: 5px; }
                QPushButton#updateButton { background: #e67e22; color: white; padding: 15px; font-weight: bold; border: none; }
                QPushButton#updateButton:hover { background: #d35400; }
                QPushButton#toggleSpoolButton { background: #2980b9; color: white; padding: 10px; font-weight: bold; border: none; margin-top: 5px; }
                QPushButton#toggleSpoolButton:hover { background: #3498db; }
                QLabel#infoLabel { color: #008855; font-weight: bold; background: #fff; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
                QScrollArea { border: 1px solid #ccc; background: #f5f5f5; }
            """)
        else:
            self.viewer.setBackgroundColor("#111111")
            self.setStyleSheet("""
                QWidget { background: #181818; color: #eee; font-family: 'Segoe UI'; }
                QTabWidget::pane { border: 1px solid #444; background: #222; }
                QTabBar::tab { background: #333; color: #eee; padding: 12px; }
                QTabBar::tab:selected { background: #e67e22; color: white; }
                QLineEdit, QComboBox { background: #111; color: #00ffaa; border: 1px solid #555; padding: 5px; }
                QPushButton#updateButton { background: #e67e22; color: white; padding: 15px; font-weight: bold; border: none; }
                QPushButton#updateButton:hover { background: #d35400; }
                QPushButton#toggleSpoolButton { background: #2c3e50; color: white; padding: 10px; font-weight: bold; border: none; margin-top: 5px; }
                QPushButton#toggleSpoolButton:hover { background: #34495e; }
                QLabel#infoLabel { color: #00ffaa; font-weight: bold; background: #111; padding: 10px; border-radius: 4px; }
                QScrollArea { border: 1px solid #333; background: #181818; }
            """)