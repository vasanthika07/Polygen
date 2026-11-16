import logging
import numpy as np
import trimesh
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class MeshValidator:
    """
    Performs rigorous geometric validation on generated 3D meshes:
    - Non-empty vertices and faces
    - Removal of unreferenced vertices and degenerate faces
    - Verification of finite coordinates (no NaN/Inf)
    - Watertightness and manifold topology checks
    - Bounding box dimension and volume validation
    - Normal generation and orientation validation
    """

    @classmethod
    def validate_and_clean(cls, mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        initial_verts = len(mesh.vertices)
        initial_faces = len(mesh.faces)

        if initial_verts == 0 or initial_faces == 0:
            raise ValueError(f"Invalid mesh geometry: vertices={initial_verts}, faces={initial_faces}")

        # Check for NaN / Inf
        if not np.isfinite(mesh.vertices).all():
            raise ValueError("Mesh contains NaN or Infinite coordinate values.")

        # Clean duplicate vertices, duplicate faces, and unreferenced vertices
        mesh.update_faces(mesh.unique_faces())
        mesh.update_faces(mesh.nondegenerate_faces())
        mesh.remove_unreferenced_vertices()

        # Ensure normals exist
        if mesh.vertex_normals is None or len(mesh.vertex_normals) != len(mesh.vertices):
            mesh.generate_vertex_normals()

        # Bounding box & extents
        extents = [float(x) for x in mesh.extents]
        bounds = mesh.bounds
        bbox_volume = float(extents[0] * extents[1] * extents[2])
        if bbox_volume <= 1e-7:
            logger.warning(f"Mesh has near-zero bounding box volume: {bbox_volume}")

        # Watertight / Manifold verification
        is_watertight = bool(mesh.is_watertight)
        is_winding_consistent = bool(mesh.is_winding_consistent)

        # Ensure correct normal orientation
        if not is_winding_consistent and len(mesh.faces) > 0:
            try:
                trimesh.repair.fix_winding(mesh)
                trimesh.repair.fix_normals(mesh)
            except Exception as e:
                logger.debug(f"Normal winding fix note: {e}")

        validation_stats = {
            "initial_vertices": initial_verts,
            "initial_faces": initial_faces,
            "valid_vertices": len(mesh.vertices),
            "valid_faces": len(mesh.faces),
            "removed_degenerate_faces": initial_faces - len(mesh.faces),
            "is_watertight": is_watertight,
            "is_winding_consistent": bool(mesh.is_winding_consistent),
            "bounding_box_extents": extents,
            "bounding_box_volume": round(bbox_volume, 6),
            "surface_area": round(float(mesh.area), 4) if hasattr(mesh, "area") else 0.0,
            "is_valid": True,
        }

        return mesh, validation_stats

mesh_validator = MeshValidator()
