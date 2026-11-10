import re
from typing import Dict, Any, List
from app.schemas.job import StructuredPrompt

class PromptProcessingEngine:
    """
    Module 1: Prompt Processing Engine
    Parses unstructured natural language prompts, extracts semantic features,
    determines materials, textures, styles, surface details, and validates
    against 3D generation constraints.
    """

    KNOWN_STYLES = [
        "medieval fantasy", "fantasy", "sci-fi", "cyberpunk", "steampunk", 
        "realistic", "stylized", "low-poly", "gothic", "ancient", "modern", "industrial"
    ]

    KNOWN_MATERIALS = [
        "rusted iron", "weathered iron", "iron", "steel", "bronze", "brass", "copper",
        "gold", "silver", "wood", "oak", "stone", "marble", "granite", "leather",
        "cloth", "glass", "crystal", "obsidian", "plastic", "ceramic"
    ]

    KNOWN_TEXTURES = [
        "weathered metallic", "polished metal", "rusted metallic", "rough wood",
        "smooth stone", "chiseled stone", "glossy", "matte", "organic", "scratched",
        "carved", "patina", "corroded"
    ]

    SPECIAL_EMISSIVE_KEYWORDS = [
        "glowing", "glow", "luminescent", "neon", "illuminated", "radiant", "sapphire", "ruby", "emerald", "energy", "plasma", "fire"
    ]

    @classmethod
    def process(
        cls,
        raw_prompt: str,
        style_override: str = None,
        quality: str = "high",
        polygon_budget: int = 10000,
        target_format: str = "glb",
    ) -> StructuredPrompt:
        text = raw_prompt.strip()
        lower = text.lower()

        # 1. Validation
        if len(text) < 3:
            raise ValueError("Prompt must be at least 3 characters long.")
        if len(text) > 1000:
            raise ValueError("Prompt exceeds maximum length of 1000 characters.")

        # 2. Extract Style
        detected_style = style_override
        if not detected_style or detected_style.lower() == "auto":
            for s in cls.KNOWN_STYLES:
                if s in lower:
                    detected_style = s
                    break
        if not detected_style:
            # Fallback style heuristics
            if any(k in lower for k in ["medieval", "sword", "shield", "dragon", "castle", "magic"]):
                detected_style = "medieval fantasy"
            elif any(k in lower for k in ["cyber", "robot", "laser", "futuristic", "mech", "spacesuit"]):
                detected_style = "sci-fi"
            else:
                detected_style = "realistic"

        # 3. Extract Material
        detected_material = None
        for m in cls.KNOWN_MATERIALS:
            if m in lower:
                detected_material = m
                break
        if not detected_material:
            if "rust" in lower or "rusted" in lower:
                detected_material = "rusted iron"
            elif "steel" in lower:
                detected_material = "steel"
            elif "wood" in lower or "oak" in lower:
                detected_material = "weathered wood"
            elif "stone" in lower or "rock" in lower or "marble" in lower:
                detected_material = "carved stone"
            elif "gold" in lower or "golden" in lower:
                detected_material = "gold"
            elif "metal" in lower or "metallic" in lower:
                detected_material = "iron"
            else:
                detected_material = "iron"

        # 4. Extract Texture / Surface characteristics
        detected_texture = "weathered metallic" if "rust" in lower or "iron" in lower else "standard pbr"
        for t in cls.KNOWN_TEXTURES:
            if t in lower:
                detected_texture = t
                break

        # 5. Extract Details & Special Features
        details: List[str] = []
        for kw in cls.SPECIAL_EMISSIVE_KEYWORDS:
            if kw in lower:
                details.append(f"emissive: {kw}")

        # Extract features like "with a glowing blue sapphire in the hilt"
        with_match = re.search(r"with (?:a|an)?\s*([a-zA-Z\s]+?)(?:$|\.|\,)", text, re.IGNORECASE)
        if with_match:
            detail_phrase = with_match.group(1).strip()
            if detail_phrase and detail_phrase not in details:
                details.append(detail_phrase)

        # 6. Extract Main Object Concept
        # Remove common introductory words
        cleaned = re.sub(r"^(a|an|the)\s+", "", text, flags=re.IGNORECASE)
        # Strip "with ..." clause for core object name
        obj_match = re.split(r"\s+with\s+", cleaned, flags=re.IGNORECASE)[0].strip()
        core_object = obj_match if obj_match else "3d asset"

        return StructuredPrompt(
            object=core_object,
            style=detected_style,
            material=detected_material,
            details=details,
            texture=detected_texture,
            quality=quality,
            target_format=target_format,
            polygon_budget=polygon_budget,
            raw_prompt=raw_prompt,
        )

prompt_engine = PromptProcessingEngine()
