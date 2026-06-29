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

    def toggle_spool(self):
        self.spool_visible = not self.spool_visible
        self.viewer.set_spool_visibility(self.spool_visible)

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

            # More robust parsing of wire diameter
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
                    verts = np.zeros((len(wire_pts), tube_res, 3), dtype=np.float32)
                    for i in range(len(wire_pts)):
                        for j in range(tube_res):
                            verts[i, j] = wire_pts[i] + ((v['w']/2)*1.002) * (np.cos(ang[j]) * v_side[i] + np.sin(ang[j]) * v_up[i])

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
                self.last_wire_cache = {'key': wire_key, 'length': length_m, 'pts_list': pts_list, 'angles_list': angles_list}

            self.viewer.update_materials(individual_wire_mats, spool_mat)

            if self.last_wire_cache:
                self.gcode_engine.units = self.tab_settings.combo_units.currentText()
                self.gcode_engine.start_gcode = self.tab_settings.txt_start_gcode.toPlainText()
                self.gcode_engine.end_gcode = self.tab_settings.txt_end_gcode.toPlainText()

                gcode = self.gcode_engine.generate(
                    self.last_wire_cache['pts_list'],
                    self.last_wire_cache['angles_list'],
                    units=self.gcode_engine.units
                )
                self.tab_preview.set_gcode(gcode)

        except Exception as e:
            print(f"Update error: {e}")
