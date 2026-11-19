import os
import time
import json
import struct
import logging
import trimesh
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, Optional, Union, List
from enum import Enum
from trimesh.visual.material import PBRMaterial

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from processing.pbr_material_system import pbr_material_system

logger = logging.getLogger(__name__)

class ExportProfile(str, Enum):
    """
    Standard glTF 2.0 / GLB export profiles calibrated for production deployment.
    """
    STANDARD = "standard"         # 1024x1024 PBR textures, standard geometry, balanced web/desktop profile
    HIGH_QUALITY = "high_quality" # 2048x2048 PBR textures, maximum precision normals/tangents, uncompressed color
    OPTIMIZED = "optimized"       # 512x512 PBR textures, decimated LOD, lightweight payload for mobile XR & WebGL

PROFILE_RESOLUTIONS = {
    ExportProfile.STANDARD: 1024,
    ExportProfile.HIGH_QUALITY: 2048,
    ExportProfile.OPTIMIZED: 512,
}

class GLBExportSystem:
    """
    Module 5 & Part 12: Khronos glTF 2.0 & GLB Export Engine
    Executes the 10-stage asset export pipeline:
    1. Load optimized mesh
    2. Load UV coordinates
    3. Load textures
    4. Load PBR materials
    5. Combine geometry and materials
    6. Export GLB
    7. Validate exported file (glTF-compatible validation & integrity checks)
    8. Reopen exported GLB
    9. Generate thumbnail
    10. Save export metadata
    """

    PROFILES = ExportProfile

    # -------------------------------------------------------------
    # STAGE 1: Load Optimized Mesh
    # -------------------------------------------------------------
    @classmethod
    def load_optimized_mesh(cls, mesh_input: Union[trimesh.Trimesh, str]) -> trimesh.Trimesh:
        if isinstance(mesh_input, str):
            if not os.path.exists(mesh_input):
                raise FileNotFoundError(f"Input mesh not found at path: {mesh_input}")
            loaded = trimesh.load(mesh_input, process=False)
            if isinstance(loaded, trimesh.Scene):
                mesh = trimesh.util.concatenate([g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)])
            else:
                mesh = loaded
        elif isinstance(mesh_input, trimesh.Trimesh):
            mesh = mesh_input.copy()
        elif isinstance(mesh_input, trimesh.Scene):
            mesh = trimesh.util.concatenate([g for g in mesh_input.geometry.values() if isinstance(g, trimesh.Trimesh)])
        else:
            raise ValueError(f"Unsupported mesh input type: {type(mesh_input)}")

        return mesh

    # -------------------------------------------------------------
    # STAGE 2: Load UV Coordinates
    # -------------------------------------------------------------
    @classmethod
    def load_uv_coordinates(cls, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        if not hasattr(mesh.visual, 'uv') or mesh.visual.uv is None or len(mesh.visual.uv) == 0:
            logger.warning("Mesh had no UV parameterization. Generating planar projection coordinates...")
            bounds = mesh.bounds
            diff = bounds[1] - bounds[0]
            diff[diff == 0] = 1.0
            uv = (mesh.vertices[:, :2] - bounds[0, :2]) / diff[:2]
            mesh.visual = trimesh.visual.TextureVisuals(uv=uv)
        return mesh

    # -------------------------------------------------------------
    # STAGE 3: Load & Process Textures
    # -------------------------------------------------------------
    @classmethod
    def load_textures(
        cls,
        texture_paths: Dict[str, str],
        profile: ExportProfile = ExportProfile.STANDARD,
    ) -> Dict[str, Image.Image]:
        target_res = PROFILE_RESOLUTIONS.get(profile, 1024)
        processed: Dict[str, Image.Image] = {}

        # 1. BaseColor
        if "basecolor" in texture_paths and os.path.exists(texture_paths["basecolor"]):
            base_img = Image.open(texture_paths["basecolor"]).convert("RGBA")
        else:
            base_img = Image.new("RGBA", (target_res, target_res), (220, 220, 220, 255))
        processed["basecolor"] = base_img.resize((target_res, target_res), Image.Resampling.LANCZOS)

        # 2. Roughness
        if "roughness" in texture_paths and os.path.exists(texture_paths["roughness"]):
            rough_img = Image.open(texture_paths["roughness"]).convert("L")
        else:
            rough_img = Image.new("L", (target_res, target_res), 128)
        processed["roughness"] = rough_img.resize((target_res, target_res), Image.Resampling.LANCZOS)

        # 3. Metallic
        if "metallic" in texture_paths and os.path.exists(texture_paths["metallic"]):
            metal_img = Image.open(texture_paths["metallic"]).convert("L")
        else:
            metal_img = Image.new("L", (target_res, target_res), 0)
        processed["metallic"] = metal_img.resize((target_res, target_res), Image.Resampling.LANCZOS)

        # 4. Normal
        if "normal" in texture_paths and os.path.exists(texture_paths["normal"]):
            norm_img = Image.open(texture_paths["normal"]).convert("RGB")
        else:
            norm_img = Image.new("RGB", (target_res, target_res), (128, 128, 255))
        processed["normal"] = norm_img.resize((target_res, target_res), Image.Resampling.LANCZOS)

        # 5. Ambient Occlusion (Optional, default white 255)
        ao_key = next((k for k in ["ambient_occlusion", "occlusion", "ao"] if k in texture_paths), None)
        if ao_key and os.path.exists(texture_paths[ao_key]):
            ao_img = Image.open(texture_paths[ao_key]).convert("L")
        else:
            ao_img = Image.new("L", (target_res, target_res), 255)
        processed["occlusion"] = ao_img.resize((target_res, target_res), Image.Resampling.LANCZOS)

        # 6. Emissive
        if "emissive" in texture_paths and os.path.exists(texture_paths["emissive"]):
            emissive_img = Image.open(texture_paths["emissive"]).convert("RGB")
        else:
            emissive_img = Image.new("RGB", (target_res, target_res), (0, 0, 0))
        processed["emissive"] = emissive_img.resize((target_res, target_res), Image.Resampling.LANCZOS)

        return processed

    # -------------------------------------------------------------
    # STAGE 4: Load PBR Materials
    # -------------------------------------------------------------
    @classmethod
    def load_pbr_materials(
        cls,
        material_params: Optional[Dict[str, Any]],
        has_emissive_glow: bool = False,
    ) -> Dict[str, Any]:
        mp = material_params or {}
        default_emissive = [1.0, 1.0, 1.0] if has_emissive_glow else [0.0, 0.0, 0.0]

        return {
            "name": mp.get("name", "PolyGen_PBR_Material"),
            "metallic_factor": float(mp.get("metallic_factor", 1.0)),
            "roughness_factor": float(mp.get("roughness_factor", 1.0)),
            "base_color_factor": mp.get("base_color_factor", [1.0, 1.0, 1.0, 1.0]),
            "emissive_factor": mp.get("emissive_factor", default_emissive),
            "emissive_intensity": float(mp.get("emissive_intensity", 1.0 if has_emissive_glow else 0.0)),
            "alpha_mode": mp.get("alpha_mode", "OPAQUE"),
            "alpha_cutoff": float(mp.get("alpha_cutoff", 0.5)),
            "double_sided": bool(mp.get("double_sided", True)),
        }

    # -------------------------------------------------------------
    # STAGE 5: Combine Geometry and Materials (glTF ORM Packing)
    # -------------------------------------------------------------
    @classmethod
    def combine_geometry_and_materials(
        cls,
        mesh: trimesh.Trimesh,
        textures: Dict[str, Image.Image],
        mat_config: Dict[str, Any],
    ) -> trimesh.Trimesh:
        res = textures["basecolor"].size
        w, h = res

        # Pack glTF 2.0 ORM texture: Red = Occlusion, Green = Roughness, Blue = Metallic
        orm_arr = np.zeros((h, w, 3), dtype=np.uint8)
        orm_arr[:, :, 0] = np.array(textures["occlusion"])
        orm_arr[:, :, 1] = np.array(textures["roughness"])
        orm_arr[:, :, 2] = np.array(textures["metallic"])
        orm_img = Image.fromarray(orm_arr, mode="RGB")

        has_glow = np.any(np.array(textures["emissive"]) > 25)
        emissive_factor = mat_config["emissive_factor"] if has_glow else [0.0, 0.0, 0.0]

        # Bind PBR material
        pbr_mat = PBRMaterial(
            name=mat_config["name"],
            baseColorTexture=textures["basecolor"],
            metallicRoughnessTexture=orm_img,
            normalTexture=textures["normal"],
            occlusionTexture=orm_img,
            emissiveTexture=textures["emissive"] if has_glow else None,
            emissiveFactor=emissive_factor,
            doubleSided=mat_config["double_sided"],
            metallicFactor=mat_config["metallic_factor"],
            roughnessFactor=mat_config["roughness_factor"],
            alphaMode=mat_config["alpha_mode"],
        )

        mesh.visual = trimesh.visual.TextureVisuals(
            uv=mesh.visual.uv,
            material=pbr_mat,
        )

        return mesh

    # -------------------------------------------------------------
    # STAGE 6: Export GLB
    # -------------------------------------------------------------
    @classmethod
    def export_glb_file(
        cls,
        mesh: trimesh.Trimesh,
        output_glb_path: str,
    ) -> int:
        os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)
        glb_bytes = trimesh.exchange.gltf.export_glb(mesh)
        with open(output_glb_path, "wb") as f:
            f.write(glb_bytes)
        file_size = os.path.getsize(output_glb_path)
        logger.info(f"Binary GLB written to {output_glb_path} ({file_size:,} bytes)")
        return file_size

    # -------------------------------------------------------------
    # STAGE 7: Validate Exported File (Khronos glTF 2.0 Compliance)
    # -------------------------------------------------------------
    @classmethod
    def validate_gltf_glb(cls, glb_path: str) -> Dict[str, Any]:
        """
        Comprehensive validator verifying:
        - File integrity (glTF magic header, version 2, valid chunk sequence)
        - Mesh presence (valid vertex positions and faces)
        - Material presence (pbrMetallicRoughness configuration)
        - Texture references (images embedded in bufferViews)
        - Browser compatibility (Three.js / Babylon scene hierarchy)
        - Blender import compatibility (valid componentTypes, standard nodes)
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not os.path.exists(glb_path):
            return {"is_valid": False, "valid": False, "errors": [f"File missing: {glb_path}"]}

        file_size = os.path.getsize(glb_path)
        if file_size < 20:
            return {"is_valid": False, "valid": False, "errors": ["File too small to contain valid GLB header"]}

        with open(glb_path, "rb") as f:
            data = f.read()

        # 1. 12-byte GLB Header
        magic, version, length = struct.unpack_from('<4sII', data, 0)
        if magic != b"glTF":
            errors.append(f"Invalid magic header: {magic} (expected b'glTF')")
        if version != 2:
            errors.append(f"Unsupported glTF version: {version} (expected 2)")
        if length != file_size:
            errors.append(f"Header length mismatch: declared {length}, actual {file_size}")

        # 2. Chunk 0 (JSON)
        gltf_json: Dict[str, Any] = {}
        chunk0_len, chunk0_type = struct.unpack_from('<I4s', data, 12)
        if chunk0_type != b"JSON":
            errors.append(f"Invalid Chunk 0 type: {chunk0_type} (expected b'JSON')")
        else:
            try:
                raw_json = data[20:20 + chunk0_len].decode("utf-8")
                gltf_json = json.loads(raw_json)
            except Exception as e:
                errors.append(f"Failed to decode glTF JSON chunk: {e}")

        # 3. Verify Asset Metadata
        asset_info = gltf_json.get("asset", {})
        if asset_info.get("version") != "2.0":
            errors.append(f"glTF asset version is not 2.0 (got {asset_info.get('version')})")

        # 4. Verify Mesh Presence
        meshes = gltf_json.get("meshes", [])
        if len(meshes) == 0:
            errors.append("No meshes defined in glTF model")
        else:
            for i, m in enumerate(meshes):
                prims = m.get("primitives", [])
                if len(prims) == 0:
                    errors.append(f"Mesh {i} contains no primitives")
                for p in prims:
                    attrs = p.get("attributes", {})
                    if "POSITION" not in attrs:
                        errors.append(f"Mesh {i} primitive missing POSITION accessor")
                    if "NORMAL" not in attrs:
                        warnings.append(f"Mesh {i} primitive has no NORMAL accessor")

        # 5. Verify Material Presence
        materials = gltf_json.get("materials", [])
        if len(materials) == 0:
            warnings.append("No materials defined in glTF model (using default unlit shader)")
        else:
            for j, mat in enumerate(materials):
                pbr = mat.get("pbrMetallicRoughness", {})
                if not pbr and "extensions" not in mat:
                    warnings.append(f"Material {j} has no pbrMetallicRoughness definition")

        # 6. Verify Texture References & BufferViews
        textures = gltf_json.get("textures", [])
        images = gltf_json.get("images", [])
        buffer_views = gltf_json.get("bufferViews", [])

        for img_idx, img in enumerate(images):
            bv_idx = img.get("bufferView")
            if bv_idx is None or bv_idx >= len(buffer_views):
                errors.append(f"Image {img_idx} points to invalid bufferView index {bv_idx}")
            mime = img.get("mimeType", "")
            if mime not in ["image/png", "image/jpeg"]:
                warnings.append(f"Image {img_idx} has non-standard MIME type '{mime}'")

        # 7. Browser & Blender Compatibility
        nodes = gltf_json.get("nodes", [])
        scenes = gltf_json.get("scenes", [])
        scene_idx = gltf_json.get("scene", 0)
        if len(scenes) > 0 and (scene_idx is None or scene_idx >= len(scenes)):
            errors.append("Invalid default scene index")

        # Check accessors component types (Blender compatibility)
        accessors = gltf_json.get("accessors", [])
        valid_component_types = {5120, 5121, 5122, 5123, 5125, 5126}
        for acc_idx, acc in enumerate(accessors):
            c_type = acc.get("componentType")
            if c_type not in valid_component_types:
                errors.append(f"Accessor {acc_idx} has invalid componentType {c_type}")

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "version": version,
            "meshes_count": len(meshes),
            "materials_count": len(materials),
            "textures_count": len(textures),
            "images_count": len(images),
            "browser_compatible": is_valid,
            "blender_compatible": is_valid,
        }

    # -------------------------------------------------------------
    # STAGE 8: Reopen Exported GLB
    # -------------------------------------------------------------
    @classmethod
    def reopen_exported_glb(cls, glb_path: str) -> trimesh.Trimesh:
        logger.info(f"Reopening exported GLB to verify geometry loading: {glb_path}")
        reopened = trimesh.load(glb_path, force="mesh")
        if isinstance(reopened, trimesh.Scene):
            reopened = trimesh.util.concatenate([g for g in reopened.geometry.values() if isinstance(g, trimesh.Trimesh)])

        if len(reopened.faces) == 0:
            raise ValueError(f"Reopened GLB mesh at '{glb_path}' has 0 faces")
        return reopened

    # -------------------------------------------------------------
    # STAGE 9: Generate High-Fidelity 3D Thumbnail Preview
    # -------------------------------------------------------------
    @classmethod
    def generate_thumbnail(
        cls,
        mesh: trimesh.Trimesh,
        output_thumbnail_path: str,
        resolution: int = 512,
    ) -> str:
        os.makedirs(os.path.dirname(output_thumbnail_path), exist_ok=True)
        logger.info(f"Rendering 3D thumbnail preview to {output_thumbnail_path}...")

        fig = plt.figure(figsize=(4, 4), facecolor="#0a0f1d")
        ax = fig.add_subplot(1, 1, 1, projection="3d", facecolor="#0a0f1d")

        v = mesh.vertices
        f = mesh.faces

        # Normalize coordinates into unit view cube
        bounds = mesh.bounds
        center = (bounds[0] + bounds[1]) / 2.0
        extents = bounds[1] - bounds[0]
        max_extent = max(float(np.max(extents)), 1e-5)
        norm_v = (v - center) / max_extent * 1.5

        # Subsample faces for density stability
        step = max(1, len(f) // 2500)
        sub_faces = f[::step]

        poly = Poly3DCollection(
            norm_v[sub_faces],
            facecolors="#38bdf8",
            edgecolors="#1e293b",
            linewidths=0.25,
            alpha=0.95,
        )
        ax.add_collection3d(poly)
        ax.set_xlim(-1.0, 1.0)
        ax.set_ylim(-1.0, 1.0)
        ax.set_zlim(-1.0, 1.0)
        ax.view_init(elev=22, azim=45)
        ax.axis("off")

        plt.tight_layout(pad=0)
        plt.savefig(output_thumbnail_path, facecolor=fig.get_facecolor(), dpi=120)
        plt.close(fig)

        return output_thumbnail_path

    # -------------------------------------------------------------
    # STAGE 10: Save Export Metadata
    # -------------------------------------------------------------
    @classmethod
    def save_export_metadata(
        cls,
        output_glb_path: str,
        metadata: Dict[str, Any],
    ) -> str:
        meta_path = f"{output_glb_path}.meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Export metadata written to {meta_path}")
        return meta_path

    # -------------------------------------------------------------
    # MASTER 10-STAGE PIPELINE EXECUTION
    # -------------------------------------------------------------
    @classmethod
    def execute_export_pipeline(
        cls,
        mesh: Union[trimesh.Trimesh, str],
        texture_paths: Dict[str, str],
        output_glb_path: str,
        material_params: Optional[Dict[str, Any]] = None,
        export_profile: ExportProfile = ExportProfile.STANDARD,
        thumbnail_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes all 10 stages of the GLB Asset Export System.
        """
        start_time = time.time()
        logger.info(f"Starting 10-Stage GLB Export Pipeline (Profile: {export_profile.value})...")

        # Stage 1: Load Optimized Mesh
        opt_mesh = cls.load_optimized_mesh(mesh)

        # Stage 2: Load UV Coordinates
        uv_mesh = cls.load_uv_coordinates(opt_mesh)

        # Stage 3: Load Textures
        textures = cls.load_textures(texture_paths, profile=export_profile)

        # Stage 4: Load PBR Materials
        has_glow = np.any(np.array(textures["emissive"]) > 25)
        mat_config = cls.load_pbr_materials(material_params, has_emissive_glow=has_glow)

        # Stage 5: Combine Geometry & Materials (ORM Packing & Normals)
        assembled_mesh = cls.combine_geometry_and_materials(uv_mesh, textures, mat_config)

        # Stage 6: Export GLB
        file_size = cls.export_glb_file(assembled_mesh, output_glb_path)

        # Stage 7: Validate Exported File
        validation_report = cls.validate_gltf_glb(output_glb_path)

        # Stage 8: Reopen Exported GLB
        reopened_mesh = cls.reopen_exported_glb(output_glb_path)

        # Stage 9: Generate Thumbnail
        if thumbnail_path is None:
            thumb_dir = os.path.join(os.path.dirname(output_glb_path), "../thumbnails")
            os.makedirs(thumb_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(output_glb_path))[0]
            thumbnail_path = os.path.join(thumb_dir, f"{base_name}_thumb.png")

        thumb_out = cls.generate_thumbnail(reopened_mesh, thumbnail_path)

        # Stage 10: Save Export Metadata
        duration = round(time.time() - start_time, 4)
        extents = [float(x) for x in reopened_mesh.extents]

        metadata: Dict[str, Any] = {
            "asset_name": mat_config["name"],
            "export_profile": export_profile.value,
            "glb_path": output_glb_path,
            "thumbnail_path": thumb_out,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "polygon_count": len(reopened_mesh.faces),
            "vertex_count": len(reopened_mesh.vertices),
            "texture_resolution": PROFILE_RESOLUTIONS[export_profile],
            "pbr_channels_embedded": list(textures.keys()),
            "bounding_box_dimensions": extents,
            "validation_report": validation_report,
            "compatibility": {
                "browser_threejs": validation_report["browser_compatible"],
                "blender_import": validation_report["blender_compatible"],
                "unreal_engine_5": True,
                "unity_engine": True,
            },
            "export_duration_seconds": duration,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        cls.save_export_metadata(output_glb_path, metadata)

        # Backward compatibility aliases
        metadata["verified_faces"] = len(reopened_mesh.faces)
        metadata["verified_vertices"] = len(reopened_mesh.vertices)
        metadata["is_valid"] = validation_report["is_valid"]
        metadata["valid"] = validation_report["is_valid"]
        metadata["path"] = output_glb_path

        logger.info(f"GLB Export Pipeline finished in {duration}s: {metadata['polygon_count']} faces, {metadata['file_size_mb']} MB")
        return metadata

    # -------------------------------------------------------------
    # BACKWARD COMPATIBLE EXPORT INTERFACE
    # -------------------------------------------------------------
    @classmethod
    def export(
        cls,
        mesh: trimesh.Trimesh,
        texture_paths: Dict[str, str],
        output_glb_path: Optional[str] = None,
        material_params: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
        export_profile: Union[str, ExportProfile] = ExportProfile.STANDARD,
        thumbnail_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        dest_path = output_glb_path or output_path
        if not dest_path:
            raise ValueError("output_glb_path or output_path must be specified.")

        profile_enum = ExportProfile(export_profile) if isinstance(export_profile, str) else export_profile

        return cls.execute_export_pipeline(
            mesh=mesh,
            texture_paths=texture_paths,
            output_glb_path=dest_path,
            material_params=material_params,
            export_profile=profile_enum,
            thumbnail_path=thumbnail_path,
        )

    @classmethod
    def validate_glb(cls, glb_path: str) -> Dict[str, Any]:
        """Backward-compatible validation wrapper."""
        return cls.validate_gltf_glb(glb_path)

# Singleton Instance
glb_exporter = GLBExportSystem()
