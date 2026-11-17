import logging
import trimesh
import numpy as np
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ExternalMeshAdapters:
    """
    Adapter bridges for optional 3D processing engines:
    - Open3D: Non-manifold edge removal, cluster connected triangles, normal estimation
    - PyMeshLab: MeshLab filters, hole filling, topological repairs
    Provides runtime discovery, graceful fallbacks, and status reporting.
    """

    def __init__(self):
        self.open3d_available = self._check_open3d()
        self.pymeshlab_available = self._check_pymeshlab()

    def _check_open3d(self) -> bool:
        try:
            import open3d as o3d
            logger.info("Open3D engine available for advanced mesh filtering.")
            return True
        except ImportError:
            return False

    def _check_pymeshlab(self) -> bool:
        try:
            import pymeshlab
            logger.info("PyMeshLab engine available for advanced filter automation.")
            return True
        except ImportError:
            return False

    def get_adapter_status(self) -> Dict[str, Any]:
        return {
            "trimesh_available": True,
            "open3d_available": self.open3d_available,
            "pymeshlab_available": self.pymeshlab_available,
            "active_backends": [
                "trimesh",
                *(["open3d"] if self.open3d_available else []),
                *(["pymeshlab"] if self.pymeshlab_available else []),
            ]
        }

    def process_with_open3d(self, mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        """Applies Open3D geometry filtering if available."""
        if not self.open3d_available:
            return mesh, {"applied": False, "reason": "Open3D not installed in environment"}

        try:
            import open3d as o3d
            # Convert trimesh to open3d TriangleMesh
            o3d_mesh = o3d.geometry.TriangleMesh()
            o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
            o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces)

            # Apply Open3D cleaning operations
            o3d_mesh.remove_duplicated_vertices()
            o3d_mesh.remove_duplicated_triangles()
            o3d_mesh.remove_degenerate_triangles()
            o3d_mesh.remove_unreferenced_vertices()
            o3d_mesh.remove_non_manifold_edges()
            o3d_mesh.compute_vertex_normals()

            # Convert back to trimesh
            new_verts = np.asarray(o3d_mesh.vertices)
            new_faces = np.asarray(o3d_mesh.triangles)
            processed_mesh = trimesh.Trimesh(vertices=new_verts, faces=new_faces, process=True)

            return processed_mesh, {
                "applied": True,
                "engine": "open3d",
                "processed_vertices": len(new_verts),
                "processed_faces": len(new_faces)
            }
        except Exception as e:
            logger.warning(f"Open3D processing encountered error: {e}. Falling back to native pipeline.")
            return mesh, {"applied": False, "error": str(e)}

    def process_with_pymeshlab(self, mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        """Applies PyMeshLab topological repair filters if available."""
        if not self.pymeshlab_available:
            return mesh, {"applied": False, "reason": "PyMeshLab not installed in environment"}

        try:
            import pymeshlab
            ms = pymeshlab.MeshSet()
            m = pymeshlab.Mesh(vertex_matrix=mesh.vertices, face_matrix=mesh.faces)
            ms.add_mesh(m)

            # PyMeshLab cleaning filters
            ms.apply_filter('meshing_remove_duplicate_vertices')
            ms.apply_filter('meshing_remove_duplicate_faces')
            ms.apply_filter('meshing_remove_null_faces')
            ms.apply_filter('meshing_repair_non_manifold_edges')
            ms.apply_filter('meshing_repair_non_manifold_vertices')

            current_mesh = ms.current_mesh()
            new_verts = current_mesh.vertex_matrix()
            new_faces = current_mesh.face_matrix()
            processed_mesh = trimesh.Trimesh(vertices=new_verts, faces=new_faces, process=True)

            return processed_mesh, {
                "applied": True,
                "engine": "pymeshlab",
                "processed_vertices": len(new_verts),
                "processed_faces": len(new_faces)
            }
        except Exception as e:
            logger.warning(f"PyMeshLab processing encountered error: {e}. Falling back to native pipeline.")
            return mesh, {"applied": False, "error": str(e)}

external_adapters = ExternalMeshAdapters()
