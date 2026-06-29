# core/controller.py
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Qt, QMetaObject, Q_ARG
from core.coil_math import CoilMathEngine
from core.gcode_engine import GCodeEngine
from core.calculation_worker import CalculationWorker

class CoilController:
    def __init__(self, ui_layout):
        self.ui = ui_layout
        self.tab_prepare = ui_layout.tab_prepare
        self.tab_preview = ui_layout.tab_preview
        self.tab_settings = ui_layout.tab_settings
        self.viewer = self.tab_prepare.viewer
        self.preview_viewer = self.tab_preview.viewer

        self.gcode_engine = GCodeEngine()

        # Background Calculation Setup
        self.calc_thread = QThread()
        self.calc_worker = CalculationWorker()
        self.calc_worker.moveToThread(self.calc_thread)
        self.calc_thread.start()

        self.calc_worker.finished.connect(self.on_calculation_finished)
        self.calc_worker.progress.connect(self.tab_prepare.progress_bar.setValue)
        self.calc_worker.error.connect(self.on_calculation_error)

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

    def toggle_spool(self):
        self.spool_visible = not self.spool_visible
        self.viewer.set_spool_visibility(self.spool_visible)
        self.preview_viewer.set_spool_visibility(self.spool_visible)

    def update_simulation(self, slider_value):
        if self.last_wire_cache is None: return

        progress = slider_value / 1000.0
        meshes_data = self.last_wire_cache['meshes_data']
        num_wires = len(meshes_data)

        meshes = []
        for w_idx in range(num_wires):
            m_data = meshes_data[w_idx]
            if m_data is None: continue

            n_pts = m_data['pts_count']
            tube_res = 32
            current_n_pts = max(2, int(n_pts * progress))
            current_n_seg = current_n_pts - 1

            total_seg = n_pts - 1
            f1 = m_data['faces'][:total_seg * tube_res]
            f2 = m_data['faces'][total_seg * tube_res:]

            sliced_faces = np.vstack([
                f1[:current_n_seg * tube_res],
                f2[:current_n_seg * tube_res]
            ])

            meshes.append(gl.MeshData(vertexes=m_data['verts'], faces=sliced_faces))

        self.preview_viewer.render_wire_meshes(meshes)
        self.apply_wire_materials(self.preview_viewer)

    def apply_wire_materials(self, viewer):
        spool_mat = self.materials_db.get(self.tab_prepare.combo_spool_color.currentText(), self.materials_db["Standaard (Donker)"])
        is_multi = (self.tab_prepare.combo_wire_type.currentIndex() == 1)
        individual_wire_mats = []
        if is_multi:
            for combo in self.tab_prepare.wire_color_combos:
                individual_wire_mats.append(self.materials_db.get(combo.currentText(), self.materials_db["Koper"]))
        else:
            individual_wire_mats.append(self.materials_db.get(self.tab_prepare.combo_wire_color.currentText(), self.materials_db["Koper"]))
        viewer.update_materials(individual_wire_mats, spool_mat)

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
            v['num_wires'] = num_wires

            if v['hole'] >= v['i']:
                v['hole'] = v['i'] - 1.0
                self.tab_prepare.inputs['hole'].setText(str(v['hole']))

            spool_key = (v['hole'], v['i'], v['f'], v['b'])
            if self.last_spool_cache is None or self.last_spool_cache != spool_key:
                spool_data = CoilMathEngine.calculate_spool_geometry(v['hole'], v['i'], v['f'], v['b'])
                self.viewer.build_spool_meshes(spool_data)
                self.preview_viewer.build_spool_meshes(spool_data)
                self.last_spool_cache = spool_key

            # Start background calculation
            self.tab_prepare.set_calculating(True)
            QMetaObject.invokeMethod(self.calc_worker, "run_calculation",
                                     Qt.QueuedConnection,
                                     Q_ARG(dict, v))

        except Exception as e:
            print(f"Update start error: {e}")

    def on_calculation_finished(self, result):
        self.tab_prepare.set_calculating(False)
        self.last_wire_cache = result

        meshes = []
        for m_data in result['meshes_data']:
            if m_data:
                meshes.append(gl.MeshData(vertexes=m_data['verts'], faces=m_data['faces']))
        self.viewer.render_wire_meshes(meshes)
        self.apply_wire_materials(self.viewer)

        self.tab_preview.slider.setValue(1000)
        self.update_simulation(1000)

        self.gcode_engine.units = self.tab_settings.combo_units.currentText()
        self.gcode_engine.start_gcode = self.tab_settings.txt_start_gcode.toPlainText()
        self.gcode_engine.end_gcode = self.tab_settings.txt_end_gcode.toPlainText()

        gcode = self.gcode_engine.generate(
            result['pts_list'],
            result['angles_list'],
            units=self.gcode_engine.units
        )
        self.tab_preview.set_gcode(gcode)

    def on_calculation_error(self, err_msg):
        self.tab_prepare.set_calculating(False)
        print(f"Calculation Error: {err_msg}")
