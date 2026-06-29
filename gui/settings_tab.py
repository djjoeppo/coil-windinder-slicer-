# ui/tabs/settings_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QComboBox, QHBoxLayout
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

        card_settings = QFrame()
        card_settings.setObjectName("sectionCard")
        card_settings.setFixedWidth(450)
        lay_card_settings = QVBoxLayout(card_settings)
        lay_card_settings.setContentsMargins(20, 20, 20, 20)
        lay_card_settings.setSpacing(15)

        self.sec_settings_title = QLabel(); self.sec_settings_title.setObjectName("sectionTitle")
        lay_card_settings.addWidget(self.sec_settings_title)
        
        self.lbl_t_res = QLabel(); self.inputs["t_res"] = QLineEdit("32")
        self.lbl_p_res = QLabel(); self.inputs["p_res"] = QLineEdit("64")
        
        self.lbl_theme = QLabel()
        self.combo_theme = QComboBox()
        self.combo_theme.setFixedWidth(120)
        self.combo_theme.currentIndexChanged.connect(self.main_window.apply_orca_theme)
        
        self.lbl_lang = QLabel()
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Nederlands", "English"])
        self.combo_lang.setFixedWidth(120)
        self.combo_lang.currentTextChanged.connect(self.main_window.change_language)
        
        lay_card_settings.addWidget(self.create_form_row(self.inputs["t_res"], self.lbl_t_res))
        lay_card_settings.addWidget(self.create_form_row(self.inputs["p_res"], self.lbl_p_res))
        
        row_theme = QWidget(); lay_rt = QHBoxLayout(row_theme); lay_rt.setContentsMargins(0,2,0,2)
        self.lbl_theme.setObjectName("formLabel")
        lay_rt.addWidget(self.lbl_theme); lay_rt.addStretch(); lay_rt.addWidget(self.combo_theme)
        lay_card_settings.addWidget(row_theme)
        
        row_lang = QWidget(); lay_rl = QHBoxLayout(row_lang); lay_rl.setContentsMargins(0,2,0,2)
        self.lbl_lang.setObjectName("formLabel")
        lay_rl.addWidget(self.lbl_lang); lay_rl.addStretch(); lay_rl.addWidget(self.combo_lang)
        lay_card_settings.addWidget(row_lang)
        
        lay_page_settings.addWidget(card_settings, 0, Qt.AlignHCenter | Qt.AlignTop)
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