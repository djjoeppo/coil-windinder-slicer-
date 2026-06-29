# coil_math.py
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
        
        steps_per_layer = int(turns_per_layer * res) + 2
        all_pts_list = []
        total_len_mm = 0
        
        for w_idx in range(num_wires):
            wire_continuous_pts = []
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
                else:
                    wire_continuous_pts.append(layer_pts)
                
                current_angle_offset = next_angle_start
            
            all_pts_list.append(np.vstack(wire_continuous_pts))
                
        total_length_all_wires_m = (total_len_mm * num_wires) / 1000.0
        return all_pts_list, total_length_all_wires_m

    @staticmethod
    def calculate_mesh_vectors(wire_pts, tube_res, visual_r):
        """Helper om vectoren (tangents, side, up) te berekenen voor 3D mesh."""
        n_pts = len(wire_pts)
        tangents = np.zeros_like(wire_pts)
        tangents[1:-1] = wire_pts[2:] - wire_pts[:-2]
        tangents[0] = wire_pts[1] - wire_pts[0]
        tangents[-1] = wire_pts[-1] - wire_pts[-2]
        norms = np.linalg.norm(tangents, axis=1, keepdims=True)
        tangents /= np.where(norms == 0, 1, norms)
        
        v_side = np.zeros_like(wire_pts)
        z_axis = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        for i in range(n_pts):
            side = np.cross(tangents[i], z_axis)
            side_len = np.linalg.norm(side)
            v_side[i] = side / side_len if side_len > 1e-4 else np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        v_up = np.cross(tangents, v_side)
        up_norms = np.linalg.norm(v_up, axis=1, keepdims=True)
        v_up /= np.where(up_norms == 0, 1, up_norms)
        
        return tangents, v_side, v_up

    @staticmethod
    def calculate_spool_geometry(hole_d, inner_d, flange_d, width, cols=60):
        """Berekent puur de hoekpunten (vertices) en vlakken (faces) van de spoel/hub."""
        r_out = inner_d / 2
        r_in = hole_d / 2
        
        # Geeft dictionary terug met ruwe geometriedata
        return {
            "r_out": r_out,
            "r_in": r_in,
            "cols": cols,
            "width": width,
            "flange_d": flange_d
        }