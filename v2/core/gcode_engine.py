# core/gcode_engine.py
import math
import numpy as np

class GCodeEngine:
    def __init__(self):
        self.start_gcode = "G28 ; Home all axes"
        self.end_gcode = "M30 ; Program end"
        self.units = "mm" 

    def generate(self, pts_list, angles_list, nozzle_y_offset=0.0, wire_offset=0.0, spool_offset=0.0, z_force=0.5, feedrate=500, units="mm", max_x=200.0,
                 m0_enable=True, compress_gcode=True, smart_reversal=True, reversal_speed_pct=50.0, reversal_y_retract=1.0, reversal_dwell_ms=200.0):
        """Generates G-code based on simulation paths and machine offsets (Phase 3)."""
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

        # Use the first wire's path
        pts = pts_list[0]
        angles = angles_list[0]
        
        # Convert to degrees for machine A-axis (spool rotation)
        a_axis = np.degrees(angles)
        
        # X-axis (traverse) = math_z + spool_offset + wire_offset
        # math_z is the position along the width of the spool from the path calculation.
        x_axis = pts[:, 2] + spool_offset + wire_offset
        
        # Y-axis (nozzle distance) = radial_dist + y_offset
        y_axis = np.sqrt(pts[:, 0]**2 + pts[:, 1]**2) + nozzle_y_offset
        
        scale = 1.0 / 25.4 if units.lower() == "inch" else 1.0

        # Start position limit check
        if x_axis[0] > max_x or x_axis[0] < 0:
            gcode.append(f"; ERROR: Machine limit reached! X ({x_axis[0] * scale:.3f}) exceeds limit (0-{max_x * scale}).")
            return "\n".join(gcode)

        # Go to start position
        gcode.append(f"G0 A{a_axis[0]:.3f} X{x_axis[0] * scale:.3f} Y{y_axis[0] * scale:.3f} Z{z_force:.3f}")
        
        # Wait at start (M0) to secure wire
        if m0_enable:
            gcode.append("M0 ; Wacht op knop - Zet draad vast en druk op start")

        # Detect turn indices (reversal points)
        turn_indices = [0]
        direction = None
        for idx in range(1, len(x_axis)):
            diff = x_axis[idx] - x_axis[idx - 1]
            if abs(diff) > 1e-5:
                curr_dir = 1 if diff > 0 else -1
                if direction is None:
                    direction = curr_dir
                elif curr_dir != direction:
                    turn_indices.append(idx - 1)
                    direction = curr_dir
        turn_indices.append(len(x_axis) - 1)

        # Generate G-code layer by layer with optional smart reversal transitions and compression
        for j in range(len(turn_indices) - 1):
            start_idx = turn_indices[j]
            end_idx = turn_indices[j + 1]

            # Smart transition zone: within 1.5 turns of either layer boundary
            transition_angle = 1.5 * 2.0 * np.pi  # 1.5 turns in radians

            mid_start_idx = start_idx
            mid_end_idx = end_idx

            if smart_reversal:
                # Find the boundary indices for middle zone
                for idx in range(start_idx, end_idx + 1):
                    if abs(angles[idx] - angles[start_idx]) >= transition_angle:
                        mid_start_idx = idx
                        break
                for idx in range(end_idx, start_idx - 1, -1):
                    if abs(angles[end_idx] - angles[idx]) >= transition_angle:
                        mid_end_idx = idx
                        break

            has_mid = smart_reversal and (mid_start_idx < mid_end_idx)

            curr_idx = start_idx
            while curr_idx <= end_idx:
                # Skip the first point since we already moved to it via G0
                if curr_idx == 0:
                    curr_idx += 1
                    continue

                if x_axis[curr_idx] > max_x or x_axis[curr_idx] < 0:
                    gcode.append(f"; ERROR: Machine limit reached! X ({x_axis[curr_idx] * scale:.3f}) exceeds limit (0-{max_x * scale}).")
                    break

                comment = ""
                if has_mid and curr_idx > mid_start_idx and curr_idx < mid_end_idx:
                    if compress_gcode:
                        # Compress the entire middle zone into a single linear step
                        curr_idx = mid_end_idx
                        if x_axis[curr_idx] > max_x or x_axis[curr_idx] < 0:
                            gcode.append(f"; ERROR: Machine limit reached! X ({x_axis[curr_idx] * scale:.3f}) exceeds limit (0-{max_x * scale}).")
                            break
                        gcode.append(f"G1 A{a_axis[curr_idx]:.3f} X{x_axis[curr_idx] * scale:.3f} Y{y_axis[curr_idx] * scale:.3f} Z{z_force:.3f} F{feedrate} ; Compressed Mid-Zone")
                        curr_idx += 1
                        continue
                    else:
                        f_val = feedrate
                        y_val = y_axis[curr_idx]
                elif smart_reversal:
                    if curr_idx <= mid_start_idx:
                        # Entry zone: ramp up speed and return Y to normal
                        t = (transition_angle - abs(angles[curr_idx] - angles[start_idx])) / transition_angle
                        t = max(0.0, min(1.0, t))
                        f_val = feedrate * (1.0 - t * (1.0 - reversal_speed_pct / 100.0))
                        y_val = y_axis[curr_idx] + t * reversal_y_retract
                        if curr_idx == start_idx + 1 or curr_idx == mid_start_idx:
                            comment = " ; Reversal Entry"
                    else:
                        # Exit zone: ramp down speed and retract Y
                        t = (transition_angle - abs(angles[end_idx] - angles[curr_idx])) / transition_angle
                        t = max(0.0, min(1.0, t))
                        f_val = feedrate * (1.0 - t * (1.0 - reversal_speed_pct / 100.0))
                        y_val = y_axis[curr_idx] + t * reversal_y_retract
                        if curr_idx == mid_end_idx + 1 or curr_idx == end_idx:
                            comment = " ; Reversal Exit"
                else:
                    f_val = feedrate
                    y_val = y_axis[curr_idx]

                gcode.append(f"G1 A{a_axis[curr_idx]:.3f} X{x_axis[curr_idx] * scale:.3f} Y{y_val * scale:.3f} Z{z_force:.3f} F{f_val:.1f}{comment}")

                # Perform dwell at the end of the layer sweep
                if smart_reversal and curr_idx == end_idx and j < (len(turn_indices) - 2):
                    gcode.append(f"G4 F{reversal_dwell_ms:.0f} ; Wachttijd omkeer")

                curr_idx += 1
            
        # Force Mode OFF
        gcode.append("M400 ; Force Mode OFF (Z in mm)")

        if self.end_gcode:
            gcode.append(self.end_gcode)
            
        return "\n".join(gcode)
