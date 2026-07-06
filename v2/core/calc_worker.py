import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import QThread, Signal
from core.coil_math import CoilMathEngine

class CalculationWorker(QThread):
    """Asynchronous worker for coil path and mesh calculations (Bolt Optimization)."""
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, params):
        super().__init__()
        self.v = params

    def run(self):
        try:
            self.progress.emit(10)
            is_multi = self.v.get('is_multi', False)
            num_wires = self.v.get('num_wires', 1)

            # 1. Path Calculation
            pts_list, length_m, angles_list = CoilMathEngine.calculate_path(
                self.v['w'], self.v['l'], self.v['i'], self.v['b'], self.v['p_res'], num_wires
            )
            self.progress.emit(40)

            # 2. Mesh Generation
            meshes = []
            tube_res = min(int(self.v['t_res']), 32)
            radius = (self.v['w'] / 2) * 1.002

            for w_idx in range(num_wires):
                wire_pts = pts_list[w_idx]
                if len(wire_pts) < 2:
                    meshes.append(gl.MeshData(vertexes=np.zeros((3, 3), dtype=np.float32), faces=np.zeros((1, 3), dtype=np.uint32)))
                    continue

                # Heavy calculation (Vectorized in CoilMathEngine)
                _, v_side, v_up = CoilMathEngine.calculate_mesh_vectors(wire_pts, self.v['t_res'], radius)

                ang = np.linspace(0, 2 * np.pi, tube_res, endpoint=False, dtype=np.float32)
                cos_ang = np.cos(ang).reshape(1, tube_res, 1)
                sin_ang = np.sin(ang).reshape(1, tube_res, 1)
                v_side_exp = v_side.reshape(-1, 1, 3)
                v_up_exp = v_up.reshape(-1, 1, 3)

                # Mesh offsets
                offsets = cos_ang * v_side_exp + sin_ang * v_up_exp
                verts = wire_pts.reshape(-1, 1, 3) + radius * offsets
                verts = verts.reshape(-1, 3)

                # Bolt Optimization: Pre-calculate normals to prevent UI freeze during MeshData initialization
                # In a tube mesh, normals are simply the unit vectors of the offsets
                normals = offsets.reshape(-1, 3)

                n_seg = len(wire_pts) - 1
                idx1 = np.arange(n_seg * tube_res, dtype=np.uint32).reshape(n_seg, tube_res)
                idx2 = idx1 + tube_res
                r1_n, r2_n = np.roll(idx1, -1, axis=1), np.roll(idx2, -1, axis=1)
                f1 = np.column_stack([idx1.ravel(), r1_n.ravel(), idx2.ravel()])
                f2 = np.column_stack([r1_n.ravel(), r2_n.ravel(), idx2.ravel()])
                wire_faces = np.vstack([f1, f2])

                meshes.append(gl.MeshData(vertexes=verts, faces=wire_faces, vertexNormals=normals))

                prog_val = 40 + int((w_idx + 1) / num_wires * 50)
                self.progress.emit(prog_val)

            result = {
                'length': length_m,
                'pts_list': pts_list,
                'angles_list': angles_list,
                'full_meshes': meshes,
                'params': self.v
            }
            self.progress.emit(100)
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))
