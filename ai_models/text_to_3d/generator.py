import os
import gc
import time
import logging
import warnings
from typing import Tuple, Dict, Any, Union, Optional
import trimesh

from app.config import settings
from app.schemas.job import StructuredPrompt
from app.services.prompt_engine import prompt_engine
from ai_models.text_to_3d.config import default_config, TextTo3DConfig
from ai_models.text_to_3d.hardware import hardware_detector
from ai_models.text_to_3d.model_loader import model_loader
from ai_models.text_to_3d.prompt_formatter import prompt_formatter
from ai_models.text_to_3d.procedural_synthesizer import procedural_synthesizer
from ai_models.text_to_3d.mesh_validator import mesh_validator
from ai_models.text_to_3d.preview_generator import preview_generator
from ai_models.text_to_3d.inference_service import model_inference_service

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

class TextTo3DGenerator:
    """
    Module 2: 3D Mesh Generation Engine
    Orchestrates the 10-step AI Text-to-3D Geometry Pipeline:
    1. Receive user prompt.
    2. Load / parse structured prompt.
    3. Apply model-specific prompt formatting.
    4. Load the selected AI model / evaluate hardware.
    5. Generate geometry (with timeout and memory tracking).
    6. Extract mesh vertices and faces.
    7. Validate geometry (degenerate face removal, watertightness check).
    8. Save raw mesh (OBJ or PLY).
    9. Generate offscreen 3D preview render.
    10. Return output path and generation telemetry metadata.
    """

    def __init__(self, config: Optional[TextTo3DConfig] = None):
        self.config = config or default_config
        self.device = hardware_detector.get_hardware_info()["cuda_available"] and "cuda" or "cpu"
        self.inference_service = model_inference_service

    def generate(
        self,
        prompt_input: Union[str, StructuredPrompt],
        output_path: Optional[str] = None,
        output_format: str = "obj",
        generate_preview_image: bool = True,
    ) -> Tuple[trimesh.Trimesh, Dict[str, Any]]:
        """
        Executes the full 10-step text-to-3D pipeline.

        Args:
            prompt_input: Either raw string prompt or StructuredPrompt instance.
            output_path: Target file path to write raw mesh (defaults to storage/raw_meshes/).
            output_format: 'obj' or 'ply'.
            generate_preview_image: Whether to render an offscreen thumbnail preview.

        Returns:
            Tuple of (trimesh.Trimesh, metadata_dict)
        """
        start_pipeline = time.perf_counter()

        # Step 1 & 2: Receive user prompt & load structured prompt
        if isinstance(prompt_input, str):
            structured_prompt = prompt_engine.process(prompt_input)
        else:
            structured_prompt = prompt_input

        raw_prompt = structured_prompt.raw_prompt
        logger.info(f"[TextTo3D] Starting 3D generation for prompt: '{raw_prompt}'")

        # Step 3, 4, 5 & 6: Format prompt, load model, run inference with timeout & memory tracking, extract vertices/faces
        mesh, telemetry = self.inference_service.run_inference(structured_prompt)

        # Step 7: Validate Geometry
        mesh, val_stats = mesh_validator.validate_and_clean(mesh)

        # Determine target output file path
        if not output_path:
            import uuid
            job_slug = str(uuid.uuid4())[:8]
            output_path = os.path.join(settings.STORAGE_RAW_DIR, f"{job_slug}_raw.{output_format}")

        abs_output = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)

        # Step 8: Save the raw mesh (OBJ or PLY)
        mesh.export(abs_output, file_type=output_format)
        logger.info(f"[TextTo3D] Raw mesh exported ({output_format.upper()}) to {abs_output}")

        # Step 9: Generate Preview Thumbnail Render
        preview_path = None
        if generate_preview_image:
            base_name = os.path.splitext(os.path.basename(abs_output))[0]
            preview_target = os.path.join(settings.STORAGE_THUMBNAILS_DIR, f"{base_name}_preview.png")
            preview_path = preview_generator.generate_preview(mesh, preview_target)

        total_pipeline_time_ms = round((time.perf_counter() - start_pipeline) * 1000, 2)

        # Step 10: Compile and Return Output Path and Comprehensive Metadata
        file_size_bytes = os.path.getsize(abs_output) if os.path.exists(abs_output) else 0

        metadata: Dict[str, Any] = {
            # Identification & Paths
            "output_raw_path": abs_output,
            "preview_image_path": preview_path,
            "output_format": output_format,
            "file_size_bytes": file_size_bytes,
            "file_size_kb": round(file_size_bytes / 1024, 2),

            # Semantic Attributes
            "object": structured_prompt.object,
            "style": structured_prompt.style,
            "material": structured_prompt.material,
            "details": structured_prompt.details,
            "raw_prompt": raw_prompt,

            # Geometry Validation Metrics
            "raw_vertices": val_stats["valid_vertices"],
            "raw_faces": val_stats["valid_faces"],
            "bounding_box": val_stats["bounding_box_extents"],
            "bounding_box_volume": val_stats["bounding_box_volume"],
            "surface_area": val_stats["surface_area"],
            "is_watertight": val_stats["is_watertight"],
            "is_manifold": val_stats["is_winding_consistent"],
            "validation_stats": val_stats,

            # Performance Telemetry
            "model_used": telemetry["model_used"],
            "execution_mode": telemetry["execution_mode"],
            "device": telemetry["device"],
            "gpu_detected": telemetry["gpu_detected"],
            "gpu_name": telemetry.get("gpu_name"),
            "fallback_used": telemetry["fallback_used"],
            "fallback_reason": telemetry["fallback_reason"],
            "model_loading_time_ms": telemetry["model_loading_time_ms"],
            "inference_time_ms": telemetry["inference_time_ms"],
            "mesh_generation_time_ms": telemetry["mesh_generation_time_ms"],
            "total_pipeline_time_ms": total_pipeline_time_ms,
            "memory_usage_mb": telemetry["memory_usage_mb"],
            "formatted_prompt": telemetry["formatted_prompt"],
        }

        # Clear garbage collection
        gc.collect()

        return mesh, metadata

text_to_3d_generator = TextTo3DGenerator()
