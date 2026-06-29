# ui/tabs/device_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QProgressBar
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

        # Execution controls
        self.btn_send = QPushButton("Start Winding")
        self.btn_send.setEnabled(False)
        self.btn_send.clicked.connect(self.send_gcode)
        sidebar_layout.addWidget(self.btn_send)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        sidebar_layout.addWidget(self.progress_bar)

        sidebar_layout.addStretch()

        # Main area for terminal
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #000; color: #0f0; font-family: monospace;")

        layout.addWidget(sidebar)
        layout.addWidget(self.terminal)

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
        if not line.startswith(">>"): # Avoid double echo in terminal
             self.terminal.append(f"<< {line}")
        else:
             self.terminal.append(line)

        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())

    def on_send_complete(self):
        self.terminal.append("--- Streaming Complete ---")
        self.btn_send.setEnabled(True)

    def send_gcode(self):
        gcode = self.main_window.tab_preview.gcode_display.toPlainText()
        if not gcode:
            self.terminal.append("Error: No G-code to send")
            return

        self.btn_send.setEnabled(False)
        lines = gcode.split('\n')
        self.terminal.append(f"--- Streaming {len(lines)} lines ---")
        self.worker.start_streaming(lines)

    def retranslate_ui(self, tx):
        self.lbl_title.setText(tx.get("nav_device", "Device"))
        self.btn_refresh.setText(tx.get("btn_refresh", "Refresh Ports"))
        self.lbl_port.setText(tx.get("lbl_port", "Serial Port:"))
        self.btn_connect.setText("Disconnect" if self.worker.is_connected() else "Connect")
        self.btn_send.setText(tx.get("btn_start_winding", "Start Winding"))
