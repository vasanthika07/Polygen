"""
PolyGen Multimodal Analyzer
Analyzes images, sketches, audio prompts, and combined text+vision inputs
to extract geometric silhouettes, depth approximations, color palettes, and material characteristics.
"""

import os
import io
import re
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

class MultimodalAnalyzer:
    """
    Multimodal Vision & Audio Analyzer for PolyGen 3D Synthesis.
    Extracts geometric cues, contour silhouettes, color palettes, and surface material attributes.
    """

    @classmethod
    def load_image(cls, image_input: Union[str, bytes, Image.Image]) -> Image.Image:
        """Loads and normalizes image input from path, raw bytes, or base64 data URI."""
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGBA")

        if isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input)).convert("RGBA")

        if isinstance(image_input, str):
            # Check for base64 data URI
            if image_input.startswith("data:image"):
                header, encoded = image_input.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            elif os.path.exists(image_input):
                return Image.open(image_input).convert("RGBA")
            else:
                # Might be raw base64 without prefix
                try:
                    img_bytes = base64.b64decode(image_input)
                    return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                except Exception:
                    raise FileNotFoundError(f"Image not found at path: {image_input}")

        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    @classmethod
    def extract_visual_features(cls, image: Image.Image) -> Dict[str, Any]:
        """
        Extracts comprehensive geometric, colorimetric, and material cues from 2D reference images:
        - Foreground contour & bounding box aspect ratio
        - Color palette (primary, secondary, accent)
        - Estimated surface roughness & metallic reflectance
        - Luminance-derived depth / height displacement map
        """
        # Resize to standard analysis resolution (256x256)
        thumb = image.resize((256, 256), Image.Resampling.LANCZOS)
        rgba_np = np.array(thumb, dtype=np.float32) / 255.0
        rgb = rgba_np[:, :, :3]
        alpha = rgba_np[:, :, 3] if rgba_np.shape[2] == 4 else np.ones((256, 256), dtype=np.float32)

        # 1. Foreground silhouette mask
        # If alpha has transparency, use it; otherwise infer foreground by contrast from corner pixels
        if np.any(alpha < 0.95):
            mask = alpha > 0.2
        else:
            # Estimate background from edge/corner luminance
            corner_sample = np.mean([rgb[:10, :10], rgb[:10, -10:], rgb[-10:, :10], rgb[-10:, -10:]], axis=(0, 1, 2))
            diff_from_bg = np.linalg.norm(rgb - corner_sample, axis=-1)
            threshold = max(0.08, float(np.mean(diff_from_bg) * 0.7))
            mask = diff_from_bg > threshold

        # If mask is empty or completely full, relax
        if not np.any(mask) or np.all(mask):
            mask = np.ones((256, 256), dtype=bool)

        # Bounding aspect ratio
        y_indices, x_indices = np.where(mask)
        if len(y_indices) > 0 and len(x_indices) > 0:
            h = np.max(y_indices) - np.min(y_indices) + 1
            w = np.max(x_indices) - np.min(x_indices) + 1
            aspect_ratio = float(w / max(1, h))
        else:
            aspect_ratio = 1.0

        # 2. Color Palette & Histogram Extraction
        fg_pixels = rgb[mask]
        if len(fg_pixels) == 0:
            fg_pixels = rgb.reshape(-1, 3)

        mean_color = np.mean(fg_pixels, axis=0)
        std_color = np.std(fg_pixels, axis=0)

        # Simple 3-tier dominant color quantization
        # Partition foreground pixels by luminance
        luminance = 0.299 * fg_pixels[:, 0] + 0.587 * fg_pixels[:, 1] + 0.114 * fg_pixels[:, 2]
        sorted_indices = np.argsort(luminance)
        n = len(sorted_indices)
        dark_part = fg_pixels[sorted_indices[: max(1, n // 3)]]
        mid_part = fg_pixels[sorted_indices[n // 3 : max(2, 2 * n // 3)]]
        bright_part = fg_pixels[sorted_indices[2 * n // 3 :]]

        dominant_rgb = np.mean(mid_part, axis=0) if len(mid_part) > 0 else mean_color
        shadow_rgb = np.mean(dark_part, axis=0) if len(dark_part) > 0 else mean_color * 0.5
        highlight_rgb = np.mean(bright_part, axis=0) if len(bright_part) > 0 else mean_color * 1.5

        def to_hex(c):
            clamped = np.clip(c * 255.0, 0, 255).astype(int)
            return f"#{clamped[0]:02x}{clamped[1]:02x}{clamped[2]:02x}"

        # 3. Material Characteristics Inference
        # High specular ratio and high contrast indicates metallic or crystal
        lum_max = np.max(luminance)
        lum_min = np.min(luminance)
        dynamic_range = float(lum_max - lum_min)
        color_variance = float(np.mean(std_color))

        # Detect high saturation/emission
        max_channel_diff = float(np.max(np.abs(dominant_rgb - np.mean(dominant_rgb))))
        is_saturated = max_channel_diff > 0.18

        # Classify inferred material from vision
        inferred_material = "dielectric_standard"
        inferred_class = "prop"
        roughness_est = 0.5
        metallic_est = 0.0

        # Blue/Cyan high saturation -> glowing sapphire or crystal
        if dominant_rgb[2] > dominant_rgb[0] * 1.3 and dominant_rgb[2] > 0.4:
            inferred_material = "glowing_sapphire"
            inferred_class = "crystal"
            roughness_est = 0.15
            metallic_est = 0.05
        # Warm brown / amber -> wood or leather
        elif dominant_rgb[0] > dominant_rgb[2] * 1.5 and dominant_rgb[1] > dominant_rgb[2] * 1.1:
            if dominant_rgb[0] > 0.6 and dominant_rgb[1] > 0.5:
                inferred_material = "polished_gold"
                inferred_class = "metallic"
                roughness_est = 0.25
                metallic_est = 0.85
            else:
                inferred_material = "carved_wood"
                inferred_class = "organic_prop"
                roughness_est = 0.72
                metallic_est = 0.0
        # Neutral grey with high dynamic range -> rusted metal or steel
        elif color_variance < 0.08 and dynamic_range > 0.5:
            if dominant_rgb[0] > dominant_rgb[2] * 1.15: # Reddish rust tinge
                inferred_material = "rusted_sword"
                inferred_class = "weapon_or_metal"
                roughness_est = 0.68
                metallic_est = 0.8
            else:
                inferred_material = "granite_stone"
                inferred_class = "architecture_stone"
                roughness_est = 0.85
                metallic_est = 0.0
        else:
            inferred_material = "granite_stone"
            inferred_class = "prop"
            roughness_est = 0.6
            metallic_est = 0.1

        # 4. Synthesize height / depth displacement map
        gray = image.convert("L").resize((128, 128), Image.Resampling.BILINEAR)
        # Apply smooth Gaussian blur
        smoothed = gray.filter(ImageFilter.GaussianBlur(radius=1.5))
        depth_np = np.array(smoothed, dtype=np.float32) / 255.0

        return {
            "aspect_ratio": round(aspect_ratio, 3),
            "dominant_color_hex": to_hex(dominant_rgb),
            "dominant_color_rgb": dominant_rgb.tolist(),
            "shadow_color_hex": to_hex(shadow_rgb),
            "highlight_color_hex": to_hex(highlight_rgb),
            "inferred_material": inferred_material,
            "inferred_class": inferred_class,
            "estimated_roughness": round(roughness_est, 2),
            "estimated_metallic": round(metallic_est, 2),
            "dynamic_range": round(dynamic_range, 3),
            "color_variance": round(color_variance, 3),
            "depth_map": depth_np,
            "mask": mask,
        }

    @classmethod
    def fuse_multimodal_prompt(
        cls,
        text_prompt: Optional[str] = None,
        image_input: Optional[Union[str, bytes, Image.Image]] = None,
        audio_transcript: Optional[str] = None,
        style_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fuses multimodal modalities (Text, Image conditioning, and Voice transcript)
        into a unified, structured generation specification.
        """
        combined_text = ""
        if text_prompt and text_prompt.strip():
            combined_text += text_prompt.strip()

        if audio_transcript and audio_transcript.strip():
            if combined_text:
                combined_text += f", {audio_transcript.strip()}"
            else:
                combined_text = audio_transcript.strip()

        visual_features = None
        analyzed_image = None
        if image_input is not None:
            analyzed_image = cls.load_image(image_input)
            visual_features = cls.extract_visual_features(analyzed_image)

        # If no text provided, generate descriptive text from image features
        if not combined_text and visual_features:
            mat = visual_features["inferred_material"].replace("_", " ")
            combined_text = f"A {mat} 3D asset matching reference image proportions"

        # Determine target style
        resolved_style = style_override or "realistic"
        if visual_features and visual_features["estimated_metallic"] > 0.5:
            resolved_style = "metallic" if not style_override else style_override
        elif visual_features and visual_features["inferred_material"] == "glowing_sapphire":
            resolved_style = "fantasy" if not style_override else style_override

        return {
            "fused_prompt": combined_text,
            "raw_text": text_prompt,
            "audio_transcript": audio_transcript,
            "has_image": image_input is not None,
            "visual_features": visual_features,
            "resolved_style": resolved_style,
            "inferred_material": visual_features["inferred_material"] if visual_features else "granite_stone",
        }

multimodal_analyzer = MultimodalAnalyzer()
