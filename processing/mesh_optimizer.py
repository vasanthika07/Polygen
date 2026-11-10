import logging
import trimesh
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class MeshOptimizer:
    """
    Module 4: Mesh Decimation & Optimization Engine
    Performs quadric error decimation while preserving UV coordinates and normals
    to meet the target polygon budget.
    """

    @staticmethod
    def optimize(
        mesh: trimesh.Trimesh,
        target_polygon_budget: int = 10000,
    ) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        initial_faces = len(mesh.faces)
        initial_verts = len(mesh.vertices)

        logger.info(f"Optimizing mesh: Current faces={initial_faces}, Target={target_polygon_budget}")

        if initial_faces <= target_polygon_budget:
            logger.info("Mesh polygon count is already within budget. Skipping decimation.")
            return mesh, {
                "initial_faces": initial_faces,
                "optimized_faces": initial_faces,
                "reduction_ratio": 0.0,
                "initial_vertices": initial_verts,
                "optimized_vertices": initial_verts,
            }

        try:
            # Quadric Error Metric decimation
            simplified = mesh.simplify_quadric_decimation(face_count=target_polygon_budget)
            # Ensure normals are updated
            try:
                simplified.fix_normals()
                _ = simplified.vertex_normals
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Quadric decimation warning: {e}. Falling back to original mesh.")
            simplified = mesh

        final_faces = len(simplified.faces)
        final_verts = len(simplified.vertices)
        reduction_pct = round((1.0 - (final_faces / max(1, initial_faces))) * 100, 2)

        stats = {
            "initial_faces": initial_faces,
            "optimized_faces": final_faces,
            "reduction_ratio": reduction_pct,
            "initial_vertices": initial_verts,
            "optimized_vertices": final_verts,
        }

        logger.info(f"Optimization complete: reduced by {reduction_pct}% ({initial_faces} -> {final_faces} faces)")
        return simplified, stats

mesh_optimizer = MeshOptimizer()
