import logging
import trimesh
import numpy as np
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class UVUnwrapper:
    """
    Module 3: UV Parameterization Engine using xatlas
    Unwraps 3D meshes into non-overlapping 2D UV texture charts.
    """

    @staticmethod
    def unwrap(mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        import xatlas

        logger.info(f"Unwrapping mesh with {len(mesh.vertices)} vertices and {len(mesh.faces)} faces...")
        
        # Ensure contiguous float arrays
        vertices = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
        faces = np.ascontiguousarray(mesh.faces, dtype=np.uint32)

        # Compute UV atlas parameterization
        vmapping, indices, uvs = xatlas.parametrize(vertices, faces)

        # Construct new parameterized mesh with updated vertex mapping and UVs
        new_vertices = vertices[vmapping]
        new_faces = indices

        unwrapped_mesh = trimesh.Trimesh(
            vertices=new_vertices,
            faces=new_faces,
            process=False
        )

        # Normalize UV coordinates to [0, 1] range if needed
        uvs = np.clip(uvs, 0.0, 1.0)
        unwrapped_mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)

        stats = {
            "original_vertices": len(vertices),
            "unwrapped_vertices": len(new_vertices),
            "faces": len(new_faces),
            "uv_min": [float(x) for x in np.min(uvs, axis=0)],
            "uv_max": [float(x) for x in np.max(uvs, axis=0)],
            "has_uv": True
        }

        logger.info(f"UV parameterization complete. UV charts mapped onto {len(new_vertices)} vertices.")
        return unwrapped_mesh, stats

uv_unwrapper = UVUnwrapper()

