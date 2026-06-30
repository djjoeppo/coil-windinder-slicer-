# core/gcode_engine.py
import math
import numpy as np

class GCodeEngine:
    def __init__(self):
        self.start_gcode = "G28 ; Home all axes"
        self.end_gcode = "M30 ; Program end"
        self.units = "mm" 

    def generate(self, pts_list, angles_list, nozzle_y_offset=0.0, x_nozzle_offset=0.0, x_spool_offset=0.0, z_force=0.5, feedrate=500, units="mm"):
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

        # Force Mode ON for winding
        gcode.append("M401 ; Force Mode ON (Z in kg)")

        # For simplicity, we use the first wire's path
        pts = pts_list[0]
        angles = angles_list[0]
        
        # Convert to degrees
        a_axis = np.degrees(angles)
        # X in machine = math_z + x_nozzle_offset + x_spool_offset
        x_axis = pts[:, 2] + x_nozzle_offset + x_spool_offset
        # Y in machine = radial_dist + y_offset
        y_axis = np.sqrt(pts[:, 0]**2 + pts[:, 1]**2) + nozzle_y_offset
        
        # Start position
        gcode.append(f"G0 A{a_axis[0]:.3f} X{x_axis[0]:.3f} Y{y_axis[0]:.3f} Z{z_force:.3f}")
        
        for i in range(1, len(pts)):
            gcode.append(f"G1 A{a_axis[i]:.3f} X{x_axis[i]:.3f} Y{y_axis[i]:.3f} Z{z_force:.3f} F{feedrate}")
            
        # Force Mode OFF
        gcode.append("M400 ; Force Mode OFF (Z in mm)")

        if self.end_gcode:
            gcode.append(self.end_gcode)
            
        return "\n".join(gcode)
