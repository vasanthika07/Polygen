from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from processing.pbr_material_system import pbr_material_system, MaterialClass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/materials", tags=["Materials & PBR"])

class MaterialEvaluateRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Natural language prompt describing object and materials")
    material_type: Optional[str] = Field(None, description="Explicit material category")
    details: Optional[List[str]] = Field(default_factory=list, description="Surface details or accent descriptors")
    custom_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom factor overrides")

@router.get("/presets", status_code=status.HTTP_200_OK)
async def get_material_presets() -> Dict[str, Any]:
    """
    Returns available physically based rendering (PBR) presets matching glTF 2.0 standards:
    rusted_sword, glowing_sapphire, carved_wood, granite_stone, translucent_glass, polished_gold.
    """
    return {
        "count": len(pbr_material_system.PRESETS),
        "presets": pbr_material_system.PRESETS,
    }

@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_material(request: MaterialEvaluateRequest) -> Dict[str, Any]:
    """
    Classifies the material, generates glTF 2.0 PBR properties, and verifies schema compatibility.
    """
    prompt_input = {
        "raw_prompt": request.prompt or "",
        "material": request.material_type or "",
        "details": request.details or [],
    }

    params = pbr_material_system.generate_material_parameters(
        prompt_data=prompt_input,
        custom_overrides=request.custom_overrides,
    )

    validation = pbr_material_system.validate_gltf_compatibility(params)

    return {
        "classification": params["classification"],
        "gltf_pbr_parameters": {
            "name": params["name"],
            "material_class": params["material_class"],
            "base_color_factor": params["base_color_factor"],
            "metallic_factor": params["metallic_factor"],
            "roughness_factor": params["roughness_factor"],
            "normal_scale": params["normal_scale"],
            "occlusion_strength": params["occlusion_strength"],
            "emissive_factor": params["emissive_factor"],
            "emissive_intensity": params["emissive_intensity"],
            "alpha_mode": params["alpha_mode"],
            "alpha_cutoff": params["alpha_cutoff"],
            "double_sided": params["double_sided"],
            "ior": params["ior"],
        },
        "validation": validation,
        "gltf_validation": validation,
        "description": params["description"],
    }
