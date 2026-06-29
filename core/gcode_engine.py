# core/gcode_engine.py
import math
import numpy as np

class GCodeEngine:
    def __init__(self):
        self.start_gcode = "G28 ; Home all axes"
        self.end_gcode = "M30 ; Program end"
        self.units = "mm"

    def generate(self, pts_list, angles_list, nozzle_y=10.0, z_pressure=0.5, feedrate=500, units="mm"):
        if not pts_list or not angles_list:
            return ""

        gcode = []

        # Units
        if units.lower() == "inch":
            gcode.append("G20 ; Inches")
        else:
            gcode.append("G21 ; Millimeters")

        gcode.append("G90 ; Absolute positioning")

        if self.start_gcode:
            gcode.append(self.start_gcode)

        # For simplicity, we use the first wire's path
        pts = pts_list[0]
        angles = angles_list[0]

        # Convert to degrees
        a_axis = np.degrees(angles)
        x_axis = pts[:, 2] # Width (Z in math is X in machine)

        # Start position
        gcode.append(f"G0 A{a_axis[0]:.3f} X{x_axis[0]:.3f} Y{nozzle_y:.3f} Z{z_pressure:.3f}")

        for i in range(1, len(pts)):
            gcode.append(f"G1 A{a_axis[i]:.3f} X{x_axis[i]:.3f} Y{nozzle_y:.3f} Z{z_pressure:.3f} F{feedrate}")

        if self.end_gcode:
            gcode.append(self.end_gcode)

        return "\n".join(gcode)
