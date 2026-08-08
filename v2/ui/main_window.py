# ui/main_window.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, QStackedWidget
from core.config import TRANSLATIONS
from ui.tabs.prepare_tab import PrepareTab
from ui.tabs.preview_tab import PreviewTab
from ui.tabs.device_tab import DeviceTab
from ui.tabs.settings_tab import SettingsTab
from core.controller import CoilController

class CoilAppLayout(QWidget):
    def __init__(self):
        super().__init__()
        self.current_lang = "NL"
        self.current_theme = "dark"
        self.nav_buttons = []
        
        # UI must be initialized before Controller
        self.init_ui()
        
        # Link the controller (Audit: Ensuring all widgets exist before controller binds)
        self.controller = CoilController(self)

    def init_ui(self):
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)

        # Top Workflow Bar
        self.top_bar = QFrame()
        self.top_bar.setObjectName("topBar")
        lay_top = QHBoxLayout(self.top_bar)
        lay_top.setContentsMargins(10, 0, 10, 0)
        lay_top.setSpacing(5)

        self.btn_nav_prepare = QPushButton()
        self.btn_nav_preview = QPushButton()
        self.btn_nav_device = QPushButton()
        self.btn_nav_settings = QPushButton()
        
        self.nav_buttons = [self.btn_nav_prepare, self.btn_nav_preview, self.btn_nav_device, self.btn_nav_settings]
        for idx, btn in enumerate(self.nav_buttons):
            btn.setCheckable(True)
            btn.setObjectName("navBtn")
            btn.clicked.connect(lambda checked, i=idx: self.switch_main_page(i))
            lay_top.addWidget(btn)

        lay_top.addStretch()
        window_layout.addWidget(self.top_bar)

        # Initialiseer de losse tabbladen
        self.tab_prepare = PrepareTab(self)
        self.tab_preview = PreviewTab(self)
        self.tab_device = DeviceTab(self)
        self.tab_settings = SettingsTab(self)

        # Centrale Pagina Manager
        self.main_pages = QStackedWidget()
        self.main_pages.addWidget(self.tab_prepare)
        self.main_pages.addWidget(self.tab_preview)
        self.main_pages.addWidget(self.tab_device)
        self.main_pages.addWidget(self.tab_settings)
        window_layout.addWidget(self.main_pages)

        # Startcondities
        self.switch_main_page(0)
        self.update_ui_text()
        self.apply_orca_theme()

    def switch_main_page(self, index):
        self.main_pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def change_language(self, text):
        self.current_lang = "NL" if text == "Nederlands" else "EN"
        self.update_ui_text()

    def change_units(self, unit_text):
        # Notify the prepare tab to update unit displays
        if hasattr(self, 'tab_prepare'):
            self.tab_prepare.on_unit_changed(unit_text)

    def update_ui_text(self):
        tx = TRANSLATIONS.get(self.current_lang, {})
        if not tx: return
        
        # Load and set icons for each button with fallback handling
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QMessageBox
        from core.config import get_resource_path
        import os
        from pathlib import Path

        icon_mapping = {
            self.btn_nav_prepare: ("prepare.png", tx.get("nav_prepare", "PREPARE")),
            self.btn_nav_preview: ("preview.png", tx.get("nav_preview", "PREVIEW")),
            self.btn_nav_device: ("device.png", tx.get("nav_device", "DEVICE")),
            self.btn_nav_settings: ("settings.png", tx.get("nav_settings", "SETTINGS"))
        }

        # We only want to trigger warning dialogs at startup to prevent multiple sequential blockers inside translation switch
        show_startup_warnings = not hasattr(self, '_warnings_triggered')
        missing_icons = []

        for btn, (filename, text) in icon_mapping.items():
            btn.setText(text)

            # Use discoverable paths
            icon_path = None
            try:
                icon_path = get_resource_path(os.path.join("icons", filename))
            except Exception:
                pass

            if icon_path and os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            else:
                # Icon not found, store in list for a single unified warning pop-up at startup
                btn.setIcon(QIcon()) # empty icon so it is text-only seamlessly
                expected_dir = str(Path(__file__).resolve().parent.parent / "assets" / "icons")
                expected_filepath = os.path.join(expected_dir, filename)
                missing_icons.append((filename, expected_filepath))

        if missing_icons and show_startup_warnings:
            self._warnings_triggered = True
            details = "\n".join([f"- '{fn}' op locatie:\n  {p}\n" for fn, p in missing_icons])

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Afbeeldingen/Icoontjes missen!")
            msg_box.setText(f"Waarschuwing: De volgende icoontjes konden niet worden geladen:\n\n{details}")
            msg_box.setInformativeText("U kunt gewoon doorwerken. De knoppen tonen tijdelijk alleen tekst.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        
        self.tab_prepare.retranslate_ui(tx)
        self.tab_preview.retranslate_ui(tx)
        self.tab_device.retranslate_ui(tx)
        self.tab_settings.retranslate_ui(tx)

    def apply_orca_theme(self):
        # Check de index van de dropdown in de settings tab
        theme_idx = self.tab_settings.combo_theme.currentIndex()
        if theme_idx == 1:
            self.current_theme = "light"
            self.setStyleSheet("""
                QWidget { background-color: #f8f9fa; color: #212529; font-family: 'Segoe UI', Arial; font-size: 12px; }
                QFrame#topBar { background-color: #e9ecef; border-bottom: 1px solid #ced4da; min-height: 45px; max-height: 45px; }
                QPushButton#navBtn { background: transparent; color: #495057; border: none; padding: 0px 20px; font-weight: bold; font-size: 13px; height: 45px; }
                QPushButton#navBtn:hover { color: #000000; background-color: #dee2e6; }
                QPushButton#navBtn:checked { color: #ffffff; background-color: #007edc; }
                QWidget#sidebarContainer { background-color: #e9ecef; border-right: 1px solid #ced4da; }
                QWidget#settingsPage { background-color: #f8f9fa; }
                QFrame#sectionCard { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 4px; padding: 12px; }
                QLabel#sectionTitle { color: #000000; font-weight: bold; font-size: 12px; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; margin-bottom: 8px; }
                QLabel#formLabel { color: #495057; }
                QPushButton#editMaterialsBtn { background-color: #f1f3f5; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px; }
                QPushButton#editMaterialsBtn:hover { background-color: #dee2e6; }
                QLineEdit { background-color: #ffffff; color: #212529; border: 1px solid #ced4da; border-radius: 3px; padding: 3px 5px; }
                QLineEdit:focus { border: 1px solid #007edc; }
                QComboBox { background-color: #f1f3f5; color: #212529; border: 1px solid #ced4da; border-radius: 3px; padding: 3px 5px; }
                QComboBox::drop-down { border: none; }
                QScrollArea#paramScroll { border: none; background-color: transparent; }
                QPushButton#sliceActionButton { background-color: #007edc; color: white; font-weight: bold; font-size: 13px; padding: 10px; border: none; border-radius: 4px; }
                QPushButton#sliceActionButton:hover { background-color: #0096ff; }
                QPushButton#secondaryActionButton { background-color: #e9ecef; color: #212529; padding: 7px; border: 1px solid #ced4da; border-radius: 4px; }
                QPushButton#secondaryActionButton:hover { background-color: #dee2e6; }
            """)
        elif theme_idx == 2:
            self.current_theme = "test"
            self.setStyleSheet("""
                QWidget { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Arial; font-size: 12px; }
                QFrame#topBar { background-color: #1e293b; border-bottom: 2px solid #0ea5e9; min-height: 48px; max-height: 48px; }
                QPushButton#navBtn { background: transparent; color: #94a3b8; border: none; padding: 0px 22px; font-weight: bold; font-size: 13px; height: 48px; }
                QPushButton#navBtn:hover { color: #f8fafc; background-color: #334155; }
                QPushButton#navBtn:checked { color: #ffffff; background-color: #0ea5e9; border-radius: 4px; height: 40px; margin: 4px 0px; }
                QWidget#sidebarContainer { background-color: #1e293b; border-right: 1px solid #334155; }
                QWidget#settingsPage { background-color: #0f172a; }
                QFrame#sectionCard { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px; }
                QLabel#sectionTitle { color: #38bdf8; font-weight: bold; font-size: 13px; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
                QLabel#formLabel { color: #94a3b8; font-weight: 500; }
                QPushButton#editMaterialsBtn { background-color: #334155; border: 1px solid #475569; border-radius: 4px; font-size: 12px; color: #f8fafc; }
                QPushButton#editMaterialsBtn:hover { background-color: #475569; border-color: #38bdf8; }
                QLineEdit { background-color: #0f172a; color: #f8fafc; border: 1px solid #475569; border-radius: 4px; padding: 3px 5px; }
                QLineEdit:focus { border: 1px solid #38bdf8; }
                QComboBox { background-color: #334155; color: #f8fafc; border: 1px solid #475569; border-radius: 4px; padding: 3px 5px; }
                QComboBox::drop-down { border: none; }
                QScrollArea#paramScroll { border: none; background-color: transparent; }
                QPushButton#sliceActionButton { background-color: #0ea5e9; color: white; font-weight: bold; font-size: 13px; padding: 10px; border: none; border-radius: 4px; }
                QPushButton#sliceActionButton:hover { background-color: #38bdf8; }
                QPushButton#secondaryActionButton { background-color: #334155; color: #f8fafc; padding: 7px; border: 1px solid #475569; border-radius: 4px; }
                QPushButton#secondaryActionButton:hover { background-color: #475569; border-color: #38bdf8; }
            """)
        else:
            self.current_theme = "dark"
            self.setStyleSheet("""
                QWidget { background-color: #1e2022; color: #e3e4e5; font-family: 'Segoe UI', Arial; font-size: 12px; }
                QFrame#topBar { background-color: #181a1b; border-bottom: 1px solid #2d2f31; min-height: 45px; max-height: 45px; }
                QPushButton#navBtn { background: transparent; color: #9da3a8; border: none; padding: 0px 20px; font-weight: bold; font-size: 13px; height: 45px; }
                QPushButton#navBtn:hover { color: #ffffff; background-color: #242628; }
                QPushButton#navBtn:checked { color: #ffffff; background-color: #007edc; }
                QWidget#sidebarContainer { background-color: #181a1b; border-right: 1px solid #2d2f31; }
                QWidget#settingsPage { background-color: #1e2022; }
                QFrame#sectionCard { background-color: #222527; border: 1px solid #2d2f31; border-radius: 4px; padding: 12px; }
                QLabel#sectionTitle { color: #ffffff; font-weight: bold; font-size: 12px; border-bottom: 1px solid #383b3d; padding-bottom: 4px; margin-bottom: 8px; }
                QLabel#formLabel { color: #9da3a8; }
                QPushButton#editMaterialsBtn { background-color: #2c2f31; border: 1px solid #383b3d; border-radius: 3px; font-size: 12px; }
                QPushButton#editMaterialsBtn:hover { background-color: #383b3d; }
                QLineEdit { background-color: #111213; color: #ffffff; border: 1px solid #383b3d; border-radius: 3px; padding: 3px 5px; }
                QLineEdit:focus { border: 1px solid #007edc; }
                QComboBox { background-color: #2c2f31; color: #ffffff; border: 1px solid #383b3d; border-radius: 3px; padding: 3px 5px; }
                QComboBox::drop-down { border: none; }
                QScrollArea#paramScroll { border: none; background-color: transparent; }
                QPushButton#sliceActionButton { background-color: #007edc; color: white; font-weight: bold; font-size: 13px; padding: 10px; border: none; border-radius: 4px; }
                QPushButton#sliceActionButton:hover { background-color: #0096ff; }
                QPushButton#secondaryActionButton { background-color: #2c2f31; color: #e3e4e5; padding: 7px; border: 1px solid #383b3d; border-radius: 4px; }
                QPushButton#secondaryActionButton:hover { background-color: #383b3d; }
            """)
