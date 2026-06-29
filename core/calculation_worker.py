# core/calculation_worker.py
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import QObject, Signal, Slot, QThread
from core.coil_math import CoilMathEngine

class CalculationWorker(QObject):
    """Handles heavy coil math and mesh generation in a separate thread."""
    finished = Signal(dict)
    progress = Signal(int)
    error = Signal(str)

    @Slot(dict)
    def run_calculation(self, params):
        try:
            # params contains: w, l, i, b, t_res, p_res, num_wires
            w = params['w']
            l = params['l']
            i_kern = params['i']
            b = params['b']
            t_res = int(params['t_res'])
            p_res = int(params['p_res'])
            num_wires = params['num_wires']

            self.progress.emit(10)
            pts_list, length_m, angles_list = CoilMathEngine.calculate_path(w, l, i_kern, b, p_res, num_wires)
            self.progress.emit(40)

            # Pre-generate meshes for all wires
            meshes_data = []
            tube_res = min(t_res, 32)
            ang = np.linspace(0, 2*np.pi, tube_res, endpoint=False, dtype=np.float32)
            radius = (w/2)*1.002
            cos_ang = np.cos(ang).reshape(1, tube_res, 1)
            sin_ang = np.sin(ang).reshape(1, tube_res, 1)

            total_wires = len(pts_list)
            for idx, wire_pts in enumerate(pts_list):
                if len(wire_pts) < 2:
                    meshes_data.append(None)
                    continue

                _, v_side, v_up = CoilMathEngine.calculate_mesh_vectors(wire_pts, t_res, radius)

                v_side_exp = v_side.reshape(-1, 1, 3)
                v_up_exp = v_up.reshape(-1, 1, 3)

                # Vectorized vertex calculation
                verts = wire_pts.reshape(-1, 1, 3) + radius * (cos_ang * v_side_exp + sin_ang * v_up_exp)
                verts = verts.reshape(-1, 3)

                n_seg = len(wire_pts) - 1
                idx1 = np.arange(n_seg * tube_res, dtype=np.uint32).reshape(n_seg, tube_res)
                idx2 = idx1 + tube_res
                r1_n, r2_n = np.roll(idx1, -1, axis=1), np.roll(idx2, -1, axis=1)
                f1 = np.column_stack([idx1.ravel(), r1_n.ravel(), idx2.ravel()])
                f2 = np.column_stack([r1_n.ravel(), r2_n.ravel(), idx2.ravel()])
                wire_faces = np.vstack([f1, f2])

                meshes_data.append({
                    'verts': verts,
                    'faces': wire_faces,
                    'pts_count': len(wire_pts)
                })

                # Emit progress based on wires processed
                prog = 40 + int((idx + 1) / total_wires * 50)
                self.progress.emit(prog)

            result = {
                'pts_list': pts_list,
                'angles_list': angles_list,
                'length_m': length_m,
                'meshes_data': meshes_data,
                'params': params
            }
            self.progress.emit(100)
            self.finished.emit(result)

        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")
