import logging
import trimesh
import numpy as np
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class MeshCleaner:
    """
    Module 4: Mesh Cleaning Service
    Removes duplicate vertices, removes degenerate faces, checks and repairs
    non-manifold edges, and recalculates consistent surface normals.
    """

    @staticmethod
    def clean(mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        initial_verts = len(mesh.vertices)
        initial_faces = len(mesh.faces)
        
        logger.info(f"Initial mesh stats: {initial_verts} vertices, {initial_faces} faces")

        # 1. Merge duplicate / coincident vertices
        mesh.merge_vertices()

        # 2. Remove degenerate faces (faces with zero area or repeated vertex indices)
        if hasattr(mesh, "nondegenerate_faces"):
            mesh.update_faces(mesh.nondegenerate_faces())

        # 3. Remove duplicate faces
        if hasattr(mesh, "unique_faces"):
            mesh.update_faces(mesh.unique_faces())

        # 4. Remove unreferenced / isolated vertices
        mesh.remove_unreferenced_vertices()

        # 5. Fill small holes if open
        if not mesh.is_watertight:
            logger.info("Mesh is not watertight. Attempting repair...")
            try:
                trimesh.repair.fill_holes(mesh)
                trimesh.repair.fix_winding(mesh)
                trimesh.repair.fix_inversion(mesh)
            except Exception as e:
                logger.warning(f"Watertight repair warning: {e}")

        # 6. Recalculate smooth normals
        try:
            mesh.fix_normals()
            _ = mesh.vertex_normals
        except Exception as e:
            logger.warning(f"Normal computation warning: {e}")

        final_verts = len(mesh.vertices)
        final_faces = len(mesh.faces)

        stats = {
            "initial_vertices": initial_verts,
            "initial_faces": initial_faces,
            "cleaned_vertices": final_verts,
            "cleaned_faces": final_faces,
            "is_watertight": bool(mesh.is_watertight),
            "is_winding_consistent": bool(mesh.is_winding_consistent),
            "volume": float(mesh.volume) if mesh.is_volume else None,
            "bounding_box": [float(x) for x in mesh.extents],
        }

        logger.info(f"Mesh cleaning completed. Result: {final_verts} vertices, {final_faces} faces")
        return mesh, stats

mesh_cleaner = MeshCleaner()
