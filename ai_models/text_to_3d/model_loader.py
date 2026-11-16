import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
from app.config import settings
from ai_models.text_to_3d.hardware import hardware_detector
from ai_models.text_to_3d.config import default_config

logger = logging.getLogger(__name__)

class ModelLoader:
    """
    Manages loading, device placement, weight caching, and lifecycle for
    Text-to-3D models (Shap-E transmitter, text300M, diffusion scheduler).
    """

    def __init__(self):
        self.xm = None
        self.model = None
        self.diffusion = None
        self.device = None
        self.loaded_model_name = None
        self.is_loaded = False
        self.load_error = None
        self.loading_time_ms = 0.0

    def detect_device(self) -> str:
        """Determines target execution device (cuda or cpu)."""
        hw = hardware_detector.get_hardware_info()
        if settings.DEVICE == "cuda" and hw["cuda_available"]:
            return "cuda"
        elif settings.DEVICE == "cpu":
            return "cpu"
        elif hw["cuda_available"]:
            return "cuda"
        return "cpu"

    def load_shape_models(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Loads OpenAI Shap-E weights ('transmitter' and 'text300M') with timing and telemetry.
        Returns a dictionary describing the load result, device, and timing.
        """
        if self.is_loaded and not force_reload:
            return {
                "success": True,
                "cached": True,
                "device": self.device,
                "model_name": self.loaded_model_name,
                "model_loading_time_ms": self.loading_time_ms,
            }

        start_time = time.perf_counter()
        target_device = self.detect_device()
        self.device = target_device

        logger.info(f"Initiating Shap-E model load on device: {target_device}")

        try:
            import torch
            from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
            from shap_e.models.download import load_model, load_config

            # Set model cache directory if configured
            cache_dir = default_config.cache_dir
            if cache_dir and os.path.exists(cache_dir):
                os.environ["SHAP_E_CACHE_DIR"] = cache_dir

            torch_device = torch.device(target_device)

            logger.info("Loading Shap-E transmitter decoder...")
            self.xm = load_model('transmitter', device=torch_device)

            logger.info("Loading Shap-E text300M diffusion model...")
            self.model = load_model('text300M', device=torch_device)

            logger.info("Initializing Gaussian diffusion scheduler...")
            self.diffusion = diffusion_from_config(load_config('diffusion'))

            self.is_loaded = True
            self.loaded_model_name = "shap-e-text300M"
            self.load_error = None
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.loading_time_ms = elapsed_ms

            logger.info(f"Shap-E models successfully initialized in {elapsed_ms} ms on {target_device}")

            return {
                "success": True,
                "cached": False,
                "device": target_device,
                "model_name": self.loaded_model_name,
                "model_loading_time_ms": elapsed_ms,
            }

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.loading_time_ms = elapsed_ms
            self.is_loaded = False
            self.load_error = str(e)
            logger.warning(
                f"Shap-E neural model load failed on {target_device} ({e}). "
                f"Documented high-precision procedural fallback will be active."
            )
            return {
                "success": False,
                "cached": False,
                "device": target_device,
                "error": str(e),
                "model_loading_time_ms": elapsed_ms,
                "fallback_mode": "procedural_sdf_synthesis",
            }

    def unload(self):
        """Releases model weights and frees memory."""
        self.xm = None
        self.model = None
        self.diffusion = None
        self.is_loaded = False
        hardware_detector.clean_memory()
        logger.info("Shap-E models unloaded and memory cleaned.")

model_loader = ModelLoader()
