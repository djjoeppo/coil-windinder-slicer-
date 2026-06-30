# ui/tabs/settings_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QComboBox, QHBoxLayout, QTextEdit
from PySide6.QtCore import Qt

class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.inputs = {}
        self.init_ui()
        
    def init_ui(self):
        self.setObjectName("settingsPage")
        lay_page_settings = QVBoxLayout(self)
        lay_page_settings.setContentsMargins(40, 40, 40, 40)
        lay_page_settings.setSpacing(20)

        # Viewer Settings
        card_viewer = QFrame()
        card_viewer.setObjectName("sectionCard")
        card_viewer.setFixedWidth(450)
        lay_card_viewer = QVBoxLayout(card_viewer)
        lay_card_viewer.setContentsMargins(20, 20, 20, 20)
        lay_card_viewer.setSpacing(15)

        self.sec_settings_title = QLabel(); self.sec_settings_title.setObjectName("sectionTitle")
        lay_card_viewer.addWidget(self.sec_settings_title)
        
        self.lbl_t_res = QLabel(); self.inputs["t_res"] = QLineEdit("32")
        self.lbl_p_res = QLabel(); self.inputs["p_res"] = QLineEdit("64")
        
        self.lbl_theme = QLabel()
        self.combo_theme = QComboBox()
        self.combo_theme.setFixedWidth(120)
        self.combo_theme.addItems(["Dark Mode", "Light Mode"]) # Temporarily add to avoid empty
        self.combo_theme.currentIndexChanged.connect(self.main_window.apply_orca_theme)
        
        self.lbl_lang = QLabel()
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Nederlands", "English"])
        self.combo_lang.setFixedWidth(120)
        self.combo_lang.currentTextChanged.connect(self.main_window.change_language)
        
        self.lbl_units = QLabel("Units:")
        self.combo_units = QComboBox()
        self.combo_units.addItems(["mm", "inch"])
        self.combo_units.setFixedWidth(120)
        
        lay_card_viewer.addWidget(self.create_form_row(self.inputs["t_res"], self.lbl_t_res))
        lay_card_viewer.addWidget(self.create_form_row(self.inputs["p_res"], self.lbl_p_res))
        
        lay_card_viewer.addWidget(self.create_dropdown_row(self.combo_theme, self.lbl_theme))
        lay_card_viewer.addWidget(self.create_dropdown_row(self.combo_lang, self.lbl_lang))
        lay_card_viewer.addWidget(self.create_dropdown_row(self.combo_units, self.lbl_units))
        
        lay_page_settings.addWidget(card_viewer, 0, Qt.AlignHCenter | Qt.AlignTop)

        # G-code Settings
        card_gcode = QFrame()
        card_gcode.setObjectName("sectionCard")
        card_gcode.setFixedWidth(450)
        lay_card_gcode = QVBoxLayout(card_gcode)
        lay_card_gcode.setContentsMargins(20, 20, 20, 20)
        lay_card_gcode.setSpacing(15)

        self.lbl_gcode_title = QLabel("G-CODE CUSTOMIZATION")
        self.lbl_gcode_title.setObjectName("sectionTitle")
        lay_card_gcode.addWidget(self.lbl_gcode_title)

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

        lay_page_settings.addWidget(card_gcode, 0, Qt.AlignHCenter | Qt.AlignTop)
        
        lay_page_settings.addStretch()

    def create_form_row(self, widget_right, text_label):
        row = QWidget(); lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 2, 0, 2)
        text_label.setObjectName("formLabel")
        widget_right.setFixedWidth(80)
        lay.addWidget(text_label)
        lay.addStretch()
        lay.addWidget(widget_right)
        return row
        
    def create_dropdown_row(self, combo, label):
        row = QWidget(); lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 2, 0, 2)
        label.setObjectName("formLabel")
        lay.addWidget(label); lay.addStretch(); lay.addWidget(combo)
        return row

    def retranslate_ui(self, tx):
        curr_theme_idx = self.combo_theme.currentIndex() if self.combo_theme.count() > 0 else 0
        
        self.sec_settings_title.setText(tx["sec_settings"])
        self.lbl_t_res.setText(tx["lbl_t_res"])
        self.lbl_p_res.setText(tx["lbl_p_res"])
        self.lbl_theme.setText(tx["lbl_theme"])
        self.lbl_lang.setText(tx["lbl_lang"])
        
        self.combo_theme.blockSignals(True)
        self.combo_theme.clear()
        self.combo_theme.addItem(tx["theme_dark"])
        self.combo_theme.addItem(tx["theme_light"])
        self.combo_theme.setCurrentIndex(curr_theme_idx if curr_theme_idx >= 0 else 0)
        self.combo_theme.blockSignals(False)
        
        self.lbl_units.setText(tx.get("lbl_units", "Units:"))
        self.lbl_gcode_title.setText(tx.get("lbl_gcode_custom", "G-CODE CUSTOMIZATION"))
        self.lbl_start_gcode.setText(tx.get("lbl_start_gcode", "Start G-code:"))
        self.lbl_end_gcode.setText(tx.get("lbl_end_gcode", "End G-code:"))
