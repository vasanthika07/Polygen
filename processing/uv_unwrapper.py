import os
import time
import logging
import trimesh
import numpy as np
import xatlas
from typing import Tuple, Dict, Any, Union, Optional, List

from app.config import settings
from processing.uv_overlap_detector import uv_quality_auditor
from processing.uv_visualizer import uv_visualizer
from processing.blender_evaluator import blender_evaluator

logger = logging.getLogger(__name__)

class UVUnwrappingEngine:
    """
    Module 3 & Part 8: Automatic UV Unwrapping Engine
    Converts 3D mesh surfaces into optimal, non-overlapping 2D UV coordinate atlases.
    
    Implements the 9 Master Prompt Features:
    1. Mesh loading (multi-format geometry ingestion)
    2. UV generation (conformal surface parameterization)
    3. Seam handling (dihedral angle & normal deviation cutting)
    4. UV island generation (chart clustering, perimeter analysis & packing)
    5. UV overlap detection (spatial 2D intersection auditing)
    6. UV normalization (strict unit space [0, 1] bounds clamping)
    7. Texture resolution configuration (adaptive texel padding for 512, 1024, 2048, 4096)
    8. UV visualization (high-resolution layout preview image generation)
    9. UV export (OBJ with 'vt' and GLB with 'TEXCOORD_0')
    """

    def __init__(self):
        self.quality_auditor = uv_quality_auditor
        self.visualizer = uv_visualizer
        self.blender_bridge = blender_evaluator

    def load_mesh(self, mesh_input: Union[str, os.PathLike, trimesh.Trimesh, trimesh.Scene]) -> trimesh.Trimesh:
        """
        Feature 1: Mesh Loading
        Loads 3D meshes from file paths or copies in-memory geometry.
        Preserves original geometry, materials, and topology.
        """
        if isinstance(mesh_input, trimesh.Trimesh):
            return mesh_input.copy()
        
        if isinstance(mesh_input, trimesh.Scene):
            if len(mesh_input.geometry) == 0:
                raise ValueError("Input scene contains no geometry.")
            return trimesh.util.concatenate([g for g in mesh_input.geometry.values() if isinstance(g, trimesh.Trimesh)])

        abs_path = os.path.abspath(str(mesh_input))
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Mesh file not found at: {abs_path}")

        loaded = trimesh.load(abs_path, process=False)
        if isinstance(loaded, trimesh.Scene):
            if len(loaded.geometry) == 0:
                raise ValueError(f"Scene at {abs_path} contains no mesh geometry.")
            mesh = trimesh.util.concatenate([g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)])
        elif isinstance(loaded, trimesh.Trimesh):
            mesh = loaded
        else:
            raise TypeError(f"Loaded object at {abs_path} is of type {type(loaded)}, expected Trimesh.")

        return mesh

    def configure_resolution(self, resolution: int = 1024, padding: Optional[int] = None) -> Tuple[int, int]:
        """
        Feature 7: Texture Resolution Configuration
        Calculates texel padding proportionally to target resolution to prevent MIP-map bleeding.
        - 512x512: 2px padding
        - 1024x1024: 4px padding
        - 2048x2048: 8px padding
        - 4096x4096: 16px padding
        """
        valid_res = [512, 1024, 2048, 4096]
        if resolution not in valid_res:
            # Snap to closest power-of-two resolution
            resolution = min(valid_res, key=lambda x: abs(x - resolution))

        if padding is None:
            # Scaled padding: 4px at 1024 base
            padding = max(2, int(round(resolution * (4.0 / 1024.0))))

        return resolution, padding

    def unwrap(
        self,
        mesh_input: Union[str, os.PathLike, trimesh.Trimesh, trimesh.Scene],
        output_path: Optional[str] = None,
        output_format: str = "obj",
        resolution: int = 1024,
        padding: Optional[int] = None,
        normal_deviation_weight: float = 2.0,
        normal_seam_weight: float = 4.0,
        visualize: bool = True,
        preview_path: Optional[str] = None,
    ) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        """
        Executes the complete 9-feature automatic UV unwrapping pipeline.
        
        Args:
            mesh_input: File path or trimesh.Trimesh instance.
            output_path: Optional path to save the UV-mapped mesh separately.
            output_format: 'obj' or 'glb'.
            resolution: Target texture resolution (512, 1024, 2048, 4096).
            padding: Gutter padding margin in texels between UV charts.
            normal_deviation_weight: Seam cutting weight for surface angle changes.
            normal_seam_weight: Seam cutting weight for sharp dihedral feature edges.
            visualize: Whether to render a 2D UV layout preview image.
            preview_path: Optional custom path for the UV layout preview image.

        Returns:
            Tuple of (unwrapped_trimesh, comprehensive_uv_report)
        """
        start_time = time.perf_counter()
        report_log = []

        # ---------------------------------------------------------
        # 1. Feature 1: Mesh Loading & Validation
        # ---------------------------------------------------------
        mesh = self.load_mesh(mesh_input)
        orig_v_count = len(mesh.vertices)
        orig_f_count = len(mesh.faces)
        report_log.append(f"Loaded mesh with {orig_v_count} vertices and {orig_f_count} faces.")

        # Ensure contiguous float arrays for xatlas
        vertices = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
        faces = np.ascontiguousarray(mesh.faces, dtype=np.uint32)

        # ---------------------------------------------------------
        # 2. Feature 7: Texture Resolution & Padding Setup
        # ---------------------------------------------------------
        res, pad = self.configure_resolution(resolution, padding)
        report_log.append(f"Configured texture resolution: {res}x{res} with {pad}px gutter padding.")

        # ---------------------------------------------------------
        # 3. Features 2, 3, 4, 5, 6: Adaptive Seam Parameterization, Island Extraction & Overlap Check
        # ---------------------------------------------------------
        current_ndw = float(normal_deviation_weight)
        current_nsw = float(normal_seam_weight)

        best_atlas = None
        best_vmapping = None
        best_indices = None
        best_uvs = None
        best_islands = None
        best_overlap_audit = None
        best_coord_audit = None

        candidate_weights = [(current_ndw, current_nsw)]
        if current_ndw < 4.0:
            candidate_weights.append((4.0, 4.0))
        if current_ndw < 8.0:
            candidate_weights.append((8.0, 4.0))

        for ndw, nsw in candidate_weights:
            atlas = xatlas.Atlas()
            atlas.add_mesh(vertices, faces)

            chart_opts = xatlas.ChartOptions()
            chart_opts.normal_deviation_weight = float(ndw)
            chart_opts.normal_seam_weight = float(nsw)
            chart_opts.roundness_weight = 0.01
            chart_opts.straightness_weight = 6.0
            chart_opts.texture_seam_weight = 0.5
            chart_opts.fix_winding = True

            pack_opts = xatlas.PackOptions()
            pack_opts.resolution = res
            pack_opts.padding = pad
            pack_opts.rotate_charts = True
            pack_opts.rotate_charts_to_axis = True
            pack_opts.create_image = False

            atlas.generate(chart_options=chart_opts, pack_options=pack_opts)
            vmap, idx, raw_uvs = atlas.get_mesh(0)
            raw_uvs = np.clip(raw_uvs, 0.0, 1.0)

            c_count = atlas.chart_count
            islands_list: List[Dict[str, Any]] = []
            f2c: Dict[int, int] = {}
            for c_idx in range(c_count):
                chart = atlas.get_mesh_chart(0, c_idx)
                c_faces = chart.faces.tolist() if hasattr(chart.faces, "tolist") else list(chart.faces)
                for f in c_faces:
                    f2c[int(f)] = c_idx

                if len(c_faces) > 0:
                    c_face_v = idx[c_faces].flatten()
                    c_uvs = raw_uvs[c_face_v]
                    c_min = [float(x) for x in np.min(c_uvs, axis=0)]
                    c_max = [float(x) for x in np.max(c_uvs, axis=0)]
                    c_w = c_max[0] - c_min[0]
                    c_h = c_max[1] - c_min[1]
                else:
                    c_min, c_max = [0.0, 0.0], [0.0, 0.0]
                    c_w, c_h = 0.0, 0.0

                islands_list.append({
                    "chart_id": c_idx,
                    "faces_count": len(c_faces),
                    "faces": c_faces,
                    "uv_bounding_box": {"min": c_min, "max": c_max, "width": round(c_w, 4), "height": round(c_h, 4)},
                    "atlas_index": int(chart.atlas_index),
                })

            c_audit = self.quality_auditor.validate_coordinates(raw_uvs)
            o_audit = self.quality_auditor.detect_overlaps(indices=idx, uvs=raw_uvs, face_to_chart_map=f2c)

            if best_overlap_audit is None or o_audit["overlap_pairs_count"] < best_overlap_audit["overlap_pairs_count"]:
                best_atlas = atlas
                best_vmapping = vmap
                best_indices = idx
                best_uvs = raw_uvs
                best_islands = islands_list
                best_overlap_audit = o_audit
                best_coord_audit = c_audit

            if o_audit["overlap_pairs_count"] == 0:
                break

        atlas = best_atlas
        vmapping = best_vmapping
        indices = best_indices
        uvs = best_uvs
        islands = best_islands
        overlap_audit = best_overlap_audit
        coord_audit = best_coord_audit

        chart_count = atlas.chart_count
        atlas_utilization = float(atlas.utilization)
        duplicated_verts = len(vmapping) - orig_v_count

        report_log.append(f"Generated {chart_count} UV charts. Atlas area utilization: {atlas_utilization*100:.1f}%.")
        report_log.append(f"Seam parameterization introduced {duplicated_verts} boundary vertex splits.")
        report_log.append(f"UV coordinates verified: bounds=[{coord_audit['uv_min']}, {coord_audit['uv_max']}].")
        report_log.append(
            f"Overlap audit: {overlap_audit['overlap_pairs_count']} overlapping pairs, "
            f"overlap_ratio: {overlap_audit['overlap_ratio']}."
        )

        # Distortion & Stretch Metrics
        new_vertices = vertices[vmapping]
        distortion_metrics = self.quality_auditor.compute_distortion(
            vertices_3d=new_vertices,
            faces_3d=indices,
            uvs=uvs,
        )

        # ---------------------------------------------------------
        # 7. Construct Unwrapped Mesh
        # ---------------------------------------------------------
        unwrapped_mesh = trimesh.Trimesh(
            vertices=new_vertices,
            faces=indices,
            process=False,
        )
        unwrapped_mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)

        # Preserve vertex normals or recalculate consistently
        if hasattr(mesh, "vertex_normals") and len(mesh.vertex_normals) == orig_v_count:
            unwrapped_mesh.vertex_normals = mesh.vertex_normals[vmapping]
        else:
            unwrapped_mesh.fix_normals()

        # ---------------------------------------------------------
        # 8. Feature 8: UV Visualization
        # ---------------------------------------------------------
        rendered_preview_path = None
        if visualize:
            if preview_path is None:
                os.makedirs(settings.STORAGE_THUMBNAILS_DIR, exist_ok=True)
                import uuid
                slug = str(uuid.uuid4())[:8]
                preview_path = os.path.join(settings.STORAGE_THUMBNAILS_DIR, f"uv_layout_{slug}.png")

            rendered_preview_path = self.visualizer.render_uv_layout(
                uvs=uvs,
                indices=indices,
                islands=islands,
                output_image_path=preview_path,
                image_size=(res, res),
                utilization=atlas_utilization,
                overlap_info=overlap_audit,
            )
            report_log.append(f"UV layout preview saved to: {rendered_preview_path}")

        # ---------------------------------------------------------
        # 9. Feature 9: UV Mesh Export & Persistence
        # ---------------------------------------------------------
        saved_mesh_path = None
        if output_path is None:
            os.makedirs(settings.STORAGE_UNWRAPPED_DIR, exist_ok=True)
            import uuid
            slug = str(uuid.uuid4())[:8]
            output_path = os.path.join(settings.STORAGE_UNWRAPPED_DIR, f"unwrapped_{slug}.{output_format}")

        if output_path:
            abs_out = os.path.abspath(output_path)
            os.makedirs(os.path.dirname(abs_out), exist_ok=True)

            if output_format.lower() == "glb":
                glb_data = trimesh.exchange.gltf.export_glb(unwrapped_mesh)
                with open(abs_out, "wb") as f:
                    f.write(glb_data)
            else:
                obj_data = trimesh.exchange.obj.export_obj(unwrapped_mesh)
                with open(abs_out, "w", encoding="utf-8") as f:
                    f.write(obj_data)

            saved_mesh_path = abs_out
            report_log.append(f"UV-mapped mesh exported to: {abs_out}")

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # ---------------------------------------------------------
        # 10. Comprehensive Statistics & Telemetry Report
        # ---------------------------------------------------------
        report: Dict[str, Any] = {
            # Backward-compatibility keys
            "original_vertices": orig_v_count,
            "unwrapped_vertices": len(new_vertices),
            "faces": len(indices),
            "uv_min": coord_audit["uv_min"],
            "uv_max": coord_audit["uv_max"],
            "has_uv": True,

            # Feature 1-9 Detailed Metrics
            "resolution": res,
            "padding_texels": pad,
            "chart_count": chart_count,
            "atlas_utilization": round(atlas_utilization, 4),
            "atlas_utilization_percent": round(atlas_utilization * 100, 2),
            "boundary_vertex_splits": duplicated_verts,
            "islands": islands,

            # Quality Checks & Overlap Detection
            "is_valid_coordinates": coord_audit["is_valid"],
            "normalized_unit_space": coord_audit["normalized_unit_space"],
            "has_overlap": overlap_audit["has_overlap"],
            "overlap_pairs_count": overlap_audit["overlap_pairs_count"],
            "overlap_ratio": overlap_audit["overlap_ratio"],
            "inverted_faces_count": overlap_audit["inverted_faces_count"],
            "degenerate_faces_count": overlap_audit["degenerate_faces_count"],

            # Texel Stretch & Distortion
            "mean_texel_stretch": distortion_metrics["mean_texel_stretch"],
            "stretch_variance": distortion_metrics["stretch_variance"],
            "conformal_quality_score": distortion_metrics["conformal_quality_score"],

            # Artifact Paths & Telemetry
            "unwrapped_mesh_path": saved_mesh_path,
            "uv_preview_path": rendered_preview_path,
            "processing_duration_ms": duration_ms,
            "reports_and_actions": report_log,
        }

        logger.info(
            f"UV Unwrapping complete in {duration_ms} ms: {chart_count} charts, "
            f"utilization={report['atlas_utilization_percent']}%, overlaps={overlap_audit['overlap_pairs_count']}"
        )

        return unwrapped_mesh, report

uv_unwrapper = UVUnwrappingEngine()
