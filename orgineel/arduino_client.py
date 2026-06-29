import time
import serial

class ArduinoClient:
    """Simple synchronous helper. Not used directly by the UI worker in this project."""

    def __init__(self):
        self.ser: serial.Serial | None = None

    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def connect(self, port: str, baud: int = 115200, timeout: float = 2.0):
        self.ser = serial.Serial(port=port, baudrate=baud, timeout=timeout, write_timeout=timeout)
        self.ser.reset_input_buffer()
        start = time.time()
        while time.time() - start < 5.0:
            line = self.readline()
            if line == "READY":
                return
        raise TimeoutError("Did not receive READY from Arduino")

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            finally:
                self.ser = None

    def write_line(self, s: str):
        if not self.is_connected():
            raise RuntimeError("Not connected")
        if not s.endswith("\n"):
            s += "\n"
        self.ser.write(s.encode("utf-8"))

    def readline(self) -> str:
        if not self.is_connected():
            return ""
        raw = self.ser.readline()
        if not raw:
            return ""
        return raw.decode("utf-8", errors="replace").strip()
