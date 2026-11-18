import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from shapely.geometry import Polygon
from shapely.strtree import STRtree

logger = logging.getLogger(__name__)

class UVQualityAuditor:
    """
    Quality and topological validation auditor for 2D UV texture coordinate layouts.
    Executes:
    - Finite coordinate validation (no NaN / Inf, strict [0, 1] bounds)
    - 2D Triangle degeneracy and inverted winding (negative signed area) detection
    - Spatial 2D triangle-triangle collision & overlap detection using GEOS STRtree
    - Intra-island (self-overlap) and inter-island (packing collision) auditing
    - Conformal distortion & texel stretch analysis comparing 3D surface area to 2D UV area
    """

    @staticmethod
    def validate_coordinates(uvs: np.ndarray) -> Dict[str, Any]:
        """
        Verifies that UV coordinates are mathematically finite, non-NaN,
        and bounded within the normalized [0.0, 1.0] unit texture square.
        """
        if uvs is None or len(uvs) == 0:
            return {
                "is_valid": False,
                "error": "UV coordinates array is empty or None",
                "uv_min": [0.0, 0.0],
                "uv_max": [0.0, 0.0],
                "has_nan": False,
                "has_inf": False,
                "out_of_bounds_count": 0,
            }

        uvs_arr = np.asarray(uvs, dtype=np.float64)
        has_nan = bool(np.isnan(uvs_arr).any())
        has_inf = bool(np.isinf(uvs_arr).any())

        if has_nan or has_inf:
            return {
                "is_valid": False,
                "error": "UV coordinates contain NaN or Inf values",
                "uv_min": [float("nan"), float("nan")],
                "uv_max": [float("nan"), float("nan")],
                "has_nan": has_nan,
                "has_inf": has_inf,
                "out_of_bounds_count": int(np.sum(~np.isfinite(uvs_arr))),
            }

        uv_min = [float(x) for x in np.min(uvs_arr, axis=0)]
        uv_max = [float(x) for x in np.max(uvs_arr, axis=0)]

        # Allow slight numerical floating-point epsilon tolerance (1e-5)
        eps = 1e-5
        out_of_bounds_mask = (uvs_arr < (0.0 - eps)) | (uvs_arr > (1.0 + eps))
        out_of_bounds_count = int(np.sum(out_of_bounds_mask.any(axis=1)))
        is_bounded = out_of_bounds_count == 0

        return {
            "is_valid": is_bounded and not has_nan and not has_inf,
            "uv_min": uv_min,
            "uv_max": uv_max,
            "has_nan": has_nan,
            "has_inf": has_inf,
            "out_of_bounds_count": out_of_bounds_count,
            "normalized_unit_space": is_bounded,
        }

    @staticmethod
    def detect_overlaps(
        indices: np.ndarray,
        uvs: np.ndarray,
        face_to_chart_map: Optional[Dict[int, int]] = None,
        area_tolerance: float = 1e-7,
    ) -> Dict[str, Any]:
        """
        Performs rigorous 2D spatial intersection testing across all UV triangles.
        Uses GEOS/Shapely STRtree broad-phase acceleration followed by exact polygon
        clipping to calculate overlapping areas.
        """
        indices_arr = np.asarray(indices, dtype=np.int64)
        uvs_arr = np.asarray(uvs, dtype=np.float64)
        num_faces = len(indices_arr)

        if num_faces == 0 or len(uvs_arr) == 0:
            return {
                "has_overlap": False,
                "overlap_pairs_count": 0,
                "total_overlap_area": 0.0,
                "overlap_ratio": 0.0,
                "inverted_faces_count": 0,
                "degenerate_faces_count": 0,
                "intra_island_overlaps": 0,
                "inter_island_overlaps": 0,
                "details": [],
            }

        # 1. Triangle 2D signed area calculation
        # Signed Area = 0.5 * ((u1 - u0)*(v2 - v0) - (u2 - u0)*(v1 - v0))
        u0 = uvs_arr[indices_arr[:, 0]]
        u1 = uvs_arr[indices_arr[:, 1]]
        u2 = uvs_arr[indices_arr[:, 2]]

        signed_areas = 0.5 * ((u1[:, 0] - u0[:, 0]) * (u2[:, 1] - u0[:, 1]) -
                               (u2[:, 0] - u0[:, 0]) * (u1[:, 1] - u0[:, 1]))

        degenerate_indices = np.where(np.abs(signed_areas) <= area_tolerance)[0].tolist()
        total_uv_area = float(np.sum(np.abs(signed_areas)))

        # Inverted faces are faces whose winding orientation contradicts their chart majority orientation
        inverted_indices = []
        if face_to_chart_map is not None:
            chart_signs: Dict[int, List[float]] = {}
            chart_face_indices: Dict[int, List[int]] = {}
            for f_i in range(num_faces):
                if f_i in degenerate_indices:
                    continue
                c_id = face_to_chart_map.get(f_i, 0)
                chart_signs.setdefault(c_id, []).append(np.sign(signed_areas[f_i]))
                chart_face_indices.setdefault(c_id, []).append(f_i)

            for c_id, signs in chart_signs.items():
                if len(signs) == 0:
                    continue
                # Determine majority sign in chart (+1 or -1)
                majority_sign = 1.0 if np.sum(signs) >= 0 else -1.0
                f_indices = chart_face_indices[c_id]
                for f_i, s in zip(f_indices, signs):
                    if s != majority_sign and s != 0:
                        inverted_indices.append(f_i)
        else:
            majority_sign = 1.0 if np.sum(np.sign(signed_areas)) >= 0 else -1.0
            inverted_indices = [
                f_i for f_i in range(num_faces)
                if f_i not in degenerate_indices and np.sign(signed_areas[f_i]) != majority_sign and np.sign(signed_areas[f_i]) != 0
            ]

        # 2. Build 2D Shapely polygons for broad-phase R-tree search
        polys: List[Optional[Polygon]] = []
        valid_poly_indices = []

        for f_idx in range(num_faces):
            tri_uv = uvs_arr[indices_arr[f_idx]]
            try:
                poly = Polygon(tri_uv)
                if poly.is_valid and poly.area > area_tolerance:
                    polys.append(poly)
                    valid_poly_indices.append(f_idx)
                else:
                    polys.append(None)
            except Exception:
                polys.append(None)

        valid_polys = [p for p in polys if p is not None]
        overlap_pairs = []
        total_overlap_area = 0.0
        intra_island = 0
        inter_island = 0

        if len(valid_polys) > 1:
            tree = STRtree(valid_polys)
            # Query candidate intersections
            query_results = tree.query(valid_polys, predicate="intersects")
            q_i, q_j = query_results[0], query_results[1]

            checked_pairs = set()

            for k in range(len(q_i)):
                idx_a, idx_b = int(q_i[k]), int(q_j[k])
                if idx_a >= idx_b:
                    continue

                orig_face_a = valid_poly_indices[idx_a]
                orig_face_b = valid_poly_indices[idx_b]

                pair_key = (orig_face_a, orig_face_b)
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                poly_a = valid_polys[idx_a]
                poly_b = valid_polys[idx_b]

                # Check if faces share vertices in topology
                shared_verts = set(indices_arr[orig_face_a]).intersection(set(indices_arr[orig_face_b]))
                
                # If they share an edge (2 vertices) or corner (1 vertex), adjacent contact is expected.
                # True geometric overlap occurs when intersection 2D area > tolerance.
                inter = poly_a.intersection(poly_b)
                inter_area = float(inter.area)

                if inter_area > area_tolerance:
                    is_same_chart = False
                    if face_to_chart_map is not None:
                        chart_a = face_to_chart_map.get(orig_face_a, -1)
                        chart_b = face_to_chart_map.get(orig_face_b, -2)
                        is_same_chart = (chart_a == chart_b)
                        if is_same_chart:
                            intra_island += 1
                        else:
                            inter_island += 1

                    overlap_pairs.append({
                        "face_a": orig_face_a,
                        "face_b": orig_face_b,
                        "shared_vertices": len(shared_verts),
                        "intersection_area": round(inter_area, 8),
                        "intra_island": is_same_chart,
                    })
                    total_overlap_area += inter_area

        overlap_ratio = (total_overlap_area / max(1e-8, total_uv_area)) if total_uv_area > 0 else 0.0

        return {
            "has_overlap": len(overlap_pairs) > 0,
            "overlap_pairs_count": len(overlap_pairs),
            "total_overlap_area": round(total_overlap_area, 8),
            "total_uv_area": round(total_uv_area, 6),
            "overlap_ratio": round(overlap_ratio, 6),
            "inverted_faces_count": len(inverted_indices),
            "inverted_face_indices": inverted_indices[:50],  # cap for telemetry
            "degenerate_faces_count": len(degenerate_indices),
            "intra_island_overlaps": intra_island,
            "inter_island_overlaps": inter_island,
            "details": overlap_pairs[:100],  # cap for telemetry
        }

    @staticmethod
    def compute_distortion(
        vertices_3d: np.ndarray,
        faces_3d: np.ndarray,
        uvs: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Measures conformal distortion and texel stretch by comparing 3D triangle
        surface areas against their 2D UV parametric areas.
        """
        v_arr = np.asarray(vertices_3d, dtype=np.float64)
        f_arr = np.asarray(faces_3d, dtype=np.int64)
        uv_arr = np.asarray(uvs, dtype=np.float64)

        if len(f_arr) == 0:
            return {"mean_stretch": 1.0, "stretch_variance": 0.0, "total_3d_area": 0.0, "total_uv_area": 0.0}

        # 3D surface area: 0.5 * ||(v1 - v0) x (v2 - v0)||
        v0 = v_arr[f_arr[:, 0]]
        v1 = v_arr[f_arr[:, 1]]
        v2 = v_arr[f_arr[:, 2]]
        cross_3d = np.cross(v1 - v0, v2 - v0)
        area_3d = 0.5 * np.linalg.norm(cross_3d, axis=1)

        # 2D UV area: 0.5 * |(u1 - u0)*(v2 - v0) - (u2 - u0)*(v1 - v0)|
        u0 = uv_arr[f_arr[:, 0]]
        u1 = uv_arr[f_arr[:, 1]]
        u2 = uv_arr[f_arr[:, 2]]
        area_2d = 0.5 * np.abs((u1[:, 0] - u0[:, 0]) * (u2[:, 1] - u0[:, 1]) -
                               (u2[:, 0] - u0[:, 0]) * (u1[:, 1] - u0[:, 1]))

        total_3d = float(np.sum(area_3d))
        total_2d = float(np.sum(area_2d))

        if total_3d > 1e-8 and total_2d > 1e-8:
            # Normalized area distribution
            norm_3d = area_3d / total_3d
            norm_2d = area_2d / total_2d
            # Avoid division by zero
            valid_mask = norm_3d > 1e-8
            stretch_factors = np.ones_like(norm_3d)
            stretch_factors[valid_mask] = norm_2d[valid_mask] / norm_3d[valid_mask]

            mean_stretch = float(np.mean(stretch_factors))
            stretch_variance = float(np.var(stretch_factors))
            min_stretch = float(np.min(stretch_factors))
            max_stretch = float(np.max(stretch_factors))
        else:
            mean_stretch = 1.0
            stretch_variance = 0.0
            min_stretch = 1.0
            max_stretch = 1.0

        return {
            "total_3d_surface_area": round(total_3d, 4),
            "total_uv_area": round(total_2d, 6),
            "mean_texel_stretch": round(mean_stretch, 4),
            "stretch_variance": round(stretch_variance, 6),
            "min_stretch": round(min_stretch, 4),
            "max_stretch": round(max_stretch, 4),
            "conformal_quality_score": round(max(0.0, 100.0 - (stretch_variance * 50.0)), 2),
        }

uv_quality_auditor = UVQualityAuditor()
