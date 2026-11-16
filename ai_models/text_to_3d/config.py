import os
from typing import Optional, Tuple
from pydantic import BaseModel, Field

class TextTo3DConfig(BaseModel):
    """
    Configuration for Text-to-3D AI Generation.
    Supports OpenAI Shap-E, Hunyuan3D architectural evaluation,
    and documented procedural volumetric fallback synthesis.
    """
    model_name: str = "shap-e-text300M"
    device: str = "auto"  # 'auto', 'cuda', or 'cpu'
    torch_dtype: str = "float32"
    guidance_scale: float = 15.0
    karras_steps: int = 32
    sigma_min: float = 1e-3
    sigma_max: float = 160.0
    s_churn: float = 0.0
    generation_timeout_seconds: float = 120.0
    enable_fallback_mode: bool = True
    output_format: str = "obj"  # 'obj' or 'ply'
    cache_dir: Optional[str] = "D:\\shap_e_model_cache"
    preview_resolution: Tuple[int, int] = (512, 512)

    class Config:
        arbitrary_types_allowed = True

default_config = TextTo3DConfig()
