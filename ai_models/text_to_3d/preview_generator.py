import os
import logging
import numpy as np
import trimesh
from typing import Optional

logger = logging.getLogger(__name__)

class PreviewGenerator:
    """
    Renders offscreen isometric preview images from 3D meshes for instant visual inspection.
    Saves PNG thumbnails with professional dark-studio lighting.
    """

    @classmethod
    def generate_preview(
        cls,
        mesh: trimesh.Trimesh,
        output_image_path: str,
        image_size: tuple = (512, 512),
        elevation: float = 25.0,
        azimuth: float = 45.0,
    ) -> Optional[str]:
        """
        Renders the given trimesh into a clean PNG preview using matplotlib's Agg backend.
        """
        abs_path = os.path.abspath(output_image_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection

            # Normalize mesh centered at origin and scaled to unit box for consistent framing
            v = mesh.vertices.copy()
            centroid = mesh.centroid
            v = v - centroid
            max_extent = np.max(mesh.extents)
            if max_extent > 0:
                scale = 1.6 / max_extent
                v = v * scale

            faces = mesh.faces

            # Subsample faces if mesh is very dense for fast preview rendering
            if len(faces) > 2500:
                step = max(1, len(faces) // 2500)
                faces_to_render = faces[::step]
            else:
                faces_to_render = faces

            triangles = v[faces_to_render]

            fig = plt.figure(figsize=(image_size[0] / 100, image_size[1] / 100), dpi=100)
            fig.patch.set_facecolor('#0d0e12')  # PolyGen dark theme
            ax = fig.add_subplot(111, projection='3d')
            ax.set_facecolor('#0d0e12')

            # Render 3D polygons with directional shading
            # Calculate simple normal-based lighting
            face_normals = mesh.face_normals[:len(faces_to_render)] if len(mesh.face_normals) >= len(faces_to_render) else None
            face_colors = []
            light_dir = np.array([0.5, 0.5, 1.0])
            light_dir = light_dir / np.linalg.norm(light_dir)

            base_color = np.array([0.45, 0.65, 0.90]) # Cyan-blue tinted studio render

            for i, tri in enumerate(triangles):
                if face_normals is not None and i < len(face_normals):
                    norm = face_normals[i]
                else:
                    u = tri[1] - tri[0]
                    w = tri[2] - tri[0]
                    norm = np.cross(u, w)
                    n_len = np.linalg.norm(norm)
                    norm = norm / (n_len + 1e-8)

                diffuse = max(0.2, float(np.dot(norm, light_dir)))
                c = np.clip(base_color * diffuse + 0.15, 0.0, 1.0)
                face_colors.append((c[0], c[1], c[2], 0.95))

            poly_collection = Poly3DCollection(
                triangles,
                facecolors=face_colors,
                edgecolors=(0.2, 0.3, 0.45, 0.2),
                linewidths=0.3,
            )
            ax.add_collection3d(poly_collection)

            # Frame bounds
            ax.set_xlim([-1.0, 1.0])
            ax.set_ylim([-1.0, 1.0])
            ax.set_zlim([-1.0, 1.0])

            # View angle
            ax.view_init(elev=elevation, azim=azimuth)
            ax.set_axis_off()

            plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
            plt.savefig(abs_path, facecolor='#0d0e12', edgecolor='none', bbox_inches='tight', pad_inches=0)
            plt.close(fig)

            logger.info(f"Offscreen preview successfully saved to {abs_path}")
            return abs_path

        except Exception as e:
            logger.warning(f"Offscreen preview generation encountered error: {e}")
            return None

preview_generator = PreviewGenerator()
