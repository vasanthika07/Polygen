import logging
import numpy as np
import trimesh
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MeshStatisticsExtractor:
    """
    Computes comprehensive topological and geometric statistics for 3D polygonal meshes:
    - Vertex, face, and edge counts
    - Euler characteristic and genus
    - Watertightness and boundary edge analysis
    - Winding consistency and normal orientation
    - Non-manifold edge and vertex detection
    - Connected component clustering
    - Bounding-box (AABB and OBB) metrics and volume
    - Surface area and aspect ratio distributions
    """

    @classmethod
    def extract(cls, mesh: trimesh.Trimesh) -> Dict[str, Any]:
        num_vertices = int(len(mesh.vertices))
        num_faces = int(len(mesh.faces))

        if num_vertices == 0 or num_faces == 0:
            return {
                "vertex_count": num_vertices,
                "face_count": num_faces,
                "edge_count": 0,
                "is_empty": True,
                "is_watertight": False,
                "is_manifold": False,
                "connected_components": 0,
            }

        # 1. Edge and Topology Metrics
        num_edges = int(len(mesh.edges_unique)) if hasattr(mesh, "edges_unique") else 0
        euler_characteristic = num_vertices - num_edges + num_faces
        # Genus g = (2 - chi) / 2 for orientable closed surfaces
        genus = max(0, (2 - euler_characteristic) // 2) if mesh.is_watertight else None

        # 2. Watertightness and Boundary Edges
        is_watertight = bool(mesh.is_watertight)
        # Boundary edges are edges that belong to exactly 1 face
        edge_face_counts = np.bincount(mesh.edges_unique_inverse)
        boundary_edges_count = int(np.sum(edge_face_counts == 1))
        # Non-manifold edges belong to > 2 faces
        non_manifold_edges_count = int(np.sum(edge_face_counts > 2))

        # 3. Winding Consistency & Normals
        is_winding_consistent = bool(mesh.is_winding_consistent)
        has_vertex_normals = mesh.vertex_normals is not None and len(mesh.vertex_normals) == num_vertices
        has_face_normals = mesh.face_normals is not None and len(mesh.face_normals) == num_faces

        # 4. Connected Components Analysis
        try:
            components = trimesh.graph.connected_components(
                mesh.face_adjacency,
                min_len=1,
                nodes=np.arange(num_faces)
            )
            connected_components_count = len(components)
            component_face_counts = sorted([len(c) for c in components], reverse=True)
        except Exception:
            connected_components_count = 1
            component_face_counts = [num_faces]

        # 5. Bounding Box & Dimensions
        bounds = mesh.bounds
        extents = [float(x) for x in mesh.extents]
        aabb_volume = float(extents[0] * extents[1] * extents[2])
        center = [float(x) for x in mesh.centroid]

        # Oriented Bounding Box
        obb_extents = None
        try:
            obb = mesh.bounding_box_oriented
            obb_extents = [float(x) for x in obb.extents]
        except Exception:
            obb_extents = extents

        # 6. Surface Area & Volume
        surface_area = round(float(mesh.area), 6) if hasattr(mesh, "area") else 0.0
        volume = None
        if is_watertight and getattr(mesh, "is_volume", False):
            try:
                v = float(mesh.volume)
                if np.isfinite(v) and v > 0:
                    volume = round(v, 6)
            except Exception:
                volume = None

        # 8. Face Aspect Ratios (Quality Assessment)
        try:
            triangles = mesh.triangles
            a = np.linalg.norm(triangles[:, 1] - triangles[:, 0], axis=1)
            b = np.linalg.norm(triangles[:, 2] - triangles[:, 1], axis=1)
            c = np.linalg.norm(triangles[:, 0] - triangles[:, 2], axis=1)
            perimeter = a + b + c
            # inradius r = Area / (0.5 * perimeter)
            # circumradius R = (a*b*c) / (4 * Area)
            face_areas = mesh.area_faces
            valid_area = face_areas > 1e-12
            aspect_ratios = np.zeros(len(triangles))
            if np.any(valid_area):
                s = perimeter[valid_area] / 2.0
                r = face_areas[valid_area] / np.maximum(s, 1e-12)
                R = (a[valid_area] * b[valid_area] * c[valid_area]) / (4.0 * np.maximum(face_areas[valid_area], 1e-12))
                aspect_ratios[valid_area] = R / (2.0 * np.maximum(r, 1e-12))
            mean_aspect_ratio = round(float(np.mean(aspect_ratios[valid_area])), 3) if np.any(valid_area) else 1.0
        except Exception:
            mean_aspect_ratio = 1.0

        stats: Dict[str, Any] = {
            "vertex_count": num_vertices,
            "face_count": num_faces,
            "edge_count": num_edges,
            "euler_characteristic": euler_characteristic,
            "genus": genus,
            "is_watertight": is_watertight,
            "is_winding_consistent": is_winding_consistent,
            "is_manifold": (non_manifold_edges_count == 0),
            "boundary_edges_count": boundary_edges_count,
            "non_manifold_edges_count": non_manifold_edges_count,
            "connected_components": connected_components_count,
            "component_face_counts": component_face_counts[:10], # Top 10
            "bounding_box_extents": extents,
            "bounding_box_volume": round(aabb_volume, 6),
            "oriented_bounding_box_extents": obb_extents,
            "centroid": center,
            "surface_area": surface_area,
            "volume": volume,
            "has_vertex_normals": has_vertex_normals,
            "has_face_normals": has_face_normals,
            "mean_face_aspect_ratio": mean_aspect_ratio,
        }
        return stats

mesh_statistics_extractor = MeshStatisticsExtractor()
