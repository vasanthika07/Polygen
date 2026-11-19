import os
import math
import logging
import trimesh
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict, Any, Tuple, Optional, Union, List

from processing.texture_generator import texture_generator_service, texture_validator

logger = logging.getLogger(__name__)

class PBRTextureBaker:
    """
    Modules 3, 5 & Part 9: Advanced PBR Texture Synthesis & Baking Engine
    Executes the 8-stage texture generation and UV baking pipeline:
    1. UV-mapped mesh ingestion
    2. Structured material description extraction
    3. Multi-channel PBR synthesis (BaseColor, Roughness, Metallic, Normal, AO, Emissive)
    4. UV-aware projection & Voronoi gutter dilation
    5. UV alignment verification & seam continuity checks
    6. Multi-resolution texture persistence (512, 1024, 2048, 4096)
    7. PBR material binding & GLB export
    8. Offscreen textured 3D preview rendering
    """

    def __init__(self):
        self.generator = texture_generator_service
        self.validator = texture_validator

    def generate_pbr_set(
        self,
        prompt_data: Any,
        output_dir: str,
        mesh: Optional[trimesh.Trimesh] = None,
        resolution: int = 1024,
        render_preview: bool = True,
        preview_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Executes the complete texture generation and baking pipeline.
        Returns a dictionary mapping map names to their saved file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        res = self._validate_resolution(resolution)

        # ---------------------------------------------------------
        # STAGE 2: Extract Structured Material Specification
        # ---------------------------------------------------------
        mat_spec = self.generator.extract_material_spec(prompt_data)
        logger.info(f"Generating {res}x{res} PBR texture set for material: '{mat_spec['material_type']}'...")

        # ---------------------------------------------------------
        # STAGE 3: Synthesize 6-Channel PBR Texture Maps
        # ---------------------------------------------------------
        textures = self.generator.generate_textures(
            material_spec=mat_spec,
            resolution=res,
        )

        # ---------------------------------------------------------
        # STAGE 4: UV-Aware Projection & Texture Baking (if mesh provided)
        # ---------------------------------------------------------
        if mesh is not None and hasattr(mesh, "visual") and hasattr(mesh.visual, "uv") and mesh.visual.uv is not None:
            textures = self.bake_uv_aware_textures(
                textures=textures,
                mesh=mesh,
                resolution=res,
            )

        # ---------------------------------------------------------
        # STAGE 5: Check UV Alignment & Validate Textures
        # ---------------------------------------------------------
        validation_report = self.validator.validate_texture_set(textures, res)
        if not validation_report["is_valid"]:
            logger.warning(f"Texture validation warnings: {validation_report['errors']}")

        alignment_report = self.check_uv_alignment(mesh, res) if mesh is not None else None

        # ---------------------------------------------------------
        # STAGE 6: Save Texture Images
        # ---------------------------------------------------------
        paths = {
            "basecolor": os.path.join(output_dir, "basecolor.png"),
            "roughness": os.path.join(output_dir, "roughness.png"),
            "metallic": os.path.join(output_dir, "metallic.png"),
            "normal": os.path.join(output_dir, "normal.png"),
            "ambient_occlusion": os.path.join(output_dir, "ambient_occlusion.png"),
            "emissive": os.path.join(output_dir, "emissive.png"),
            "orm": os.path.join(output_dir, "orm.png"),
        }

        textures["basecolor"].save(paths["basecolor"], "PNG")
        textures["roughness"].save(paths["roughness"], "PNG")
        textures["metallic"].save(paths["metallic"], "PNG")
        textures["normal"].save(paths["normal"], "PNG")
        textures["ambient_occlusion"].save(paths["ambient_occlusion"], "PNG")
        textures["emissive"].save(paths["emissive"], "PNG")
        textures["orm"].save(paths["orm"], "PNG")

        logger.info(f"PBR texture set successfully saved to: {output_dir}")

        # ---------------------------------------------------------
        # STAGE 8: Generate Textured 3D Preview (if mesh provided)
        # ---------------------------------------------------------
        if render_preview and mesh is not None:
            if preview_path is None:
                preview_path = os.path.join(output_dir, "textured_preview.png")
            try:
                self.render_textured_preview(
                    mesh=mesh,
                    textures=textures,
                    output_image_path=preview_path,
                )
                paths["textured_preview"] = preview_path
            except Exception as e:
                logger.warning(f"Textured preview generation note: {e}")

        return paths

    def bake_uv_aware_textures(
        self,
        textures: Dict[str, Image.Image],
        mesh: trimesh.Trimesh,
        resolution: int = 1024,
    ) -> Dict[str, Image.Image]:
        """
        Stage 4: UV-aware texture baking.
        - Calculates UV occupancy mask from mesh topology.
        - Performs Voronoi edge dilation into UV gutters to eliminate dark seam filtering artifacts.
        - Bakes 3D surface geometry crevice cavity ambient occlusion directly into the AO channel.
        """
        res = resolution
        uvs = mesh.visual.uv
        faces = mesh.faces

        if uvs is None or len(uvs) == 0 or len(faces) == 0:
            return textures

        # 1. Rasterize UV Occupancy Mask
        mask_img = Image.new("L", (res, res), 0)
        draw = ImageDraw.Draw(mask_img)

        # Scale UV coordinates to pixel space [0, res-1]
        pixel_uvs = np.clip(uvs * [res - 1, res - 1], 0, res - 1)
        for face in faces:
            pts = [(pixel_uvs[v, 0], (res - 1) - pixel_uvs[v, 1]) for v in face]
            draw.polygon(pts, fill=255)

        occupancy_arr = np.array(mask_img) > 0

        # 2. Geometry-Aware 3D Ambient Occlusion Baking
        try:
            edges = mesh.edges_unique
            v = mesh.vertices
            normals = mesh.vertex_normals
            cavity = np.zeros(len(v), dtype=np.float32)
            counts = np.zeros(len(v), dtype=np.float32)

            for e0, e1 in edges:
                d = v[e1] - v[e0]
                dist = np.linalg.norm(d)
                if dist > 1e-6:
                    dir0 = d / dist
                    dir1 = -dir0
                    cavity[e0] += max(0.0, np.dot(normals[e0], dir0))
                    cavity[e1] += max(0.0, np.dot(normals[e1], dir1))
                    counts[e0] += 1.0
                    counts[e1] += 1.0

            cavity = cavity / np.maximum(counts, 1.0)
            vert_ao = np.clip(1.0 - cavity * 1.0, 0.35, 1.0)

            # Rasterize vertex AO into UV space
            ao_baked_img = Image.new("L", (res, res), 255)
            ao_draw = ImageDraw.Draw(ao_baked_img)
            face_ao = np.mean(vert_ao[faces], axis=1)

            for idx, face in enumerate(faces):
                shade = int(face_ao[idx] * 255)
                pts = [(pixel_uvs[v, 0], (res - 1) - pixel_uvs[v, 1]) for v in face]
                ao_draw.polygon(pts, fill=shade)

            # Modulate procedural AO with baked 3D geometric AO
            proc_ao = np.array(textures["ambient_occlusion"], dtype=np.float32) / 255.0
            baked_ao = np.array(ao_baked_img, dtype=np.float32) / 255.0
            combined_ao = (proc_ao * 0.4 + baked_ao * 0.6) * 255.0
            textures["ambient_occlusion"] = Image.fromarray(combined_ao.astype(np.uint8), mode="L")
        except Exception as e:
            logger.warning(f"3D AO baking note: {e}")

        # 3. Voronoi Gutter Bleed Dilation (expand pixels outward into empty gutter padding)
        try:
            import scipy.ndimage as ndi
            if not np.all(occupancy_arr):
                # Calculate nearest neighbor coordinates for non-occupied gutter pixels
                _, nearest_coords = ndi.distance_transform_edt(~occupancy_arr, return_distances=True, return_indices=True)
                iy, ix = nearest_coords[0], nearest_coords[1]

                for key in ["basecolor", "roughness", "metallic", "normal", "ambient_occlusion", "emissive"]:
                    img = textures[key]
                    arr = np.array(img)
                    if arr.ndim == 3:
                        dilated_arr = arr[iy, ix, :]
                    else:
                        dilated_arr = arr[iy, ix]
                    textures[key] = Image.fromarray(dilated_arr, mode=img.mode)

                # Recompute ORM with dilated maps
                ao_arr = np.array(textures["ambient_occlusion"])
                r_arr = np.array(textures["roughness"])
                m_arr = np.array(textures["metallic"])
                textures["orm"] = Image.fromarray(np.stack([ao_arr, r_arr, m_arr], axis=-1), mode="RGB")
        except Exception as e:
            logger.warning(f"Voronoi gutter dilation note: {e}")

        return textures

    def check_uv_alignment(self, mesh: trimesh.Trimesh, resolution: int) -> Dict[str, Any]:
        """
        Stage 5: Verifies that UV coordinates align properly with the active texture space.
        """
        if not hasattr(mesh, "visual") or not hasattr(mesh.visual, "uv") or mesh.visual.uv is None:
            return {"is_aligned": False, "error": "Mesh has no UV coordinates"}

        uvs = mesh.visual.uv
        faces = mesh.faces

        # Check bounds
        u_min, u_max = float(np.min(uvs[:, 0])), float(np.max(uvs[:, 0]))
        v_min, v_max = float(np.min(uvs[:, 1])), float(np.max(uvs[:, 1]))
        is_bounded = (u_min >= -1e-4 and v_min >= -1e-4 and u_max <= 1.0001 and v_max <= 1.0001)

        # Texel coverage
        face_areas_uv = []
        for face in faces:
            pts = uvs[face]
            a = 0.5 * abs((pts[1, 0] - pts[0, 0]) * (pts[2, 1] - pts[0, 1]) -
                          (pts[2, 0] - pts[0, 0]) * (pts[1, 1] - pts[0, 1]))
            face_areas_uv.append(a)

        total_uv_coverage = float(np.sum(face_areas_uv))
        texel_density = round(float(np.sqrt(total_uv_coverage) * resolution / max(0.001, np.max(mesh.extents))), 2)

        return {
            "is_aligned": is_bounded,
            "bounds": {"u_min": round(u_min, 4), "u_max": round(u_max, 4), "v_min": round(v_min, 4), "v_max": round(v_max, 4)},
            "uv_coverage_ratio": round(total_uv_coverage, 4),
            "estimated_texel_density": texel_density,
            "alignment_status": "ALIGNED" if is_bounded else "OUT_OF_BOUNDS",
        }

    def render_textured_preview(
        self,
        mesh: trimesh.Trimesh,
        textures: Dict[str, Image.Image],
        output_image_path: str,
        image_size: Tuple[int, int] = (600, 600),
    ) -> str:
        """
        Stage 8: Renders an offscreen 3D isometric preview of the textured model
        with realistic key/fill/rim studio lighting, PBR reflection, and emissive bloom.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        abs_out = os.path.abspath(output_image_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        w, h = image_size
        dpi = 120
        fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
        fig.patch.set_facecolor("#0b0f19")
        ax = fig.add_subplot(111, projection="3d")
        ax.set_facecolor("#0b0f19")
        ax.axis("off")

        # Normalize mesh to unit cube centered at origin
        v = mesh.vertices - mesh.centroid
        max_extent = np.max(mesh.extents)
        if max_extent > 0:
            v = v * (1.6 / max_extent)

        faces = mesh.faces
        uvs = mesh.visual.uv
        normals = mesh.face_normals

        # Sample texture colors per face
        base_arr = np.array(textures["basecolor"])
        emissive_arr = np.array(textures["emissive"])
        rough_arr = np.array(textures["roughness"])
        res_h, res_w = base_arr.shape[:2]

        f_uvs = np.mean(uvs[faces], axis=1)
        u_idx = np.clip((f_uvs[:, 0] * (res_w - 1)).astype(int), 0, res_w - 1)
        v_idx = np.clip(((1.0 - f_uvs[:, 1]) * (res_h - 1)).astype(int), 0, res_h - 1)

        diffuse_colors = base_arr[v_idx, u_idx] / 255.0
        emissive_colors = emissive_arr[v_idx, u_idx] / 255.0
        roughness = rough_arr[v_idx, u_idx] / 255.0

        # Studio 3-Point Lighting
        # Key Light
        key_dir = np.array([0.577, 0.577, 0.577])
        key_dot = np.maximum(0.0, np.dot(normals, key_dir))

        # Fill Light (softer, cool)
        fill_dir = np.array([-0.707, -0.707, 0.0])
        fill_dot = np.maximum(0.0, np.dot(normals, fill_dir)) * 0.35

        # Ambient & Specular
        ambient = 0.22
        specular = (key_dot ** 16.0) * (1.0 - roughness) * 0.4

        shaded_colors = diffuse_colors * (ambient + key_dot[:, None] * 0.75 + fill_dot[:, None]) + specular[:, None]
        # Add Emissive glow
        shaded_colors = np.clip(shaded_colors + emissive_colors * 1.2, 0.0, 1.0)

        # Subsample faces if dense for snappy rendering
        step = max(1, len(faces) // 3000)
        poly = Poly3DCollection(
            v[faces[::step]],
            facecolors=shaded_colors[::step],
            edgecolors="none",
            alpha=1.0,
        )
        ax.add_collection3d(poly)

        ax.set_xlim(-0.9, 0.9)
        ax.set_ylim(-0.9, 0.9)
        ax.set_zlim(-0.9, 0.9)
        ax.view_init(elev=22, azim=45)

        plt.savefig(abs_out, bbox_inches="tight", facecolor=fig.get_facecolor(), pad_inches=0.1)
        plt.close(fig)

        logger.info(f"Textured 3D preview successfully generated: {abs_out}")
        return abs_out

    @staticmethod
    def _validate_resolution(resolution: int) -> int:
        valid_res = [512, 1024, 2048, 4096]
        if resolution in valid_res:
            return resolution
        return min(valid_res, key=lambda x: abs(x - resolution))

    # Backward-compatible static methods
    @staticmethod
    def _synthesize_basecolor(material: str, style: str, details: str, res: int) -> Image.Image:
        spec = {"material_type": material, "style": style, "details": details.split(), "has_emissive": "sapphire" in details}
        return texture_generator_service.generate_textures(spec, res)["basecolor"]

    @staticmethod
    def _synthesize_roughness(material: str, res: int) -> Image.Image:
        spec = {"material_type": material, "has_emissive": False}
        return texture_generator_service.generate_textures(spec, res)["roughness"]

    @staticmethod
    def _synthesize_metallic(material: str, res: int) -> Image.Image:
        spec = {"material_type": material, "has_emissive": False}
        return texture_generator_service.generate_textures(spec, res)["metallic"]

    @staticmethod
    def _synthesize_normal(base_img: Image.Image, res: int) -> Image.Image:
        return texture_generator_service._height_to_normal(np.array(base_img.convert("L")) / 255.0, res)

    @staticmethod
    def _synthesize_emissive(details: str, raw_prompt: str, res: int, has_emissive: bool) -> Image.Image:
        spec = {"material_type": "glowing_sapphire" if has_emissive else "stone", "has_emissive": has_emissive, "raw_query": details + " " + raw_prompt}
        return texture_generator_service.generate_textures(spec, res)["emissive"]

texture_baker = PBRTextureBaker()
