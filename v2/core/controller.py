# core/controller.py
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QApplication, QProgressDialog, QMessageBox
from PySide6.QtCore import Qt
from core.coil_math import CoilMathEngine
from core.gcode_engine import GCodeEngine
from core.calc_worker import CalculationWorker
from ui.dialogs import MachineLimitsDialog

class CoilController:
    def __init__(self, ui_layout):
        self.ui = ui_layout
        self.tab_prepare = ui_layout.tab_prepare
        self.tab_preview = ui_layout.tab_preview
        self.tab_settings = ui_layout.tab_settings
        self.viewer = self.tab_prepare.viewer
        self.preview_viewer = self.tab_preview.viewer

        # Ensure nozzle tracker is only visible in the Preview tab
        self.viewer.set_machine_visibility(False)
        self.preview_viewer.set_machine_visibility(True)

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
        self.tab_preview.btn_update_gcode.clicked.connect(self.process_gcode_generation)
        self.tab_preview.btn_machine_limits.clicked.connect(self.open_machine_limits)

        self.machine_limits = {
            "max_x": 200.0,
            "max_y": 100.0,
            "max_z": 15.0,
            "max_z_force": 10.0
        }

        self.calc_worker = None
        self.progress_dialog = None

    def toggle_spool(self):
        self.spool_visible = not self.spool_visible
        self.update_spool_visibility()

    def update_spool_visibility(self):
        chk_l = self.tab_prepare.chk_flange_l.isChecked()
        chk_r = self.tab_prepare.chk_flange_r.isChecked()

        self.viewer.hub.setVisible(self.spool_visible)
        self.viewer.flange_l.setVisible(self.spool_visible and chk_l)
        self.viewer.flange_r.setVisible(self.spool_visible and chk_r)

        self.preview_viewer.hub.setVisible(self.spool_visible)
        self.preview_viewer.flange_l.setVisible(self.spool_visible and chk_l)
        self.preview_viewer.flange_r.setVisible(self.spool_visible and chk_r)

    def update_simulation(self, slider_value):
        """Update the 3D viewer in the Preview tab based on simulation progress (Bolt optimized)."""
        if self.last_wire_cache is None or 'full_meshes' not in self.last_wire_cache: return

        progress = slider_value / 1000.0
        full_meshes = self.last_wire_cache['full_meshes']
        pts_list = self.last_wire_cache['pts_list']
        angles_list = self.last_wire_cache['angles_list']
        num_wires = len(pts_list)

        partial_meshes = []

        # Get offsets for nozzle visualization (Phase 2)
        try:
            wire_offset = float(self.tab_preview.input_wire_offset.text())
            spool_offset = float(self.tab_preview.input_spool_offset.text())
            y_offset = float(self.tab_preview.input_y_offset.text())
        except ValueError:
            wire_offset, spool_offset, y_offset = 0.0, 0.0, 0.0

        for w_idx in range(num_wires):
            full_mesh_data = full_meshes[w_idx]
            n_pts = len(pts_list[w_idx])
            current_n = max(2, int(n_pts * progress))

            # Bolt optimization: reuse existing MeshData's vertexes and slice faces
            # instead of creating completely new MeshData objects with vertex copies.
            tube_res = int(self.last_wire_cache['params']['t_res'])
            tube_res = min(tube_res, 32)
            n_seg = current_n - 1
            num_faces = n_seg * tube_res * 2

            # Use raw faces from the full mesh for zero-copy slicing performance
            sliced_faces = full_mesh_data.faces()[:num_faces]
            partial_meshes.append(gl.MeshData(vertexes=full_mesh_data.vertexes(), faces=sliced_faces))

            # Update nozzle position based on the last point of the first wire
            if w_idx == 0:
                idx = current_n - 1
                last_pt = pts_list[w_idx][idx]
                last_angle = np.degrees(angles_list[w_idx][idx])
                
                # Radial distance calculation
                r = np.sqrt(last_pt[0]**2 + last_pt[1]**2) + y_offset
                angle_rad = angles_list[w_idx][idx]
                nozzle_x = r * np.cos(angle_rad)
                nozzle_y = r * np.sin(angle_rad)
                nozzle_z = last_pt[2] + wire_offset + spool_offset

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

            from core.config import parse_fraction_or_float, inch_to_mm

            unit = self.tab_settings.combo_units.currentText()
            scale_to_mm = 25.4 if unit == "inch" else 1.0

            # Parse inputs (supporting fractions and mixed fractions)
            chk_l = self.tab_prepare.chk_flange_l.isChecked()
            chk_r = self.tab_prepare.chk_flange_r.isChecked()

            i_val = parse_fraction_or_float(self.tab_prepare.inputs['i'].text()) * scale_to_mm
            hole_val = parse_fraction_or_float(self.tab_prepare.inputs['hole'].text()) * scale_to_mm

            f_l_val = parse_fraction_or_float(self.tab_prepare.inputs['f_l'].text()) * scale_to_mm if chk_l else i_val
            f_r_val = parse_fraction_or_float(self.tab_prepare.inputs['f_r'].text()) * scale_to_mm if chk_r else i_val

            b_val = parse_fraction_or_float(self.tab_prepare.inputs['b'].text()) * scale_to_mm

            try:
                l_val = int(self.tab_prepare.inputs['l'].text())
            except ValueError:
                l_val = 1

            try:
                t_res_val = float(self.tab_settings.inputs['t_res'].text())
            except ValueError:
                t_res_val = 16.0

            try:
                p_res_val = float(self.tab_settings.inputs['p_res'].text())
            except ValueError:
                p_res_val = 32.0

            v = {
                'i': i_val,
                'hole': hole_val,
                'f_l': f_l_val,
                'f_r': f_r_val,
                'b': b_val,
                'l': l_val,
                't_res': t_res_val,
                'p_res': p_res_val,
                'is_multi': is_multi,
                'num_wires': num_wires
            }

            # Retrieve wire diameter: if we are in inch mode, extract the fraction or decimals inside parentheses or AWG lookup
            wire_d_text = self.tab_prepare.input_wire_d_display.text()
            if "AWG" in wire_d_text:
                # We can extract the millimeter or inch value. e.g. "24 AWG (0.0201")"
                # Let's extract the value inside parenthesises: e.g. 0.0201
                import re
                match = re.search(r'\(([^)]+)\)', wire_d_text)
                if match:
                    val_str = match.group(1).replace('"', '').strip()
                    v['w'] = float(val_str) * 25.4 # convert inch back to mm internally
                else:
                    v['w'] = 0.5 # fallback
            else:
                v['w'] = float(wire_d_text.split(' ')[0]) # millimeter value

            if v['hole'] >= v['i']:
                v['hole'] = v['i'] - 1.0
                self.tab_prepare.inputs['hole'].setText(str(v['hole']))

            wire_key = (v['w'], v['l'], v['i'], v['b'], v['t_res'], v['p_res'], num_wires)
            spool_key = (v['hole'], v['i'], f_l_val, f_r_val, v['b'])

            if self.last_spool_cache is None or self.last_spool_cache != spool_key:
                spool_data = CoilMathEngine.calculate_spool_geometry(v['hole'], v['i'], f_l_val, f_r_val, v['b'])
                self.viewer.build_spool_meshes(spool_data)
                self.preview_viewer.build_spool_meshes(spool_data)
                self.last_spool_cache = spool_key
                self.update_spool_visibility()

            if self.last_wire_cache is None or self.last_wire_cache['key'] != wire_key:
                self.start_calculation(v, wire_key)
            else:
                self.apply_visuals()

        except Exception as e:
            print(f"Update error: {e}")
            import traceback
            traceback.print_exc()

    def start_calculation(self, v, wire_key):
        if self.calc_worker and self.calc_worker.isRunning():
            return

        self.progress_dialog = QProgressDialog("Berekenen van wikkeling...", "Annuleren", 0, 100, self.ui)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)

        self.calc_worker = CalculationWorker(v)
        self.calc_worker.progress.connect(self.progress_dialog.setValue)
        self.calc_worker.finished.connect(lambda res: self.on_calc_finished(res, wire_key))
        self.calc_worker.error.connect(self.on_calc_error)
        self.calc_worker.start()

    def on_calc_finished(self, result, wire_key):
        self.progress_dialog.close()
        self.last_wire_cache = result
        self.last_wire_cache['key'] = wire_key

        self.viewer.render_wire_meshes(result['full_meshes'])
        self.apply_visuals()

        # Reset simulation on new calculation
        self.tab_preview.slider.setValue(1000)
        self.update_simulation(1000)

    def on_calc_error(self, err_msg):
        self.progress_dialog.close()
        QMessageBox.critical(self.ui, "Fout", f"Berekeningsfout: {err_msg}")

    def open_machine_limits(self):
        from ui.dialogs import MachineLimitsDialog
        dialog = MachineLimitsDialog(self.ui, self.machine_limits)
        if dialog.exec():
            self.machine_limits = dialog.get_values()
            print(f"Machine limits updated: {self.machine_limits}")

    def apply_visuals(self):
        spool_mat = self.materials_db.get(self.tab_prepare.combo_spool_color.currentText(), self.materials_db["Standaard (Donker)"])
        is_multi = (self.tab_prepare.combo_wire_type.currentIndex() == 1)
        individual_wire_mats = []
        if is_multi:
            for combo in self.tab_prepare.wire_color_combos:
                individual_wire_mats.append(self.materials_db.get(combo.currentText(), self.materials_db["Koper"]))
        else:
            individual_wire_mats.append(self.materials_db.get(self.tab_prepare.combo_wire_color.currentText(), self.materials_db["Koper"]))

        self.viewer.update_materials(individual_wire_mats, spool_mat)
        self.preview_viewer.update_materials(individual_wire_mats, spool_mat)

    def process_gcode_generation(self):
        if not self.last_wire_cache:
            QMessageBox.warning(self.ui, "Waarschuwing", "Geen wikkeling data beschikbaar. Klik eerst op berekenen.")
            return

        try:
            z_force = float(self.tab_preview.input_z_force.text())
            wire_offset = float(self.tab_preview.input_wire_offset.text())
            spool_offset = float(self.tab_preview.input_spool_offset.text())
            y_offset = float(self.tab_preview.input_y_offset.text())
            feedrate = float(self.tab_preview.input_feedrate.text())

            # Validation
            pts = self.last_wire_cache['pts_list'][0]
            max_x_calc = np.max(np.abs(pts[:, 2] + wire_offset + spool_offset))
            max_y_calc = np.max(np.sqrt(pts[:, 0]**2 + pts[:, 1]**2) + y_offset)

            # Let's handle scale based on units selected in Settings Tab
            unit = self.tab_settings.combo_units.currentText()
            scale = 1.0 / 25.4 if unit == "inch" else 1.0
            unit_suffix = "inch" if unit == "inch" else "mm"

            error_msgs = []
            if max_x_calc > self.machine_limits["max_x"]:
                error_msgs.append(f"X-as limiet overschreden: {max_x_calc * scale:.2f} {unit_suffix} > {self.machine_limits['max_x'] * scale:.2f} {unit_suffix}")
            if max_y_calc > self.machine_limits["max_y"]:
                error_msgs.append(f"Y-as limiet overschreden: {max_y_calc * scale:.2f} {unit_suffix} > {self.machine_limits['max_y'] * scale:.2f} {unit_suffix}")
            if z_force > self.machine_limits["max_z_force"]:
                error_msgs.append(f"Z-kracht limiet overschreden: {z_force:.2f} > {self.machine_limits['max_z_force']}")

            if error_msgs:
                QMessageBox.critical(self.ui, "Limiet Overschreden", "\n".join(error_msgs))
                return

            self.gcode_engine.units = self.tab_settings.combo_units.currentText()
            self.gcode_engine.start_gcode = self.tab_preview.txt_start_gcode.toPlainText()
            self.gcode_engine.end_gcode = self.tab_preview.txt_end_gcode.toPlainText()

            gcode = self.gcode_engine.generate(
                self.last_wire_cache['pts_list'],
                self.last_wire_cache['angles_list'],
                nozzle_y_offset=y_offset,
                wire_offset=wire_offset,
                spool_offset=spool_offset,
                z_force=z_force,
                feedrate=feedrate,
                units=self.gcode_engine.units,
                max_x=self.machine_limits["max_x"]
            )
            self.tab_preview.set_gcode(gcode)
            QMessageBox.information(self.ui, "Succes", "G-code succesvol gegenereerd.")
        except Exception as e:
            print(f"G-code generation error: {e}")
            import traceback
            traceback.print_exc()

    def get_gcode(self):
        """Phase 4: Safely retrieve the live G-code from the UI (Live Sync)."""
        return self.tab_preview.gcode_display.toPlainText()
