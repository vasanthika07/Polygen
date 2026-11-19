from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class PromptAnalyzeRequest(BaseModel):
    """Input payload for natural language prompt analysis."""
    prompt: str = Field(..., min_length=3, max_length=1000, description="Natural-language description of 3D asset")
    style_override: Optional[str] = Field(None, description="Optional user manual style override")
    quality: Optional[str] = Field("high", description="Target quality tier")
    polygon_budget: Optional[int] = Field(10000, ge=500, le=50000, description="Polygon target limit")
    target_format: Optional[str] = Field("glb", description="Desired export format")

    @field_validator("prompt")
    @classmethod
    def validate_and_strip_prompt(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 3:
            raise ValueError("Prompt must contain at least 3 non-whitespace characters")
        return trimmed

class ShapeGeometryDescription(BaseModel):
    """Geometric topology and volumetric properties."""
    primary_shape: str = Field(..., description="Dominant primitive or volumetric shape")
    symmetry: str = Field("none", description="Geometric symmetry: bilateral, radial, none")
    proportions: str = Field("balanced", description="Proportions: elongated, compact, tall, wide")
    topology: str = Field("manifold", description="Target topology requirements")

class ModelSpecificPrompts(BaseModel):
    """Specialized adapted prompts optimized for distinct AI generation engines."""
    shap_e: str = Field(..., description="Optimized prompt for OpenAI Shap-E text-to-3D")
    hunyuan3d: str = Field(..., description="Optimized prompt for Tencent Hunyuan3D dense mesh synthesis")
    stable_diffusion: str = Field(..., description="Optimized prompt for Stable Diffusion UV texture synthesis")
    triposr: str = Field(..., description="Neutral isolated rendering prompt for TripoSR reconstruction")

class PromptSpecification(BaseModel):
    """
    Validated structured specification for 3D model generation,
    satisfying the exact PolyGen Part 5 Master Specification.
    """
    object: str = Field(..., description="Primary object / entity identified")
    style: str = Field(..., description="Classified artistic or aesthetic style")
    materials: List[str] = Field(default_factory=list, description="Extracted and inferred material layers")
    colors: List[str] = Field(default_factory=list, description="Extracted dominant and accent colors")
    surface_details: List[str] = Field(default_factory=list, description="Micro and macro surface textures and imperfections")
    lighting: str = Field("cinematic", description="Interpreted studio or scene lighting conditions")
    special_effects: List[str] = Field(default_factory=list, description="Emissive glows, auras, elemental fx")
    geometry_requirements: List[str] = Field(default_factory=list, description="Physical and topological mesh constraints")
    texture_requirements: List[str] = Field(default_factory=list, description="PBR channel requirements and resolution")
    negative_prompt: List[str] = Field(default_factory=list, description="Unwanted attributes and generation artifacts")

    # Extended intelligence metadata
    category: Optional[str] = Field("prop", description="Identified taxonomy category")
    shape_and_geometry: Optional[ShapeGeometryDescription] = None
    model_prompts: Optional[ModelSpecificPrompts] = None
    inferred_details: Optional[List[str]] = Field(default_factory=list, description="Details inferred by engine to fill missing prompt gaps")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score of parser extraction")
    raw_prompt: Optional[str] = None

