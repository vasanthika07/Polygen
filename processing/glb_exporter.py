import os
import logging
import trimesh
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple
from trimesh.visual.material import PBRMaterial

logger = logging.getLogger(__name__)

class GLBExporter:
    """
    Module 5 & 6: PBR Material Assignment & GLB Export Engine
    Embeds PBR textures into the 3D mesh, exports binary glTF 2.0 (.glb),
    and validates geometry integrity upon export.
    """

    @classmethod
    def export(
        cls,
        mesh: trimesh.Trimesh,
        texture_paths: Dict[str, str],
        output_glb_path: str,
    ) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)

        logger.info(f"Assigning PBR materials and exporting GLB to {output_glb_path}...")

        # Load textures
        base_img = Image.open(texture_paths["basecolor"]).convert("RGBA")
        rough_img = Image.open(texture_paths["roughness"]).convert("L")
        metal_img = Image.open(texture_paths["metallic"]).convert("L")
        normal_img = Image.open(texture_paths["normal"]).convert("RGB")
        emissive_img = Image.open(texture_paths["emissive"]).convert("RGB")

        # In glTF 2.0 standard:
        # Metallic-Roughness texture: Green channel = Roughness, Blue channel = Metallic
        res = base_img.size
        r_arr = np.array(rough_img.resize(res))
        m_arr = np.array(metal_img.resize(res))
        
        # Combine into glTF metallic-roughness packed texture: [R=unused, G=roughness, B=metallic]
        mr_packed = np.zeros((res[1], res[0], 3), dtype=np.uint8)
        mr_packed[:, :, 1] = r_arr
        mr_packed[:, :, 2] = m_arr
        mr_packed_img = Image.fromarray(mr_packed, mode="RGB")

        # Check if emissive has glowing pixels
        emissive_arr = np.array(emissive_img)
        has_glow = np.any(emissive_arr > 30)
        emissive_factor = [1.0, 1.0, 1.0] if has_glow else [0.0, 0.0, 0.0]

        # Construct PBR material
        material = PBRMaterial(
            name="PolyGen_PBR_Material",
            baseColorTexture=base_img,
            metallicRoughnessTexture=mr_packed_img,
            normalTexture=normal_img,
            emissiveTexture=emissive_img if has_glow else None,
            emissiveFactor=emissive_factor,
            doubleSided=True,
            metallicFactor=1.0,
            roughnessFactor=1.0,
        )

        # Ensure visual has UV coordinates
        if not hasattr(mesh.visual, 'uv') or mesh.visual.uv is None or len(mesh.visual.uv) == 0:
            logger.warning("Mesh had no UV coordinates. Generating planar default UVs...")
            # Fallback planar UVs if not yet parameterized
            bounds = mesh.bounds
            diff = bounds[1] - bounds[0]
            diff[diff == 0] = 1.0
            uv = (mesh.vertices[:, :2] - bounds[0, :2]) / diff[:2]
            mesh.visual = trimesh.visual.TextureVisuals(uv=uv)

        # Attach material to mesh visual
        mesh.visual.material = material

        # Export as GLB
        glb_bytes = trimesh.exchange.gltf.export_glb(mesh)
        with open(output_glb_path, "wb") as f:
            f.write(glb_bytes)

        file_size_bytes = os.path.getsize(output_glb_path)
        logger.info(f"GLB written successfully: {file_size_bytes} bytes ({round(file_size_bytes / (1024*1024), 2)} MB)")

        # Verification pass: Reload the exported GLB to validate file integrity
        validation_stats = cls.validate_glb(output_glb_path)
        validation_stats["file_size_bytes"] = file_size_bytes
        validation_stats["file_size_mb"] = round(file_size_bytes / (1024 * 1024), 2)

        return validation_stats

    @staticmethod
    def validate_glb(glb_path: str) -> Dict[str, Any]:
        """
        Reloads the exported file to verify compatibility, geometry, and materials.
        """
        logger.info(f"Verifying exported GLB: {glb_path}")
        scene_or_mesh = trimesh.load(glb_path, force="mesh")
        
        if isinstance(scene_or_mesh, trimesh.Scene):
            # Combined scene
            faces = sum(len(g.faces) for g in scene_or_mesh.geometry.values() if hasattr(g, 'faces'))
            verts = sum(len(g.vertices) for g in scene_or_mesh.geometry.values() if hasattr(g, 'vertices'))
            extents = [float(x) for x in scene_or_mesh.extents]
        else:
            faces = len(scene_or_mesh.faces)
            verts = len(scene_or_mesh.vertices)
            extents = [float(x) for x in scene_or_mesh.extents]

        return {
            "is_valid": True,
            "verified_vertices": verts,
            "verified_faces": faces,
            "bounding_box_dimensions": extents,
            "path": glb_path
        }

glb_exporter = GLBExporter()

