# core/machine_worker.py
from __future__ import annotations
import serial
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread

class MachineWorker(QObject):
    """Machine serial worker that runs in a QThread.
    - Connect waits for READY once.
    - Handles line-by-line sending with flow control (waiting for 'ok').
    """

    connected = Signal(str)
    disconnected = Signal()
    connection_error = Signal(str)
    line_received = Signal(str)
    progress_updated = Signal(int) # Percentage
    send_complete = Signal()

    def __init__(self):
        super().__init__()
        self._ser: serial.Serial | None = None
        self._send_queue = []
        self._is_sending = False
        self._total_lines = 0
        self._sent_lines = 0

        self._poll_timer = QTimer()
        self._poll_timer.setInterval(10)
        self._poll_timer.timeout.connect(self._poll_serial)

    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    @Slot(str, int, float)
    def connect_port(self, port: str, baud: int = 115200, timeout: float = 2.0):
        try:
            self._ser = serial.Serial(port=port, baudrate=baud, timeout=timeout, write_timeout=timeout)
            self._ser.reset_input_buffer()

            ready = False
            for _ in range(250):
                line = self._readline()
                if line:
                    self.line_received.emit(line)
                if "READY" in line.upper():
                    ready = True
                    break

            if not ready:
                # Some ESP32 might not send READY, but we can try to continue
                pass

            self._poll_timer.start()
            self.connected.emit(f"connected ({port})")

        except Exception as e:
            self.connection_error.emit(str(e))
            self._safe_close()

    @Slot()
    def disconnect_port(self):
        self._safe_close()
        self.disconnected.emit()

    @Slot(list)
    def start_streaming(self, lines: list[str]):
        if not self.is_connected():
            return
        self._send_queue = [l.strip() for l in lines if l.strip()]
        self._total_lines = len(self._send_queue)
        self._sent_lines = 0
        self._is_sending = True
        self._send_next_line()

    def _send_next_line(self):
        if not self._send_queue:
            self._is_sending = False
            self.send_complete.emit()
            return
            
        line = self._send_queue.pop(0)
        try:
            full_line = line + "\n"
            self._ser.write(full_line.encode("utf-8"))
            self._sent_lines += 1
            progress = int((self._sent_lines / self._total_lines) * 100)
            self.progress_updated.emit(progress)
            self.line_received.emit(f">> {line}")
        except Exception as e:
            self.line_received.emit(f"ERR,WRITE,{e!s}")
            self._is_sending = False

    @Slot(str)
    def send_single_line(self, line: str):
        if not self.is_connected(): return
        try:
            if not line.endswith("\n"): line += "\n"
            self._ser.write(line.encode("utf-8"))
        except Exception as e:
            self.line_received.emit(f"ERR,WRITE,{e!s}")

    def _poll_serial(self):
        if not self.is_connected(): return
        try:
            while self._ser.in_waiting > 0:
                line = self._readline()
                if line:
                    self.line_received.emit(line)
                    # Simple flow control: if we receive 'ok' and we are sending, send next
                    if self._is_sending and "OK" in line.upper():
                        self._send_next_line()
        except Exception as e:
            self.line_received.emit(f"ERR,READ,{e!s}")

    def _readline(self) -> str:
        assert self._ser is not None
        raw = self._ser.readline()
        if not raw: return ""
        return raw.decode("utf-8", errors="replace").strip()

    def _safe_close(self):
        self._poll_timer.stop()
        self._is_sending = False
        if self._ser:
            try: self._ser.close()
            except: pass
        self._ser = None
