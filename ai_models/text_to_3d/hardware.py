import os
import gc
import logging
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class HardwareDetector:
    """
    Hardware detection and telemetry service for Text-to-3D pipeline.
    Monitors CPU cores, CUDA GPUs, system RAM, and GPU VRAM.
    """

    @classmethod
    def get_hardware_info(cls) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "platform": os.name,
            "cpu_count": os.cpu_count() or 1,
            "cuda_available": False,
            "gpu_name": None,
            "gpu_memory_total_mb": 0.0,
            "system_ram_total_mb": 0.0,
            "system_ram_available_mb": 0.0,
        }

        # System RAM via psutil
        if psutil:
            mem = psutil.virtual_memory()
            info["system_ram_total_mb"] = round(mem.total / (1024 * 1024), 2)
            info["system_ram_available_mb"] = round(mem.available / (1024 * 1024), 2)

        # PyTorch CUDA detection
        try:
            import torch
            info["torch_version"] = torch.__version__
            cuda_avail = torch.cuda.is_available()
            info["cuda_available"] = cuda_avail
            if cuda_avail:
                info["gpu_count"] = torch.cuda.device_count()
                info["gpu_name"] = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                info["gpu_memory_total_mb"] = round(props.total_memory / (1024 * 1024), 2)
                info["cuda_capability"] = f"{props.major}.{props.minor}"
        except Exception as e:
            logger.debug(f"PyTorch CUDA detection error: {e}")

        return info

    @classmethod
    def get_memory_usage_mb(cls) -> float:
        """Returns the current process resident memory in Megabytes."""
        if psutil:
            try:
                process = psutil.Process(os.getpid())
                return round(process.memory_info().rss / (1024 * 1024), 2)
            except Exception:
                pass
        return 0.0

    @classmethod
    def get_gpu_memory_usage_mb(cls) -> float:
        """Returns the current process GPU memory allocated in Megabytes."""
        try:
            import torch
            if torch.cuda.is_available():
                return round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
        except Exception:
            pass
        return 0.0

    @classmethod
    def clean_memory(cls):
        """Forces Python garbage collection and clears PyTorch CUDA cache."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    @classmethod
    def evaluate_model_fit(cls, model_name: str) -> Dict[str, Any]:
        """
        Evaluates hardware compatibility for candidate text-to-3D models:
        - Shap-E: OpenAI latent diffusion model; ~4GB VRAM on CUDA; CPU fallback supported.
        - Hunyuan3D: Tencent dense 3D diffusion; requires >=16GB VRAM CUDA GPU + flash-attn.
        - TripoSR: Large Reconstruction Model; strictly image-to-3D single view pipeline.
        """
        hw = cls.get_hardware_info()
        cuda_ok = hw["cuda_available"]
        vram = hw.get("gpu_memory_total_mb", 0.0)

        evaluations = {
            "shap-e": {
                "supported": True,
                "preferred_device": "cuda" if cuda_ok else "cpu",
                "reason": "Direct text-conditioned diffusion; light latent space representations; CPU execution or fallback supported.",
                "meets_vram_requirement": cuda_ok and vram >= 3500,
            },
            "hunyuan3d": {
                "supported": cuda_ok and vram >= 16000,
                "preferred_device": "cuda",
                "reason": "High-density multi-view diffusion model; requires minimum 16GB VRAM CUDA with compiled flash-attn kernel. Not runnable on CPU.",
                "meets_vram_requirement": cuda_ok and vram >= 16000,
            },
            "triposr": {
                "supported": False,
                "preferred_device": "cuda",
                "reason": "TripoSR is strictly an Image-to-3D single-view reconstruction model, reserved for image conditioning in Part 7.",
                "meets_vram_requirement": False,
            },
        }
        return evaluations.get(model_name.lower(), evaluations["shap-e"])

hardware_detector = HardwareDetector()
