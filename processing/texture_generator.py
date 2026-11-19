import os
import math
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict, Any, Tuple, Union, Optional, List

logger = logging.getLogger(__name__)

class TextureGeneratorService:
    """
    Module 3 & Part 9: AI Texture Generation Service
    Generates realistic, physically based PBR texture maps corresponding directly
    to geometry and natural-language material descriptions:
    - Base Color (Albedo, sRGB)
    - Roughness (Linear grayscale)
    - Metallic (Linear grayscale)
    - Normal (Tangent space RGB)
    - Ambient Occlusion (Linear grayscale cavity occlusion)
    - Emissive (sRGB self-illumination)
    - Packed ORM (R=AO, G=Roughness, B=Metallic)
    """

    SUPPORTED_MATERIALS = [
        "wood",
        "rusted_metal",
        "stone",
        "glass",
        "glowing_sapphire",
    ]

    @classmethod
    def extract_material_spec(cls, prompt_input: Any) -> Dict[str, Any]:
        """
        Stage 2: Extracts structured material descriptions and physical PBR parameters
        from StructuredPrompt, dictionary, or natural-language prompt string.
        """
        raw_text = ""
        material_str = ""
        details = []
        style = "photorealistic"

        if hasattr(prompt_input, "raw_prompt"):
            raw_text = getattr(prompt_input, "raw_prompt", "")
            material_str = getattr(prompt_input, "material", "")
            details = getattr(prompt_input, "details", [])
            style = getattr(prompt_input, "style", "photorealistic")
        elif isinstance(prompt_input, dict):
            raw_text = prompt_input.get("raw_prompt", prompt_input.get("prompt", ""))
            material_str = prompt_input.get("material", prompt_input.get("object", ""))
            details = prompt_input.get("details", prompt_input.get("materials", []))
            style = prompt_input.get("style", "photorealistic")
        elif isinstance(prompt_input, str):
            raw_text = prompt_input
            material_str = prompt_input

        full_query = f"{raw_text} {material_str} {' '.join(details)}".lower()

        # Classify primary material category
        if "sapphire" in full_query or "crystal" in full_query or "gem" in full_query:
            mat_type = "glowing_sapphire"
        elif "glass" in full_query or "translucent" in full_query or "transparent" in full_query:
            mat_type = "glass"
        elif "rust" in full_query or "weathered metal" in full_query or "corroded" in full_query:
            mat_type = "rusted_metal"
        elif "wood" in full_query or "oak" in full_query or "pine" in full_query or "mahogany" in full_query:
            mat_type = "wood"
        elif "stone" in full_query or "rock" in full_query or "granite" in full_query or "marble" in full_query or "sculpture" in full_query:
            mat_type = "stone"
        elif "metal" in full_query or "steel" in full_query or "iron" in full_query or "robot" in full_query:
            mat_type = "rusted_metal" if "rust" in full_query else "metal"
        else:
            mat_type = "stone"

        # Check for radiant/emissive accents
        has_emissive = any(k in full_query for k in [
            "glowing", "glow", "sapphire", "ruby", "emerald", "neon", "energy", "emissive", "magic", "luminescent"
        ])

        return {
            "material_type": mat_type,
            "style": style,
            "has_emissive": has_emissive,
            "details": details,
            "raw_query": full_query,
        }

    @classmethod
    def generate_textures(
        cls,
        material_spec: Dict[str, Any],
        resolution: int = 1024,
        seed: int = 42,
    ) -> Dict[str, Image.Image]:
        """
        Stage 3: Synthesizes a synchronized 6-channel PBR map set based on the material specification.
        """
        res = resolution
        mat = material_spec.get("material_type", "wood")
        has_emissive = material_spec.get("has_emissive", False)

        np.random.seed(seed)

        if mat == "wood":
            maps = cls._synthesize_wood(res)
        elif mat in ["rusted_metal", "metal"]:
            maps = cls._synthesize_rusted_metal(res, is_heavily_rusted="rust" in material_spec.get("raw_query", ""))
        elif mat == "stone":
            maps = cls._synthesize_stone(res)
        elif mat == "glass":
            maps = cls._synthesize_glass(res)
        elif mat == "glowing_sapphire":
            maps = cls._synthesize_glowing_sapphire(res)
        else:
            maps = cls._synthesize_stone(res)

        # Emissive map handling
        if not has_emissive and mat != "glowing_sapphire":
            maps["emissive"] = Image.new("RGB", (res, res), (0, 0, 0))

        # Pack standard ORM texture: R=AmbientOcclusion, G=Roughness, B=Metallic
        ao_arr = np.array(maps["ambient_occlusion"])
        r_arr = np.array(maps["roughness"])
        m_arr = np.array(maps["metallic"])

        orm_arr = np.stack([ao_arr, r_arr, m_arr], axis=-1)
        maps["orm"] = Image.fromarray(orm_arr, mode="RGB")

        return maps

    # -------------------------------------------------------------
    # 1. WOOD MATERIAL SYNTHESIS
    # -------------------------------------------------------------
    @classmethod
    def _synthesize_wood(cls, res: int) -> Dict[str, Image.Image]:
        """Oak/walnut fibrous grain with growth rings, zero metallic, medium-high roughness."""
        y = np.linspace(0, 10 * np.pi, res)
        x = np.linspace(0, 2 * np.pi, res)
        X, Y = np.meshgrid(x, y)

        # Multi-octave organic grain noise
        noise = np.random.normal(0, 0.15, (res, res))
        grain = np.sin(Y * 2.5 + np.sin(X * 1.5) * 2.0 + noise * 1.5)
        grain = (grain - grain.min()) / (grain.max() - grain.min())

        # BaseColor (Albedo)
        dark_wood = np.array([85, 52, 30], dtype=np.float32)
        light_wood = np.array([145, 98, 60], dtype=np.float32)
        albedo_arr = dark_wood + (light_wood - dark_wood) * grain[:, :, None]
        albedo_arr = np.clip(albedo_arr + np.random.normal(0, 4, albedo_arr.shape), 0, 255).astype(np.uint8)
        basecolor_img = Image.fromarray(albedo_arr, mode="RGB").filter(ImageFilter.GaussianBlur(0.8))

        # Roughness: 0.65 - 0.78 (dry organic timber)
        rough_arr = 165 + (grain * 35) + np.random.normal(0, 6, (res, res))
        rough_arr = np.clip(rough_arr, 140, 210).astype(np.uint8)
        roughness_img = Image.fromarray(rough_arr, mode="L").filter(ImageFilter.GaussianBlur(1.0))

        # Metallic: 0.0 (dielectric)
        metallic_img = Image.new("L", (res, res), 0)

        # Tangent-Space Normal Map: Grain ridges
        normal_img = cls._height_to_normal(grain * 0.4, res, strength=2.5)

        # Ambient Occlusion: Grain pores and plank boundaries
        ao_arr = 255 - (grain * 30).astype(np.uint8)
        ao_img = Image.fromarray(ao_arr, mode="L").filter(ImageFilter.GaussianBlur(1.5))

        # Emissive: Black
        emissive_img = Image.new("RGB", (res, res), (0, 0, 0))

        return {
            "basecolor": basecolor_img,
            "roughness": roughness_img,
            "metallic": metallic_img,
            "normal": normal_img,
            "ambient_occlusion": ao_img,
            "emissive": emissive_img,
        }

    # -------------------------------------------------------------
    # 2. RUSTED METAL MATERIAL SYNTHESIS
    # -------------------------------------------------------------
    @classmethod
    def _synthesize_rusted_metal(cls, res: int, is_heavily_rusted: bool = True) -> Dict[str, Image.Image]:
        """Gunmetal steel core with cellular iron-oxide rust patches."""
        # Multi-scale cellular noise for rust clustering
        n1 = np.random.normal(0.5, 0.2, (res // 8, res // 8))
        n1_up = np.array(Image.fromarray((n1 * 255).astype(np.uint8)).resize((res, res), Image.Resampling.BILINEAR)) / 255.0
        n2 = np.random.normal(0.5, 0.2, (res // 32, res // 32))
        n2_up = np.array(Image.fromarray((n2 * 255).astype(np.uint8)).resize((res, res), Image.Resampling.BICUBIC)) / 255.0

        rust_mask = np.clip(n1_up * 0.5 + n2_up * 0.7 - 0.2, 0.0, 1.0)
        rust_threshold = 0.45 if is_heavily_rusted else 0.65
        rust_binary = (rust_mask > rust_threshold).astype(np.float32)

        # BaseColor: Steel (165, 170, 178) vs Rust (138, 52, 24)
        steel_color = np.array([168, 172, 180], dtype=np.float32)
        rust_color = np.array([135, 50, 22], dtype=np.float32)
        rust_dark = np.array([85, 32, 14], dtype=np.float32)

        # Blend
        rust_full = rust_dark + (rust_color - rust_dark) * rust_mask[:, :, None]
        albedo_arr = steel_color * (1.0 - rust_binary[:, :, None]) + rust_full * rust_binary[:, :, None]
        albedo_arr = np.clip(albedo_arr + np.random.normal(0, 5, albedo_arr.shape), 0, 255).astype(np.uint8)
        basecolor_img = Image.fromarray(albedo_arr, mode="RGB").filter(ImageFilter.GaussianBlur(0.6))

        # Roughness: Steel is 0.28 (~70), Rust is 0.88 (~225)
        rough_arr = 70 * (1.0 - rust_binary) + (220 + np.random.normal(0, 10, (res, res))) * rust_binary
        rough_arr = np.clip(rough_arr, 40, 250).astype(np.uint8)
        roughness_img = Image.fromarray(rough_arr, mode="L").filter(ImageFilter.GaussianBlur(1.0))

        # Metallic: Steel is 1.0 (255), Rust is 0.1 (25)
        metal_arr = 250 * (1.0 - rust_binary) + 25 * rust_binary
        metal_arr = np.clip(metal_arr, 0, 255).astype(np.uint8)
        metallic_img = Image.fromarray(metal_arr, mode="L").filter(ImageFilter.GaussianBlur(0.8))

        # Tangent Normal: Pitted surface in rust regions
        pitting = (rust_binary * (np.random.normal(0.5, 0.3, (res, res))))
        normal_img = cls._height_to_normal(pitting, res, strength=3.5)

        # Ambient Occlusion: Cavity occlusion inside rust pits
        ao_arr = 255 - (rust_binary * 55).astype(np.uint8)
        ao_img = Image.fromarray(ao_arr, mode="L").filter(ImageFilter.GaussianBlur(1.5))

        emissive_img = Image.new("RGB", (res, res), (0, 0, 0))

        return {
            "basecolor": basecolor_img,
            "roughness": roughness_img,
            "metallic": metallic_img,
            "normal": normal_img,
            "ambient_occlusion": ao_img,
            "emissive": emissive_img,
        }

    # -------------------------------------------------------------
    # 3. STONE MATERIAL SYNTHESIS
    # -------------------------------------------------------------
    @classmethod
    def _synthesize_stone(cls, res: int) -> Dict[str, Image.Image]:
        """Granite/slate rock with quartz flecks, high roughness, zero metallic."""
        noise_coarse = np.random.normal(0.5, 0.18, (res // 16, res // 16))
        coarse_up = np.array(Image.fromarray((noise_coarse * 255).astype(np.uint8)).resize((res, res), Image.Resampling.BICUBIC)) / 255.0
        fine_noise = np.random.normal(0, 0.08, (res, res))
        stone_h = np.clip(coarse_up + fine_noise, 0.0, 1.0)

        # BaseColor: Granite gray (125, 128, 132) + dark biotite mica (50, 52, 55) + quartz (185, 188, 192)
        base_gray = np.array([125, 128, 132], dtype=np.float32)
        albedo_arr = base_gray + (stone_h[:, :, None] - 0.5) * 80.0

        # Mica specks
        specks = (np.random.uniform(0, 1, (res, res)) > 0.985).astype(np.float32)
        albedo_arr = albedo_arr * (1.0 - specks[:, :, None]) + np.array([45, 48, 50]) * specks[:, :, None]
        albedo_arr = np.clip(albedo_arr, 0, 255).astype(np.uint8)
        basecolor_img = Image.fromarray(albedo_arr, mode="RGB").filter(ImageFilter.GaussianBlur(0.7))

        # Roughness: 0.85 (~215)
        rough_arr = np.clip(215 + (stone_h - 0.5) * 30 + np.random.normal(0, 8, (res, res)), 180, 245).astype(np.uint8)
        roughness_img = Image.fromarray(rough_arr, mode="L").filter(ImageFilter.GaussianBlur(1.2))

        # Metallic: 0.0 (dielectric rock)
        metallic_img = Image.new("L", (res, res), 0)

        # Tangent Normal: Rocky chiseled relief
        normal_img = cls._height_to_normal(stone_h, res, strength=3.0)

        # Ambient Occlusion: Deep cracks and crevices
        ao_arr = np.clip(255 - (1.0 - stone_h) * 70, 150, 255).astype(np.uint8)
        ao_img = Image.fromarray(ao_arr, mode="L").filter(ImageFilter.GaussianBlur(1.8))

        emissive_img = Image.new("RGB", (res, res), (0, 0, 0))

        return {
            "basecolor": basecolor_img,
            "roughness": roughness_img,
            "metallic": metallic_img,
            "normal": normal_img,
            "ambient_occlusion": ao_img,
            "emissive": emissive_img,
        }

    # -------------------------------------------------------------
    # 4. GLASS-LIKE MATERIAL SYNTHESIS
    # -------------------------------------------------------------
    @classmethod
    def _synthesize_glass(cls, res: int) -> Dict[str, Image.Image]:
        """Translucent silicate glass with specular reflection, near-zero roughness."""
        # BaseColor: Clear pale ice-cyan tint
        glass_tint = np.full((res, res, 3), [225, 242, 250], dtype=np.uint8)
        basecolor_img = Image.fromarray(glass_tint, mode="RGB")

        # Roughness: 0.05 (~12) mirror smooth
        rough_arr = np.full((res, res), 12, dtype=np.uint8)
        roughness_img = Image.fromarray(rough_arr, mode="L")

        # Metallic: 0.0 (dielectric)
        metallic_img = Image.new("L", (res, res), 0)

        # Normal: Flat pristine surface normal (128, 128, 255)
        normal_arr = np.full((res, res, 3), [128, 128, 255], dtype=np.uint8)
        normal_img = Image.fromarray(normal_arr, mode="RGB")

        # Ambient Occlusion: Unoccluded (255)
        ao_img = Image.new("L", (res, res), 255)

        emissive_img = Image.new("RGB", (res, res), (0, 0, 0))

        return {
            "basecolor": basecolor_img,
            "roughness": roughness_img,
            "metallic": metallic_img,
            "normal": normal_img,
            "ambient_occlusion": ao_img,
            "emissive": emissive_img,
        }

    # -------------------------------------------------------------
    # 5. GLOWING SAPPHIRE MATERIAL SYNTHESIS
    # -------------------------------------------------------------
    @classmethod
    def _synthesize_glowing_sapphire(cls, res: int) -> Dict[str, Image.Image]:
        """Deep royal cobalt crystal with facets and radiant blue self-illumination."""
        # 1. BaseColor: Cobalt-sapphire blue with refractive facets
        cx, cy = res // 2, res // 2
        Y, X = np.ogrid[:res, :res]
        dist_from_center = np.sqrt((X - cx)**2 + (Y - cy)**2) / (res * 0.5)

        sapphire_deep = np.array([12, 55, 205], dtype=np.float32)
        sapphire_light = np.array([85, 175, 255], dtype=np.float32)

        facet_pattern = np.sin(X * 0.05) * np.cos(Y * 0.05)
        albedo_arr = sapphire_deep + (sapphire_light - sapphire_deep) * (np.clip(1.0 - dist_from_center + facet_pattern * 0.2, 0.0, 1.0))[:, :, None]
        albedo_arr = np.clip(albedo_arr, 0, 255).astype(np.uint8)
        basecolor_img = Image.fromarray(albedo_arr, mode="RGB").filter(ImageFilter.GaussianBlur(0.8))

        # Roughness: 0.12 (~30) glossy crystal polish
        rough_arr = np.clip(30 + np.random.normal(0, 4, (res, res)), 15, 60).astype(np.uint8)
        roughness_img = Image.fromarray(rough_arr, mode="L")

        # Metallic: 0.0 (dielectric gemstone)
        metallic_img = Image.new("L", (res, res), 0)

        # Normal: Gemstone facet bevels
        normal_img = cls._height_to_normal(facet_pattern * 0.5, res, strength=2.2)

        # Ambient Occlusion: Crisp facet corners (220 - 255)
        ao_arr = np.clip(240 - (facet_pattern * 15), 200, 255).astype(np.uint8)
        ao_img = Image.fromarray(ao_arr, mode="L")

        # Emissive: Radiant glowing azure-blue jewel core with white bloom
        emissive_arr = np.zeros((res, res, 3), dtype=np.float32)
        glow_radius = res * 0.35
        glow_mask = np.clip(1.0 - (dist_from_center / (glow_radius / (res * 0.5))), 0.0, 1.0)
        # Power falloff for radiant core
        glow_mask = glow_mask ** 2.2

        glow_blue = np.array([30, 140, 255], dtype=np.float32)
        white_core = np.array([230, 245, 255], dtype=np.float32)

        core_mask = np.clip(1.0 - (dist_from_center / 0.15), 0.0, 1.0) ** 3.0
        emissive_arr = (glow_blue * glow_mask[:, :, None]) + (white_core * core_mask[:, :, None])
        emissive_arr = np.clip(emissive_arr, 0, 255).astype(np.uint8)
        emissive_img = Image.fromarray(emissive_arr, mode="RGB").filter(ImageFilter.GaussianBlur(2.5))

        return {
            "basecolor": basecolor_img,
            "roughness": roughness_img,
            "metallic": metallic_img,
            "normal": normal_img,
            "ambient_occlusion": ao_img,
            "emissive": emissive_img,
        }

    # -------------------------------------------------------------
    # HELPER: TANGENT NORMAL COMPUTATION
    # -------------------------------------------------------------
    @staticmethod
    def _height_to_normal(height_arr: np.ndarray, res: int, strength: float = 2.0) -> Image.Image:
        """Derives mathematically exact tangent-space normal map from 2D height gradients."""
        h = height_arr.astype(np.float32)
        gx = np.zeros_like(h)
        gy = np.zeros_like(h)

        gx[:, 1:-1] = (h[:, 2:] - h[:, :-2]) * strength
        gy[1:-1, :] = (h[2:, :] - h[:-2, :]) * strength

        nx = -gx
        ny = -gy
        nz = np.ones_like(h)

        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        norm[norm == 0] = 1.0
        nx = ((nx / norm) * 0.5 + 0.5) * 255.0
        ny = ((ny / norm) * 0.5 + 0.5) * 255.0
        nz = ((nz / norm) * 0.5 + 0.5) * 255.0

        normal_arr = np.stack([nx, ny, nz], axis=-1).astype(np.uint8)
        return Image.fromarray(normal_arr, mode="RGB")

class TextureValidator:
    """Validates generated texture maps for resolution, channels, contrast, and validity."""

    @staticmethod
    def validate_texture_set(textures: Dict[str, Image.Image], expected_res: int) -> Dict[str, Any]:
        report = {"is_valid": True, "errors": [], "channels_verified": {}}

        required_channels = ["basecolor", "roughness", "metallic", "normal", "ambient_occlusion", "emissive"]
        for ch in required_channels:
            if ch not in textures:
                report["is_valid"] = False
                report["errors"].append(f"Missing required channel: {ch}")
                continue

            img = textures[ch]
            w, h = img.size
            if w != expected_res or h != expected_res:
                report["is_valid"] = False
                report["errors"].append(f"Channel {ch} resolution mismatch: expected {expected_res}x{expected_res}, got {w}x{h}")

            arr = np.array(img)
            var = float(np.var(arr))
            has_contrast = var > 0.0 or ch in ["metallic", "emissive", "ambient_occlusion"]

            report["channels_verified"][ch] = {
                "dimensions": [w, h],
                "mode": img.mode,
                "mean": round(float(np.mean(arr)), 2),
                "variance": round(var, 2),
                "has_valid_content": has_contrast,
            }

        return report

texture_generator_service = TextureGeneratorService()
texture_validator = TextureValidator()
