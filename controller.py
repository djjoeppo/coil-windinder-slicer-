# Verander dit bovenin controller.py:
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QApplication
from model.coil_math import CoilMathEngine  # <-- Aangepast met 'model.'

class CoilController:
    def __init__(self, ui_layout):
        self.ui = ui_layout
        self.last_wire_cache = None
        self.last_spool_cache = None
        self.spool_visible = True
        
        # Geoptimaliseerde materiaaldatabase voor glans vs mat
        self.materials_db = {
            # Glanzende realistische metalen (is_metallic: True activeert de glanslaag)
            "Koper": {"diffuse": (0.85, 0.38, 0.15, 1.0), "is_metallic": True},
            "Goud": {"diffuse": (0.88, 0.68, 0.12, 1.0), "is_metallic": True},
            "Zilver": {"diffuse": (0.75, 0.77, 0.80, 1.0), "is_metallic": True},
            "Aluminium": {"diffuse": (0.68, 0.70, 0.72, 1.0), "is_metallic": True},
            "Messing": {"diffuse": (0.72, 0.62, 0.18, 1.0), "is_metallic": True},
            
            # Volledig matte kleuren (Geen glans/hotspots)
            "Rood": {"diffuse": (0.80, 0.12, 0.12, 1.0), "is_metallic": False},
            "Blauw": {"diffuse": (0.12, 0.40, 0.70, 1.0), "is_metallic": False},
            "Groen": {"diffuse": (0.12, 0.60, 0.28, 1.0), "is_metallic": False},
            "Paars": {"diffuse": (0.50, 0.12, 0.55, 1.0), "is_metallic": False},
            "Zwart": {"diffuse": (0.15, 0.15, 0.15, 1.0), "is_metallic": False},
            "Wit": {"diffuse": (0.88, 0.88, 0.88, 1.0), "is_metallic": False},
            
            # Spoel materialen (Mat)
            "Standaard (Donker)": {"diffuse": (0.22, 0.22, 0.22, 1.0), "is_metallic": False},
            "Plastic Zwart": {"diffuse": (0.10, 0.10, 0.11, 1.0), "is_metallic": False},
            "Plastic Wit": {"diffuse": (0.92, 0.92, 0.92, 1.0), "is_metallic": False}
        }
        
        self.ui.btn_update.clicked.connect(self.process_update)
        self.ui.btn_toggle_spool.clicked.connect(self.toggle_spool)
        self.ui.combo_wire_type.currentIndexChanged.connect(self.ui.toggle_multi_wire_fields)
        self.ui.inputs["num_wires"].textChanged.connect(self.ui.generate_dynamic_wire_color_menus)
        self.ui.combo_theme.currentTextChanged.connect(self.ui.apply_theme)

    def toggle_spool(self):
        self.spool_visible = not self.spool_visible
        self.ui.viewer.set_spool_visibility(self.spool_visible)
        status_tekst = "Zichtbaar" if self.spool_visible else "Onzichtbaar"
        self.ui.lbl_info.setText(f"Status: Spoel is nu {status_tekst}")

    def process_update(self):
        try:
            is_multi = (self.ui.combo_wire_type.currentIndex() == 1)
            num_wires = int(float(self.ui.inputs["num_wires"].text())) if is_multi else 1
            num_wires = max(1, num_wires)

            v = {k: float(val.text()) for k, val in self.ui.inputs.items() if k != "num_wires"}
            
            if v['hole'] >= v['i']:
                v['hole'] = v['i'] - 1.0
                self.ui.inputs['hole'].setText(str(v['hole']))
                self.ui.lbl_info.setText("Waarschuwing: Gat Ø aangepast tot onder Kern Ø!")
                QApplication.processEvents()
            
            wire_key = (v['w'], v['l'], v['i'], v['b'], v['t_res'], v['p_res'], num_wires)
            spool_key = (v['hole'], v['i'], v['f'], v['b'])
            
            spool_mat = self.materials_db.get(self.ui.combo_spool_color.currentText(), self.materials_db["Standaard (Donker)"])
            
            individual_wire_mats = []
            if is_multi:
                for combo in self.ui.wire_color_combos:
                    individual_wire_mats.append(self.materials_db.get(combo.currentText(), self.materials_db["Koper"]))
            else:
                individual_wire_mats.append(self.materials_db.get(self.ui.combo_wire_color.currentText(), self.materials_db["Koper"]))
            
            if self.last_spool_cache is None or self.last_spool_cache != spool_key:
                spool_data = CoilMathEngine.calculate_spool_geometry(v['hole'], v['i'], v['f'], v['b'])
                self.ui.viewer.build_spool_meshes(spool_data)
                self.last_spool_cache = spool_key

            if self.last_wire_cache is None or self.last_wire_cache['key'] != wire_key:
                self.ui.lbl_info.setText("Status: Ononderbroken spoel berekenen...")
                QApplication.processEvents()
                
                pts_list, length_m = CoilMathEngine.calculate_path(v['w'], int(v['l']), v['i'], v['b'], v['p_res'], num_wires)
                
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
                
                self.ui.viewer.render_wire_meshes(meshes)
                self.last_wire_cache = {'key': wire_key, 'length': length_m}
            else:
                length_m = self.last_wire_cache['length']
            
            self.ui.viewer.update_materials(individual_wire_mats, spool_mat)
            
            vol_per_wire = (np.pi * ((v['w']/20)**2)) * (length_m * 100)
            total_weight = vol_per_wire * v['dens']
            prefix = f"Multi ({num_wires}x)" if is_multi else "Single"
            self.ui.lbl_info.setText(f"{prefix} | L per draad: {length_m:.2f} m | Tot. Gew: {total_weight:.1f} g")
            
        except ValueError:
            self.ui.lbl_info.setText("Fout: Controleer of alle invoervelden cijfers bevatten!")
        except Exception as e:
            self.ui.lbl_info.setText(f"Fout tijdens berekening: {str(e)}")