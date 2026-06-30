# ui/components.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.viewer_3d import Coil3DViewer

# This file can now just expose the real viewer or other small components
class Dummy3DViewer(Coil3DViewer):
    def __init__(self, parent=None):
        super().__init__()
        # We don't need a dummy anymore, but keeping the name for compatibility if needed
        # or we just use Coil3DViewer directly.
