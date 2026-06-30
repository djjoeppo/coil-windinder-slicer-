# core/controller.py
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QApplication
from core.coil_math import CoilMathEngine
from core.gcode_engine import GCodeEngine

class CoilController:
    def __init__(self, ui_layout):
        self.ui = ui_layout
        self.tab_prepare = ui_layout.tab_prepare
        self.tab_preview = ui_layout.tab_preview
        self.tab_settings = ui_layout.tab_settings
        self.viewer = self.tab_prepare.viewer
        self.preview_viewer = self.tab_preview.viewer
        
        self.gcode_engine = GCodeEngine()
        
        self.last_wire_cache = None
        self.last_spool_cache = None
        self.spool_visible = True
        
        # Optimized material database
        self.materials_db = {
            "Koper": {"diffuse": (0.85, 0.38, 0.15, 1.0), "is_metallic": True},
            "Goud": {"diffuse": (0.95, 0.75, 0.1, 1.0), "is_metallic": True},
            "Zilver": {"diffuse": (0.75, 0.75, 0.75, 1.0), "is_metallic": True},
            "Aluminium": {"diffuse": (0.68, 0.70, 0.72, 1.0), "is_metallic": True},
            "Messing": {"diffuse": (0.72, 0.62, 0.18, 1.0), "is_metallic": True},
            "Rood": {"diffuse": (0.80, 0.12, 0.12, 1.0), "is_metallic": False},
            "Blauw": {"diffuse": (0.12, 0.40, 0.70, 1.0), "is_metallic": False},
            "Groen": {"diffuse": (0.12, 0.60, 0.28, 1.0), "is_metallic": False},
            "Paars": {"diffuse": (0.50, 0.12, 0.55, 1.0), "is_metallic": False},
            "Zwart": {"diffuse": (0.15, 0.15, 0.15, 1.0), "is_metallic": False},
            "Wit": {"diffuse": (0.88, 0.88, 0.88, 1.0), "is_metallic": False},
            "Standaard (Donker)": {"diffuse": (0.22, 0.22, 0.22, 1.0), "is_metallic": False},
            "Plastic Zwart": {"diffuse": (0.10, 0.10, 0.11, 1.0), "is_metallic": False},
            "Plastic Wit": {"diffuse": (0.92, 0.92, 0.92, 1.0), "is_metallic": False}
        }
        
        self.tab_prepare.btn_update.clicked.connect(self.process_update)
        self.tab_prepare.btn_toggle_spool.clicked.connect(self.toggle_spool)
        self.tab_preview.timeline_changed.connect(self.update_simulation)
        self.tab_preview.btn_generate_gcode.clicked.connect(self.process_gcode_generation)

    def toggle_spool(self):
        self.spool_visible = not self.spool_visible
        self.viewer.set_spool_visibility(self.spool_visible)
        self.preview_viewer.set_spool_visibility(self.spool_visible)

    def update_simulation(self, slider_value):
        """Update the 3D viewer in the Preview tab based on simulation progress."""
        if self.last_wire_cache is None or 'full_meshes' not in self.last_wire_cache: return
        
        progress = slider_value / 1000.0
        full_meshes = self.last_wire_cache['full_meshes']
        pts_list = self.last_wire_cache['pts_list']
        angles_list = self.last_wire_cache['angles_list']
        num_wires = len(pts_list)
        
        partial_meshes = []

        # Get offsets for nozzle visualization
        try:
            x_nozzle_offset = float(self.tab_preview.input_x_nozzle_offset.text())
            x_spool_offset = float(self.tab_preview.input_x_spool_offset.text())
            y_offset = float(self.tab_preview.input_y_offset.text())
        except ValueError:
            x_nozzle_offset, x_spool_offset, y_offset = 0.0, 0.0, 0.0

        for w_idx in range(num_wires):
            full_mesh_data = full_meshes[w_idx]
            n_pts = len(pts_list[w_idx])
            current_n = max(2, int(n_pts * progress))
            
            if current_n < 2:
                partial_meshes.append(gl.MeshData(vertexes=np.zeros((3, 3), dtype=np.float32), faces=np.zeros((1, 3), dtype=np.uint32)))
                continue

            # Pre-calculated verts are already there, we just need to slice faces
            tube_res = int(self.last_wire_cache['params']['t_res'])
            tube_res = min(tube_res, 32)
            n_seg = current_n - 1
            num_faces = n_seg * tube_res * 2
            
            sliced_faces = full_mesh_data.faces()[:num_faces]
            partial_meshes.append(gl.MeshData(vertexes=full_mesh_data.vertexes(), faces=sliced_faces))
            
            # Update nozzle position based on the last point of the first wire
            if w_idx == 0:
                last_pt = pts_list[w_idx][current_n-1]
                last_angle = np.degrees(angles_list[w_idx][current_n-1])
                # In 3D: Z is spool axis (width), X/Y is radial
                # math pts are [x, y, z] where x,y is radial and z is width.
                # So nozzle 3D position is [last_pt[0], last_pt[1], last_pt[2]]?
                # Actually, nozzle distance should include y_offset.
                # Radial distance:
                r = np.sqrt(last_pt[0]**2 + last_pt[1]**2) + y_offset
                angle_rad = angles_list[w_idx][current_n-1]
                nozzle_x = r * np.cos(angle_rad)
                nozzle_y = r * np.sin(angle_rad)
                nozzle_z = last_pt[2] + x_nozzle_offset + x_spool_offset

                self.preview_viewer.update_machine_elements(last_angle, nozzle_x, nozzle_y, nozzle_z)

        self.preview_viewer.render_wire_meshes(partial_meshes)
        
        # Color wires according to settings
        spool_mat = self.materials_db.get(self.tab_prepare.combo_spool_color.currentText(), self.materials_db["Standaard (Donker)"])
        is_multi = (self.tab_prepare.combo_wire_type.currentIndex() == 1)
        individual_wire_mats = []
        if is_multi:
            for combo in self.tab_prepare.wire_color_combos:
                individual_wire_mats.append(self.materials_db.get(combo.currentText(), self.materials_db["Koper"]))
        else:
            individual_wire_mats.append(self.materials_db.get(self.tab_prepare.combo_wire_color.currentText(), self.materials_db["Koper"]))
        self.preview_viewer.update_materials(individual_wire_mats, spool_mat)

    def process_update(self):
        try:
            is_multi = (self.tab_prepare.combo_wire_type.currentIndex() == 1)
            num_wires = int(float(self.tab_prepare.inputs["num_wires"].text())) if is_multi else 1
            num_wires = max(1, num_wires)

            v = {
                'i': float(self.tab_prepare.inputs['i'].text()),
                'hole': float(self.tab_prepare.inputs['hole'].text()),
                'f': float(self.tab_prepare.inputs['f'].text()),
                'b': float(self.tab_prepare.inputs['b'].text()),
                'l': int(self.tab_prepare.inputs['l'].text()),
            }
            
            wire_d_text = self.tab_prepare.input_wire_d_display.text().split(' ')[0]
            v['w'] = float(wire_d_text)
            
            v['t_res'] = float(self.tab_settings.inputs['t_res'].text())
            v['p_res'] = float(self.tab_settings.inputs['p_res'].text())
            
            if v['hole'] >= v['i']:
                v['hole'] = v['i'] - 1.0
                self.tab_prepare.inputs['hole'].setText(str(v['hole']))
            
            wire_key = (v['w'], v['l'], v['i'], v['b'], v['t_res'], v['p_res'], num_wires)
            spool_key = (v['hole'], v['i'], v['f'], v['b'])
            
            spool_mat = self.materials_db.get(self.tab_prepare.combo_spool_color.currentText(), self.materials_db["Standaard (Donker)"])
            
            individual_wire_mats = []
            if is_multi:
                for combo in self.tab_prepare.wire_color_combos:
                    individual_wire_mats.append(self.materials_db.get(combo.currentText(), self.materials_db["Koper"]))
            else:
                individual_wire_mats.append(self.materials_db.get(self.tab_prepare.combo_wire_color.currentText(), self.materials_db["Koper"]))
            
            if self.last_spool_cache is None or self.last_spool_cache != spool_key:
                spool_data = CoilMathEngine.calculate_spool_geometry(v['hole'], v['i'], v['f'], v['b'])
                self.viewer.build_spool_meshes(spool_data)
                self.preview_viewer.build_spool_meshes(spool_data)
                self.last_spool_cache = spool_key

            if self.last_wire_cache is None or self.last_wire_cache['key'] != wire_key:
                pts_list, length_m, angles_list = CoilMathEngine.calculate_path(v['w'], int(v['l']), v['i'], v['b'], v['p_res'], num_wires)
                
                meshes = []
                for w_idx in range(num_wires):
                    wire_pts = pts_list[w_idx]
                    if len(wire_pts) < 2:
                        meshes.append(gl.MeshData(vertexes=np.zeros((3, 3), dtype=np.float32), faces=np.zeros((1, 3), dtype=np.uint32)))
                        continue
                    
                    _, v_side, v_up = CoilMathEngine.calculate_mesh_vectors(wire_pts, v['t_res'], (v['w']/2)*1.002)
                    tube_res = min(int(v['t_res']), 32)
                    ang = np.linspace(0, 2*np.pi, tube_res, endpoint=False, dtype=np.float32)
                    radius = (v['w']/2)*1.002
                    cos_ang = np.cos(ang).reshape(1, tube_res, 1)
                    sin_ang = np.sin(ang).reshape(1, tube_res, 1)
                    v_side_exp = v_side.reshape(-1, 1, 3)
                    v_up_exp = v_up.reshape(-1, 1, 3)
                    
                    verts = wire_pts.reshape(-1, 1, 3) + radius * (cos_ang * v_side_exp + sin_ang * v_up_exp)
                    verts = verts.reshape(-1, 3)
                    n_seg = len(wire_pts) - 1
                    idx1 = np.arange(n_seg * tube_res, dtype=np.uint32).reshape(n_seg, tube_res)
                    idx2 = idx1 + tube_res
                    r1_n, r2_n = np.roll(idx1, -1, axis=1), np.roll(idx2, -1, axis=1)
                    f1 = np.column_stack([idx1.ravel(), r1_n.ravel(), idx2.ravel()])
                    f2 = np.column_stack([r1_n.ravel(), r2_n.ravel(), idx2.ravel()])
                    wire_faces = np.vstack([f1, f2])
                    meshes.append(gl.MeshData(vertexes=verts, faces=wire_faces))
                
                self.viewer.render_wire_meshes(meshes)
                self.last_wire_cache = {
                    'key': wire_key,
                    'length': length_m,
                    'pts_list': pts_list,
                    'angles_list': angles_list,
                    'params': v,
                    'full_meshes': meshes
                }
                
                # Reset simulation on new calculation
                self.tab_preview.slider.setValue(1000)
                self.update_simulation(1000)
            
            self.viewer.update_materials(individual_wire_mats, spool_mat)
            self.preview_viewer.update_materials(individual_wire_mats, spool_mat)
            
        except Exception as e:
            print(f"Update error: {e}")
            import traceback
            traceback.print_exc()

    def process_gcode_generation(self):
        if not self.last_wire_cache:
            print("No wire cache available. Please click calculate first.")
            return

        try:
            self.gcode_engine.units = self.tab_settings.combo_units.currentText()
            self.gcode_engine.start_gcode = self.tab_preview.txt_start_gcode.toPlainText()
            self.gcode_engine.end_gcode = self.tab_preview.txt_end_gcode.toPlainText()

            z_force = float(self.tab_preview.input_z_force.text())
            x_nozzle_offset = float(self.tab_preview.input_x_nozzle_offset.text())
            x_spool_offset = float(self.tab_preview.input_x_spool_offset.text())
            y_offset = float(self.tab_preview.input_y_offset.text())

            gcode = self.gcode_engine.generate(
                self.last_wire_cache['pts_list'],
                self.last_wire_cache['angles_list'],
                nozzle_y_offset=y_offset,
                x_nozzle_offset=x_nozzle_offset,
                x_spool_offset=x_spool_offset,
                z_force=z_force,
                units=self.gcode_engine.units
            )
            self.tab_preview.set_gcode(gcode)
            print("G-code generated successfully.")
        except Exception as e:
            print(f"G-code generation error: {e}")
            import traceback
            traceback.print_exc()
