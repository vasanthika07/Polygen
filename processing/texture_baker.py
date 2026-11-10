import os
import math
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict, Any, Tuple
from app.schemas.job import StructuredPrompt

logger = logging.getLogger(__name__)

class PBRTextureBaker:
    """
    Modules 3 & 5: PBR Texture Synthesis Engine
    Generates physically based texture maps (BaseColor, Roughness, Metallic, Normal, Emissive)
    tailored to the prompt's material, style, and surface details.
    """

    @classmethod
    def generate_pbr_set(
        cls,
        prompt_data: StructuredPrompt,
        output_dir: str,
        resolution: int = 1024,
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        res = resolution

        logger.info(f"Generating PBR textures at {res}x{res} for '{prompt_data.object}'...")

        # Determine Material Palette
        mat = prompt_data.material.lower()
        details_str = " ".join(prompt_data.details).lower()
        has_emissive = any(k in details_str or k in prompt_data.raw_prompt.lower() 
                           for k in ["glowing", "glow", "sapphire", "ruby", "emerald", "neon", "energy"])

        # 1. BaseColor (Albedo) Map
        base_img = cls._synthesize_basecolor(mat, prompt_data.style, details_str, res)

        # 2. Roughness Map (0.0 = mirror smooth, 1.0 = completely diffuse)
        rough_img = cls._synthesize_roughness(mat, res)

        # 3. Metallic Map (0.0 = dielectric/non-metal, 1.0 = conductive metal)
        metal_img = cls._synthesize_metallic(mat, res)

        # 4. Tangent-Space Normal Map (RGB encoding X, Y, Z surface perturbations)
        normal_img = cls._synthesize_normal(base_img, res)

        # 5. Emissive Map (RGB self-illumination)
        emissive_img = cls._synthesize_emissive(details_str, prompt_data.raw_prompt, res, has_emissive)

        # Save all maps
        paths = {
            "basecolor": os.path.join(output_dir, "basecolor.png"),
            "roughness": os.path.join(output_dir, "roughness.png"),
            "metallic": os.path.join(output_dir, "metallic.png"),
            "normal": os.path.join(output_dir, "normal.png"),
            "emissive": os.path.join(output_dir, "emissive.png"),
        }

        base_img.save(paths["basecolor"], "PNG")
        rough_img.save(paths["roughness"], "PNG")
        metal_img.save(paths["metallic"], "PNG")
        normal_img.save(paths["normal"], "PNG")
        emissive_img.save(paths["emissive"], "PNG")

        logger.info(f"PBR texture set successfully saved to {output_dir}")
        return paths

    @staticmethod
    def _synthesize_basecolor(material: str, style: str, details: str, res: int) -> Image.Image:
        # Generate base albedo color based on material semantics
        if "iron" in material or "steel" in material:
            if "rust" in material or "weathered" in material:
                # Weathered / rusted iron: dark steel base with burnt sienna rust flecks
                base_color = (65, 68, 72)
                rust_color = (130, 52, 28)
            else:
                base_color = (180, 185, 190)
                rust_color = (100, 105, 110)
        elif "gold" in material:
            base_color = (235, 185, 50)
            rust_color = (195, 140, 30)
        elif "wood" in material:
            base_color = (110, 75, 45)
            rust_color = (75, 48, 28)
        elif "stone" in material:
            base_color = (120, 122, 125)
            rust_color = (85, 87, 90)
        else:
            base_color = (110, 115, 125)
            rust_color = (70, 75, 80)

        # Create procedural Perlin-style noise layer using numpy
        np.random.seed(42)
        noise = np.random.normal(0.5, 0.15, (res, res, 3))
        noise = np.clip(noise, 0.0, 1.0)

        base_arr = np.full((res, res, 3), base_color, dtype=np.float32)
        rust_arr = np.full((res, res, 3), rust_color, dtype=np.float32)

        # Procedural mask
        mask = np.random.uniform(0.0, 1.0, (res, res, 1))
        # Add smooth variation
        composite = base_arr * (1.0 - mask * 0.45) + rust_arr * (mask * 0.45)
        composite = np.clip(composite * (0.8 + 0.4 * noise), 0, 255).astype(np.uint8)

        img = Image.fromarray(composite, mode="RGB")
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))

        # Check for sapphire / gemstone accents
        if "sapphire" in details or "blue" in details:
            draw = ImageDraw.Draw(img)
            # Add decorative sapphire crystal accent in texture UV center-quarter
            cx, cy = int(res * 0.5), int(res * 0.3)
            r = int(res * 0.08)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(20, 90, 240))
            draw.ellipse([cx - r//2, cy - r//2, cx + r//2, cy + r//2], fill=(80, 160, 255))

        return img

    @staticmethod
    def _synthesize_roughness(material: str, res: int) -> Image.Image:
        # Metallic polished: 0.15, rusted iron: 0.65-0.85, wood: 0.7, stone: 0.85
        if "rust" in material:
            base_val = 190 # ~0.75 roughness
        elif "steel" in material or "metal" in material:
            base_val = 80  # ~0.3 roughness
        elif "wood" in material:
            base_val = 180
        elif "stone" in material:
            base_val = 210
        else:
            base_val = 128

        noise = np.random.normal(0, 25, (res, res)).astype(np.float32)
        arr = np.clip(base_val + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode="L").filter(ImageFilter.GaussianBlur(radius=1.5))
        return img

    @staticmethod
    def _synthesize_metallic(material: str, res: int) -> Image.Image:
        # Metal: 255, Rusted Metal: 160-220, Dielectric (wood/stone/plastic): 0
        if "gold" in material or "silver" in material:
            base_val = 250
        elif "rust" in material:
            base_val = 175 # Partially oxidized
        elif "iron" in material or "steel" in material or "metal" in material:
            base_val = 240
        else:
            base_val = 10 # Dielectric

        noise = np.random.normal(0, 15, (res, res)).astype(np.float32)
        arr = np.clip(base_val + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr, mode="L")
        return img

    @staticmethod
    def _synthesize_normal(base_img: Image.Image, res: int) -> Image.Image:
        # Sobel filter to derive tangent-space normal map from luminance height
        gray = np.array(base_img.convert("L"), dtype=np.float32) / 255.0
        
        # Sobel gradients
        gx = np.zeros_like(gray)
        gy = np.zeros_like(gray)
        
        gx[:, 1:-1] = (gray[:, 2:] - gray[:, :-2]) * 2.0
        gy[1:-1, :] = (gray[2:, :] - gray[:-2, :]) * 2.0
        
        # Normal vectors (nx, ny, nz)
        nx = -gx
        ny = -gy
        nz = np.ones_like(gray) * 0.5
        
        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        nx = (nx / norm * 0.5 + 0.5) * 255.0
        ny = (ny / norm * 0.5 + 0.5) * 255.0
        nz = (nz / norm * 0.5 + 0.5) * 255.0

        normal_arr = np.stack([nx, ny, nz], axis=-1).astype(np.uint8)
        return Image.fromarray(normal_arr, mode="RGB")

    @staticmethod
    def _synthesize_emissive(details: str, raw_prompt: str, res: int, has_emissive: bool) -> Image.Image:
        emissive_arr = np.zeros((res, res, 3), dtype=np.uint8)
        if not has_emissive:
            return Image.fromarray(emissive_arr, mode="RGB")

        # Determine emissive color
        lower = (details + " " + raw_prompt).lower()
        if "blue" in lower or "sapphire" in lower:
            glow_color = (30, 140, 255)
        elif "green" in lower or "emerald" in lower:
            glow_color = (40, 255, 80)
        elif "red" in lower or "ruby" in lower or "fire" in lower:
            glow_color = (255, 50, 30)
        else:
            glow_color = (0, 200, 255)

        img = Image.fromarray(emissive_arr, mode="RGB")
        draw = ImageDraw.Draw(img)

        # Draw glowing sapphire jewel in center
        cx, cy = int(res * 0.5), int(res * 0.3)
        r = int(res * 0.08)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=glow_color)
        draw.ellipse([cx - r//2, cy - r//2, cx + r//2, cy + r//2], fill=(255, 255, 255))

        # Add bloom blur
        img = img.filter(ImageFilter.GaussianBlur(radius=3.0))
        return img

texture_baker = PBRTextureBaker()

