import re
import logging
from typing import Dict, Any, List, Optional
from app.schemas.job import StructuredPrompt

logger = logging.getLogger(__name__)

class ModelPromptFormatter:
    """
    Transforms user prompts and structured prompt schemas into model-specific
    conditioning inputs optimized for Text-to-3D diffusion backends (Shap-E, etc.).
    """

    @classmethod
    def format_for_shape(cls, prompt_data: StructuredPrompt) -> Dict[str, Any]:
        """
        Formats structured prompt for OpenAI Shap-E text300M.
        Shap-E's CLIP ViT-L/14 encoder responds best to concise, object-centric
        phrases with style and salient visual descriptors.
        """
        obj = prompt_data.object.strip() if prompt_data.object else "3d object"
        style = prompt_data.style.strip() if prompt_data.style else "realistic"
        materials = prompt_data.material or []
        if isinstance(materials, str):
            materials = [materials]
        details = prompt_data.details or []
        if isinstance(details, str):
            details = [details]

        # Construct primary positive prompt
        components = [f"a 3D model of a {obj}"]
        if style and style.lower() not in ["none", "default"]:
            components.append(f"{style} style")
        if materials:
            components.append(f"made of {', '.join(materials[:2])}")
        if details:
            components.append(f"with {', '.join(details[:2])}")

        positive_prompt = ", ".join(components)

        # Token length sanity check (CLIP ViT-L/14 max 77 tokens)
        words = positive_prompt.split()
        if len(words) > 60:
            positive_prompt = " ".join(words[:60])

        # Negative prompt tokens
        negative_tokens = prompt_data.negative_prompt if hasattr(prompt_data, "negative_prompt") else []
        if not negative_tokens:
            negative_tokens = ["blurry", "degenerate", "flat plane", "floating disconnected parts", "inverted normals"]

        return {
            "model_target": "shap-e-text300M",
            "formatted_prompt": positive_prompt,
            "raw_prompt": prompt_data.raw_prompt,
            "object_entity": obj,
            "style_entity": style,
            "materials": materials,
            "negative_prompt": negative_tokens,
            "guidance_scale": 15.0,
            "karras_steps": 32,
        }

    @classmethod
    def format_for_hunyuan3d(cls, prompt_data: StructuredPrompt) -> Dict[str, Any]:
        """
        Formats prompt for Tencent Hunyuan3D pipeline (evaluative formatting).
        Hunyuan3D prefers detailed descriptive scene prompts with lighting and camera viewpoint.
        """
        obj = prompt_data.object or "asset"
        style = prompt_data.style or "photorealistic"
        formatted = f"A high resolution 3D asset of {obj}, {style} aesthetic, centered, 360 view, studio lighting, highly detailed surface texture."
        return {
            "model_target": "hunyuan3d",
            "formatted_prompt": formatted,
            "raw_prompt": prompt_data.raw_prompt,
            "viewpoints": ["front", "side", "top", "back"],
        }

prompt_formatter = ModelPromptFormatter()
