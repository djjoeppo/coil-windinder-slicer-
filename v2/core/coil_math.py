# core/coil_math.py
import numpy as np

class CoilMathEngine:
    @staticmethod
    def calculate_path(wire_d, layers, inner_d, width, p_res, num_wires=1):
        """Berekent de pure 3D-coördinaten (X, Y, Z) van de draden."""
        wire_d = max(0.05, wire_d)
        res = min(int(p_res), 48)
        layers = max(1, int(layers))
        
        ribbon_width = wire_d * num_wires
        effective_width = width - ribbon_width
        if effective_width <= 0:
            effective_width = max(0.1, width - wire_d)
            
        effective_pitch = wire_d * num_wires
        turns_per_layer = effective_width / effective_pitch
        if turns_per_layer < 0.1: turns_per_layer = 0.1
        
        # Determine an adaptive resolution (points per turn) to balance performance and quality.
        # We want to keep steps_per_layer reasonable (e.g. under 6000), but we MUST have at least 12 points per turn
        # to prevent straight lines cutting through the spool (the "basket/star" glitch).
        adaptive_res = res
        if (turns_per_layer * adaptive_res) > 6000:
            adaptive_res = max(12.0, 6000.0 / turns_per_layer)

        steps_per_layer = int(turns_per_layer * adaptive_res) + 2

        all_pts_list = []
        all_angles_list = [] # ADDED
        total_len_mm = 0
        
        # Performance optimization: if layers is extremely large, warn or cap it for rendering
        if layers > 50:
            layers = 50

        for w_idx in range(num_wires):
            wire_continuous_pts = []
            wire_continuous_angles = [] # ADDED
            current_angle_offset = 0.0
            z_ribbon_offset = w_idx * wire_d
            
            for l in range(layers):
                r = (inner_d / 2) + (l * wire_d * 0.866) + (wire_d / 2)
                
                if w_idx == 0:
                    total_len_mm += (2 * np.pi * r) * turns_per_layer
                
                p = np.linspace(0.0, 1.0, steps_per_layer, dtype=np.float32)
                angles = (p * turns_per_layer * 2 * np.pi) + current_angle_offset
                
                if l % 2 == 0:
                    z = (p * effective_width) + z_ribbon_offset + (wire_d / 2)
                else:
                    z = ((1.0 - p) * effective_width) + z_ribbon_offset + (wire_d / 2)
                
                next_angle_start = angles[-1]
                z = np.clip(z, wire_d / 2, width - (wire_d / 2))
                
                layer_pts = np.zeros((steps_per_layer, 3), dtype=np.float32)
                layer_pts[:, 0] = r * np.cos(angles)
                layer_pts[:, 1] = r * np.sin(angles)
                layer_pts[:, 2] = z
                
                if l > 0 and len(wire_continuous_pts) > 0:
                    wire_continuous_pts.append(layer_pts[1:])
                    wire_continuous_angles.append(angles[1:]) # ADDED
                else:
                    wire_continuous_pts.append(layer_pts)
                    wire_continuous_angles.append(angles) # ADDED
                
                current_angle_offset = next_angle_start
            
            all_pts_list.append(np.vstack(wire_continuous_pts))
            all_angles_list.append(np.concatenate(wire_continuous_angles)) # ADDED
                
        total_length_all_wires_m = (total_len_mm * num_wires) / 1000.0
        return all_pts_list, total_length_all_wires_m, all_angles_list # ADDED

    @staticmethod
    def calculate_mesh_vectors(wire_pts, tube_res, visual_r):
        """Helper om vectoren (tangents, side, up) te berekenen voor 3D mesh."""
        # Vectorized calculation for performance (Bolt optimization)
        n_pts = len(wire_pts)
        tangents = np.zeros_like(wire_pts)
        tangents[1:-1] = wire_pts[2:] - wire_pts[:-2]
        tangents[0] = wire_pts[1] - wire_pts[0]
        tangents[-1] = wire_pts[-1] - wire_pts[-2]
        norms = np.linalg.norm(tangents, axis=1, keepdims=True)
        tangents /= np.where(norms == 0, 1, norms)

        z_axis = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        v_side = np.cross(tangents, z_axis)
        side_norms = np.linalg.norm(v_side, axis=1, keepdims=True)

        # Handle cases where tangents are parallel to Z-axis by using a fallback vector
        mask = (side_norms > 1e-4).ravel()
        v_side_final = np.tile(np.array([1.0, 0.0, 0.0], dtype=np.float32), (n_pts, 1))
        v_side_final[mask] = v_side[mask] / side_norms[mask]
        v_side = v_side_final

        v_up = np.cross(tangents, v_side)
        up_norms = np.linalg.norm(v_up, axis=1, keepdims=True)
        v_up /= np.where(up_norms == 0, 1, up_norms)

        return tangents, v_side, v_up

    @staticmethod
    def calculate_spool_geometry(hole_d, inner_d, flange_l_d, flange_r_d, width, cols=60):
        """Berekent puur de hoekpunten (vertices) en vlakken (faces) van de spoel/hub."""
        r_out = inner_d / 2
        r_in = hole_d / 2
        
        return {
            "r_out": r_out,
            "r_in": r_in,
            "cols": cols,
            "width": width,
            "flange_l_d": flange_l_d,
            "flange_r_d": flange_r_d
        }
