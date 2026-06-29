from __future__ import annotations

import serial
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class ArduinoWorker(QObject):
    """Arduino serial worker that runs in a QThread.

    - Connect waits for READY once.
    - Then a QTimer polls the serial buffer and emits every line via line_received.
    - UI sends commands via send_line() without blocking.
    """

    connected = Signal(str)
    disconnected = Signal()
    connection_error = Signal(str)

    line_received = Signal(str)

    def __init__(self):
        super().__init__()
        self._ser: serial.Serial | None = None

        self._timer = QTimer()
        self._timer.setInterval(10)
        self._timer.timeout.connect(self._poll_serial)

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
                if line == "READY":
                    ready = True
                    break

            if not ready:
                raise TimeoutError("Did not receive READY from Arduino")

            self._timer.start()
            self.connected.emit(f"connected ({port})")

        except Exception as e:
            self.connection_error.emit(str(e))
            self._safe_close()

    @Slot()
    def disconnect_port(self):
        self._safe_close()
        self.disconnected.emit()

    @Slot(str)
    def send_line(self, line: str):
        if not self.is_connected():
            self.line_received.emit("ERR,NOT_CONNECTED")
            return
        try:
            if not line.endswith("\n"):
                line += "\n"
            self._ser.write(line.encode("utf-8"))
        except Exception as e:
            self.line_received.emit(f"ERR,WRITE,{e!s}")

    def _poll_serial(self):
        if not self.is_connected():
            return
        try:
            while self._ser.in_waiting > 0:
                line = self._readline()
                if line:
                    self.line_received.emit(line)
        except Exception as e:
            self.line_received.emit(f"ERR,READ,{e!s}")

    def _readline(self) -> str:
        assert self._ser is not None
        raw = self._ser.readline()
        if not raw:
            return ""
        return raw.decode("utf-8", errors="replace").strip()

    def _safe_close(self):
        try:
            self._timer.stop()
        except Exception:
            pass
        try:
            if self._ser:
                self._ser.close()
        finally:
            self._ser = None
