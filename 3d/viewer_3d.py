# viewer_3d.py
import numpy as np
import pyqtgraph.opengl as gl
from OpenGL import GL  # Importeer ruwe OpenGL functies voor de glans

class CustomGLMeshItem(gl.GLMeshItem):
    """Een geavanceerde mesh die echte OpenGL glans (specular) ondersteunt 
       en compatibel is met Python 3.13 / PySide6."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.material_params = None

    def paint(self):
        # --- VOORKOM 6 ARGUMENTS CRASH ---
        # Haal de kleur op uit de pyqtgraph opties
        c = self.opts.get('color', (1, 1, 1, 1))
        
        # Als de kleur genest is (zoals een tuple in een lijst), breek hem open
        if isinstance(c, (list, tuple)) and len(c) == 1 and isinstance(c[0], (list, tuple, np.ndarray)):
            c = c[0]
            
        # Zorg dat de kleur ALTIJD exact een platte tuple van 4 getallen is (RGBA)
        c_flat = list(c)
        if len(c_flat) == 3:
            c_flat.append(1.0)
        elif len(c_flat) > 4:
            c_flat = c_flat[:4]
        self.opts['color'] = tuple(c_flat)
        # ---------------------------------

        # Als het materiaal glanzend metaal is, zetten we de spiegeling aan
        if self.material_params and self.material_params.get("is_metallic"):
            GL.glEnable(GL.GL_LIGHTING)
            GL.glEnable(GL.GL_LIGHT0)
            
            diffuse = self.material_params["diffuse"]
            # Zorg dat diffuse ook exact 4 elementen heeft voor OpenGL
            if len(diffuse) == 3: diffuse = (*diffuse, 1.0)
            
            specular = (1.0, 0.95, 0.9, 1.0) # De glanzende lichtvlek (hotspot)
            shininess = 110.0                # Hoe scherp de lak reflecteert
            
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, diffuse)
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, specular)
            GL.glMaterialf(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, shininess)
        else:
            # Voor matte kleuren/plastics zetten we de glansvlek uit
            GL.glDisable(GL.GL_LIGHT0)
            if self.material_params:
                diffuse = self.material_params["diffuse"]
                if len(diffuse) == 3: diffuse = (*diffuse, 1.0)
                GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, diffuse)
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
            GL.glMaterialf(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, 0.0)

        try:
            super().paint()
        except Exception:
            # Ultiem vangnet: Als pyqtgraph intern alsnog struikelt over vertex attributen,
            # dwingen we OpenGL hier handmatig naar de juiste kleurmodus.
            GL.glColor4f(*c_flat)
            super().paint()


class Coil3DViewer(gl.GLViewWidget):
    def __init__(self):
        super().__init__()
        self.setBackgroundColor("#111111")
        self.opts.update({"distance": 250, "elevation": 30, "azimuth": 150})
        
        start_verts = np.array([[0,0,0], [1,0,0], [0,1,0]], dtype=np.float32)
        start_faces = np.array([[0,1,2]], dtype=np.uint32)
        light_mesh = gl.MeshData(vertexes=start_verts, faces=start_faces)
        
        self.hub = CustomGLMeshItem(meshdata=light_mesh, smooth=True, shader="shaded")
        self.flange_l = CustomGLMeshItem(meshdata=light_mesh, smooth=True, shader="shaded")
        self.flange_r = CustomGLMeshItem(meshdata=light_mesh, smooth=True, shader="shaded")
        self.addItem(self.hub)
        self.addItem(self.flange_l)
        self.addItem(self.flange_r)
        
        self.wire_items = []

    def build_spool_meshes(self, spool_data):
        r_out = spool_data["r_out"]
        r_in = spool_data["r_in"]
        cols = spool_data["cols"]
        width = spool_data["width"]
        flange_d = spool_data["flange_d"]
        
        if r_in > 0:
            ang = np.linspace(0, 2*np.pi, cols, endpoint=False)
            cos_a, sin_a = np.cos(ang), np.sin(ang)
            v_out_b = np.column_stack([r_out * cos_a, r_out * sin_a, np.zeros(cols)])
            v_out_t = np.column_stack([r_out * cos_a, r_out * sin_a, np.full(cols, width)])
            v_in_b = np.column_stack([r_in * cos_a, r_in * sin_a, np.zeros(cols)])
            v_in_t = np.column_stack([r_in * cos_a, r_in * sin_a, np.full(cols, width)])
            v_hub = np.vstack([v_out_b, v_out_t, v_in_b, v_in_t])
            f_hub = []
            for i in range(cols):
                n = (i + 1) % cols
                f_hub.append([i, n, i + cols]); f_hub.append([n, n + cols, i + cols])
                f_hub.append([i + 2*cols, i + 3*cols, n + 2*cols]); f_hub.append([n + 2*cols, i + 3*cols, n + 3*cols])
                f_hub.append([i, i + 2*cols, n]); f_hub.append([n, i + 2*cols, n + 2*cols])
                f_hub.append([i + cols, n + cols, i + 3*cols]); f_hub.append([n + cols, n + 3*cols, i + 3*cols])
            hub_mesh = gl.MeshData(vertexes=v_hub.astype(np.float32), faces=np.array(f_hub, dtype=np.uint32))
        else:
            md = gl.MeshData.cylinder(rows=1, cols=cols, radius=[r_out, r_out], length=width)
            v = md.vertexes(); f = list(md.faces())
            b, t = len(v), len(v)+1
            v = np.vstack([v, [0,0,0], [0,0,width]])
            for i in range(cols):
                n = (i+1)%cols
                f.append([b, i, n]); f.append([t, i+cols, n+cols])
            hub_mesh = gl.MeshData(vertexes=v.astype(np.float32), faces=np.array(f, dtype=np.uint32))
            
        def _make_flange(z_offset, thickness):
            rf_out = flange_d / 2
            rf_in = r_in 
            ang = np.linspace(0, 2*np.pi, cols, endpoint=False)
            cos_a, sin_a = np.cos(ang), np.sin(ang)
            v_o_b = np.column_stack([rf_out * cos_a, rf_out * sin_a, np.full(cols, z_offset)])
            v_o_t = np.column_stack([rf_out * cos_a, rf_out * sin_a, np.full(cols, z_offset + thickness)])
            v_i_b = np.column_stack([rf_in * cos_a, rf_in * sin_a, np.full(cols, z_offset)])
            v_i_t = np.column_stack([rf_in * cos_a, rf_in * sin_a, np.full(cols, z_offset + thickness)])
            v_fl = np.vstack([v_o_b, v_o_t, v_i_b, v_i_t])
            f_fl = []
            for i in range(cols):
                n = (i + 1) % cols
                f_fl.append([i, n, i + cols]); f_fl.append([n, n + cols, i + cols])
                f_fl.append([i + 2*cols, i + 3*cols, n + 2*cols]); f_fl.append([n + 2*cols, i + 3*cols, n + 3*cols])
                f_fl.append([i, i + 2*cols, n]); f_fl.append([n, i + 2*cols, n + 2*cols])
                f_fl.append([i + cols, n + cols, i + 3*cols]); f_fl.append([n + cols, n + 3*cols, i + 3*cols])
            return gl.MeshData(vertexes=v_fl.astype(np.float32), faces=np.array(f_fl, dtype=np.uint32))

        self.hub.setMeshData(meshdata=hub_mesh)
        self.flange_l.setMeshData(meshdata=_make_flange(-3, 3))
        self.flange_r.setMeshData(meshdata=_make_flange(width, 3))

    def render_wire_meshes(self, meshes_data):
        for item in self.wire_items:
            self.removeItem(item)
        self.wire_items.clear()
        
        for mesh_data in meshes_data:
            item = CustomGLMeshItem(meshdata=mesh_data, smooth=True, shader='shaded')
            item.setGLOptions('opaque')
            self.addItem(item)
            self.wire_items.append(item)

    def update_materials(self, wire_materials, spool_material):
        for part in [self.hub, self.flange_l, self.flange_r]:
            part.material_params = spool_material
            part.setColor((*spool_material["diffuse"], 1.0))
            part.update()
            
        for idx, item in enumerate(self.wire_items):
            if idx < len(wire_materials):
                mat = wire_materials[idx]
                item.material_params = mat
                item.setColor((*mat["diffuse"], 1.0))
                item.update()

    def set_spool_visibility(self, visible: bool):
        self.hub.setVisible(visible)
        self.flange_l.setVisible(visible)
        self.flange_r.setVisible(visible)