# ui/tabs/device_tab.py
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QProgressBar, QFrame
from PySide6.QtCore import Qt, Slot
import serial.tools.list_ports
from core.machine_worker import MachineWorker

class DeviceTab(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.worker = MachineWorker()
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Sidebar for connection controls
        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        
        self.lbl_title = QLabel("Machine Control")
        self.lbl_title.setObjectName("sectionTitle")
        sidebar_layout.addWidget(self.lbl_title)
        
        # Port selection
        self.lbl_port = QLabel("Serial Port:")
        self.combo_port = QComboBox()
        self.refresh_ports()
        
        self.btn_refresh = QPushButton("Refresh Ports")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        
        sidebar_layout.addWidget(self.lbl_port)
        sidebar_layout.addWidget(self.combo_port)
        sidebar_layout.addWidget(self.btn_refresh)
        
        # Connect/Disconnect
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setObjectName("sliceActionButton")
        self.btn_connect.clicked.connect(self.toggle_connection)
        sidebar_layout.addWidget(self.btn_connect)
        
        # Status
        self.lbl_status = QLabel("Status: Disconnected")
        sidebar_layout.addWidget(self.lbl_status)
        
        sidebar_layout.addSpacing(20)

        # Limits Config
        self.btn_limits_config = QPushButton("🔧 Machine Limits Config")
        self.btn_limits_config.setObjectName("secondaryActionButton")
        self.btn_limits_config.clicked.connect(self.open_limits_dialog)
        sidebar_layout.addWidget(self.btn_limits_config)

        sidebar_layout.addSpacing(10)
        
        # Execution controls
        self.btn_send = QPushButton("Start Winding")
        self.btn_send.setEnabled(False)
        self.btn_send.clicked.connect(self.send_gcode)
        sidebar_layout.addWidget(self.btn_send)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        sidebar_layout.addWidget(self.progress_bar)

        sidebar_layout.addSpacing(20)

        # 1. HERNOEMD EN MODERNE STYLING (Oranje/Rood)
        self.btn_emergency = QPushButton("🔄 Reset Programma")
        self.btn_emergency.setFixedHeight(50)
        self.btn_emergency.setStyleSheet("""
            QPushButton {
                background-color: #d97706;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                border: 1px solid #b45309;
            }
            QPushButton:hover {
                background-color: #f59e0b;
            }
            QPushButton:pressed {
                background-color: #b45309;
            }
        """)
        self.btn_emergency.clicked.connect(self.emergency_stop)
        sidebar_layout.addWidget(self.btn_emergency)
        
        sidebar_layout.addStretch()
        
        # Main container on the right: holds the DRO dashboard and the terminal
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # --- DRO (Digital Read Out) DASHBOARD ---
        self.dro_panel = QFrame()
        self.dro_panel.setObjectName("sectionCard")

        dro_layout = QHBoxLayout(self.dro_panel)
        dro_layout.setContentsMargins(10, 10, 10, 10)
        dro_layout.setSpacing(10)

        self.dro_labels = {}
        axes_info = [
            ("x", "X-POSITION (Width)", "mm"),
            ("y", "Y-POSITION (Nozzle)", "mm"),
            ("z", "Z-POSITION (Tension)", "mm"),
            ("a", "A-ROTATION (Spool)", "°"),
            ("force", "Z-FORCE (Weight)", "kg")
        ]

        for key, name, unit in axes_info:
            box = QFrame()
            box.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
            box.setStyleSheet("background-color: rgba(0, 0, 0, 0.15); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 4px;")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(8, 8, 8, 8)
            box_layout.setSpacing(2)

            lbl_title = QLabel(name)
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_title.setStyleSheet("font-size: 9px; font-weight: bold; color: #9da3a8; text-transform: uppercase;")

            lbl_val = QLabel("0.00")
            lbl_val.setAlignment(Qt.AlignCenter)
            lbl_val.setStyleSheet("font-size: 20px; font-weight: bold; font-family: 'Courier New', monospace; color: #10b981;")

            lbl_unit = QLabel(unit)
            lbl_unit.setAlignment(Qt.AlignCenter)
            lbl_unit.setStyleSheet("font-size: 9px; color: #6b7280;")

            box_layout.addWidget(lbl_title)
            box_layout.addWidget(lbl_val)
            box_layout.addWidget(lbl_unit)

            dro_layout.addWidget(box)
            self.dro_labels[key] = (lbl_val, lbl_unit)

        right_layout.addWidget(self.dro_panel)

        # Main area for terminal
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #000; color: #0f0; font-family: monospace;")
        right_layout.addWidget(self.terminal)
        
        layout.addWidget(sidebar)
        layout.addWidget(right_container)
        
    def setup_connections(self):
        self.worker.connected.connect(self.on_connected)
        self.worker.disconnected.connect(self.on_disconnected)
        self.worker.connection_error.connect(self.on_error)
        self.worker.line_received.connect(self.on_line_received)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.send_complete.connect(self.on_send_complete)
        
    def refresh_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.combo_port.addItem(p.device)
            
    def toggle_connection(self):
        if self.worker.is_connected():
            self.worker.disconnect_port()
        else:
            port = self.combo_port.currentText()
            if port:
                self.worker.connect_port(port)
                
    def on_connected(self, msg):
        self.lbl_status.setText(f"Status: {msg}")
        self.btn_connect.setText("Disconnect")
        self.btn_send.setEnabled(True)
        self.terminal.append(f"--- Connected to {msg} ---")
        
    def on_disconnected(self):
        self.lbl_status.setText("Status: Disconnected")
        self.btn_connect.setText("Connect")
        self.btn_send.setEnabled(False)
        self.terminal.append("--- Disconnected ---")
        
    def on_error(self, err):
        self.terminal.append(f"ERROR: {err}")
        self.on_disconnected()
        
    def on_line_received(self, line):
        # Check if the line contains live positions feedback from the machine
        if self.parse_and_update_dro(line):
            # Cleanly update the GUI and prevent printing positioning updates in terminal
            return

        if not line.startswith(">>"): # Avoid double echo in terminal
             self.terminal.append(f"<< {line}")
        else:
            self.terminal.append(line)
             
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())
        
    def on_send_complete(self):
        self.terminal.append("--- Streaming Complete ---")
        self.btn_send.setEnabled(True)

    def parse_and_update_dro(self, line):
        """Parses position reports (like GRBL or key-value format) to update the DRO readouts."""
        line_upper = line.upper().strip()

        # 1. Check for standard GRBL status reporting: MPos:1.00,2.00,3.00,4.00
        grbl_m = re.search(r'MPOS\s*[:\s]*\s*(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:,(-?\d+(?:\.\d+)?))?', line_upper)
        if grbl_m:
            try:
                x = float(grbl_m.group(1))
                y = float(grbl_m.group(2))
                z = float(grbl_m.group(3))
                a = float(grbl_m.group(4))
                force = float(grbl_m.group(5)) if grbl_m.group(5) else None

                # Look for weight separately if present
                w_m = re.search(r'(?:W|KG|FORCE)\s*[:\s]*\s*(-?\d+(?:\.\d+)?)', line_upper)
                if w_m:
                    force = float(w_m.group(1))

                self.update_dro_values(x, y, z, a, force)
                return True
            except ValueError:
                pass

        # 2. Key-Value labels: X:1.0 Y:2.0 Z:3.0 A:4.0 W:5.0
        has_val = False
        x, y, z, a, force = None, None, None, None, None

        x_m = re.search(r'\bX\s*[:\s]*\s*(-?\d+(?:\.\d+)?)', line_upper)
        if x_m:
            x = float(x_m.group(1))
            has_val = True

        y_m = re.search(r'\bY\s*[:\s]*\s*(-?\d+(?:\.\d+)?)', line_upper)
        if y_m:
            y = float(y_m.group(1))
            has_val = True

        z_m = re.search(r'\bZ\s*[:\s]*\s*(-?\d+(?:\.\d+)?)', line_upper)
        if z_m:
            z = float(z_m.group(1))
            has_val = True

        a_m = re.search(r'\bA\s*[:\s]*\s*(-?\d+(?:\.\d+)?)', line_upper)
        if a_m:
            a = float(a_m.group(1))
            has_val = True

        w_m = re.search(r'\b(?:W|KG|FORCE|Z-FORCE)\s*[:\s]*\s*(-?\d+(?:\.\d+)?)', line_upper)
        if w_m:
            force = float(w_m.group(1))
            has_val = True

        if has_val:
            self.update_dro_values(x, y, z, a, force)
            return True

        return False

    def update_dro_values(self, x, y, z, a, force):
        """Updates the numeric displays of the digital readout with scaled unit values."""
        unit = self.main_window.tab_settings.combo_units.currentText() if hasattr(self.main_window, 'tab_settings') else "mm"
        scale = 1.0 / 25.4 if unit == "inch" else 1.0

        if x is not None:
            self.dro_labels["x"][0].setText(f"{x * scale:.2f}")
        if y is not None:
            self.dro_labels["y"][0].setText(f"{y * scale:.2f}")
        if z is not None:
            self.dro_labels["z"][0].setText(f"{z * scale:.2f}")
        if a is not None:
            self.dro_labels["a"][0].setText(f"{a:.1f}")
        if force is not None:
            self.dro_labels["force"][0].setText(f"{force:.2f}")

    def send_gcode(self):
        # Phase 4: Pull live G-code via the controller's sync method
        gcode = self.main_window.controller.get_gcode()
        if not gcode:
            self.terminal.append("Error: No G-code to send")
            return
        
        if "; ERROR: Machine limit reached!" in gcode:
            self.terminal.append("CRITICAL: Cannot send G-code with safety errors!")
            return
            
        self.btn_send.setEnabled(False)
        lines = gcode.split('\n')
        self.terminal.append(f"--- Streaming {len(lines)} lines ---")
        self.worker.start_streaming(lines)

    def open_limits_dialog(self):
        from ui.dialogs import MachineLimitsDialog
        dialog = MachineLimitsDialog(self, self.main_window.controller.machine_limits)
        if dialog.exec():
            new_limits = dialog.get_values()
            self.main_window.controller.machine_limits = new_limits
            self.terminal.append(f"Machine limits updated: Max X = {new_limits['max_x']}mm")

    # 2. VOLLEDIGE RESET VAN DE STATUS & INTERFACE
    def emergency_stop(self):
        self.terminal.append("--- Programma gereset door gebruiker ---")
        
        # Stop de achtergrond worker direct en wis de wachtrij
        self.worker.emergency_stop()
        
        # Reset de interface elementen direct naar de beginstatus
        self.progress_bar.setValue(0)
        
        # Maak de startknop direct weer actief (als de machine verbonden is)
        if self.worker.is_connected():
            self.btn_send.setEnabled(True)

    def retranslate_ui(self, tx):
        self.lbl_title.setText(tx.get("nav_device", "Device"))
        self.btn_refresh.setText(tx.get("btn_refresh", "Refresh Ports"))
        self.lbl_port.setText(tx.get("lbl_port", "Serial Port:"))
        self.btn_connect.setText("Disconnect" if self.worker.is_connected() else "Connect")
        self.btn_send.setText(tx.get("btn_start_winding", "Start Winding"))
        self.btn_emergency.setText(tx.get("btn_reset_program", "🔄 Reset Programma"))

        # Update DRO unit labels dynamically based on settings unit
        unit = self.main_window.tab_settings.combo_units.currentText() if hasattr(self.main_window, 'tab_settings') else "mm"
        pos_unit = "inch" if unit == "inch" else "mm"

        if "x" in self.dro_labels:
            self.dro_labels["x"][1].setText(pos_unit)
        if "y" in self.dro_labels:
            self.dro_labels["y"][1].setText(pos_unit)
        if "z" in self.dro_labels:
            self.dro_labels["z"][1].setText(pos_unit)
