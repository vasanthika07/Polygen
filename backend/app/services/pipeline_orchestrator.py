import os
import time
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models.job import GenerationJob
from app.models.asset import GeneratedAsset
from app.core.websocket_manager import ws_manager
from app.services.prompt_engine import prompt_engine
from ai_models.text_to_3d.generator import text_to_3d_generator
from processing.mesh_cleaner import mesh_cleaner
from processing.uv_unwrapper import uv_unwrapper
from processing.texture_baker import texture_baker
from processing.mesh_optimizer import mesh_optimizer
from processing.glb_exporter import glb_exporter

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Core Generation Orchestrator
    Executes the 8-stage text-to-3D asset pipeline sequentially,
    broadcasting live status events via WebSockets and updating database state.
    """

    @classmethod
    async def run_pipeline(
        cls,
        job_id: str,
        db_factory,
        style_override: str = None,
        quality: str = "high",
        polygon_budget: int = 10000,
        target_format: str = "glb",
    ):
        logger.info(f"Starting PolyGen pipeline for job: {job_id}")

        async def update_stage(stage: str, progress: int, message: str, data: dict = None):
            async with db_factory() as db:
                result = await db.execute(select(GenerationJob).where(GenerationJob.job_id == job_id))
                job = result.scalars().first()
                if job:
                    job.current_stage = stage
                    job.progress = progress
                    job.status = "processing"
                    await db.commit()

            # Broadcast via WebSocket
            payload = {
                "job_id": job_id,
                "stage": stage,
                "progress": progress,
                "message": message,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            await ws_manager.broadcast_to_job(job_id, payload)

        try:
            # Retrieve initial job
            async with db_factory() as db:
                result = await db.execute(select(GenerationJob).where(GenerationJob.job_id == job_id))
                job = result.scalars().first()
                if not job:
                    logger.error(f"Job {job_id} not found.")
                    return
                raw_prompt = job.prompt
                user_id = job.user_id

            # ==========================================
            # STAGE 1: PROMPT PROCESSING (10%)
            # ==========================================
            await update_stage(
                stage="prompt_processing",
                progress=10,
                message="Deconstructing natural-language semantics, materials, and geometry",
            )
            structured_prompt = prompt_engine.process(
                raw_prompt=raw_prompt,
                style_override=style_override,
                quality=quality,
                polygon_budget=polygon_budget,
                target_format=target_format,
            )
            time.sleep(0.5)

            # ==========================================
            # STAGE 2: 3D MESH GENERATION (35%)
            # ==========================================
            await update_stage(
                stage="mesh_generation",
                progress=35,
                message=f"Generating 3D polygonal surface for '{structured_prompt.object}'",
                data={"structured_prompt": structured_prompt.model_dump()},
            )
            raw_mesh_path = os.path.join(settings.STORAGE_RAW_DIR, f"{job_id}_raw.obj")
            raw_mesh, gen_meta = text_to_3d_generator.generate(structured_prompt, raw_mesh_path)
            time.sleep(0.5)

            # ==========================================
            # STAGE 3: MESH CLEANING & UV UNWRAPPING (50%)
            # ==========================================
            await update_stage(
                stage="uv_mapping",
                progress=50,
                message="Cleaning topology and generating non-overlapping UV atlas charts",
                data={"raw_faces": len(raw_mesh.faces), "raw_vertices": len(raw_mesh.vertices)},
            )
            cleaned_mesh, clean_stats = mesh_cleaner.clean(raw_mesh)
            unwrapped_mesh, uv_stats = uv_unwrapper.unwrap(cleaned_mesh)
            time.sleep(0.5)

            # ==========================================
            # STAGE 4: PBR TEXTURE SYNTHESIS (65%)
            # ==========================================
            await update_stage(
                stage="texture_generation",
                progress=65,
                message="Synthesizing PBR diffuse, roughness, metallic, normal, and emissive maps",
                data={"uv_stats": uv_stats},
            )
            textures_dir = os.path.join(settings.STORAGE_TEXTURES_DIR, job_id)
            tex_paths = texture_baker.generate_pbr_set(
                prompt_data=structured_prompt,
                output_dir=textures_dir,
                resolution=1024 if quality != "standard" else 512,
            )
            time.sleep(0.5)

            # ==========================================
            # STAGE 5: MESH OPTIMIZATION & DECIMATION (80%)
            # ==========================================
            await update_stage(
                stage="mesh_optimization",
                progress=80,
                message=f"Decimating mesh to target budget ({structured_prompt.polygon_budget} polygons)",
            )
            optimized_mesh, opt_stats = mesh_optimizer.optimize(
                mesh=unwrapped_mesh,
                target_polygon_budget=structured_prompt.polygon_budget,
            )
            time.sleep(0.5)

            # ==========================================
            # STAGE 6: PBR MATERIAL ASSIGNMENT & GLB EXPORT (90%)
            # ==========================================
            await update_stage(
                stage="material_assignment",
                progress=90,
                message="Binding PBR texture channels and packing glTF 2.0 binary GLB",
                data={"optimization_stats": opt_stats},
            )
            output_glb_path = os.path.join(settings.STORAGE_EXPORTS_DIR, f"{job_id}.glb")
            export_stats = glb_exporter.export(
                mesh=optimized_mesh,
                texture_paths=tex_paths,
                output_glb_path=output_glb_path,
            )
            time.sleep(0.5)

            # ==========================================
            # STAGE 7 & 8: ASSET PERSISTENCE & COMPLETED (100%)
            # ==========================================
            final_poly_count = export_stats["verified_faces"]
            final_file_size = export_stats["file_size_bytes"]
            asset_name = f"{structured_prompt.object.title()} ({structured_prompt.style.title()})"

            async with db_factory() as db:
                asset = GeneratedAsset(
                    job_id=job_id,
                    user_id=user_id,
                    asset_name=asset_name,
                    glb_path=output_glb_path,
                    preview_path=tex_paths.get("basecolor"),
                    polygon_count=final_poly_count,
                    file_size=final_file_size,
                    texture_resolution=1024 if quality != "standard" else 512,
                )
                db.add(asset)
                
                result = await db.execute(select(GenerationJob).where(GenerationJob.job_id == job_id))
                job = result.scalars().first()
                if job:
                    job.status = "completed"
                    job.progress = 100
                    job.current_stage = "completed"
                    job.completed_at = datetime.utcnow()
                await db.commit()
                await db.refresh(asset)
                asset_id = asset.asset_id

            await update_stage(
                stage="completed",
                progress=100,
                message="Asset generated and verified! Ready for 3D inspection and download.",
                data={
                    "asset_id": asset_id,
                    "glb_url": f"/api/assets/{asset_id}/download",
                    "polygon_count": final_poly_count,
                    "file_size": final_file_size,
                    "file_size_mb": export_stats.get("file_size_mb", 0),
                    "dimensions": export_stats.get("bounding_box_dimensions", []),
                },
            )
            logger.info(f"Pipeline successfully completed for job: {job_id}")

        except Exception as e:
            logger.error(f"Pipeline failed for job {job_id}: {e}", exc_info=True)
            async with db_factory() as db:
                result = await db.execute(select(GenerationJob).where(GenerationJob.job_id == job_id))
                job = result.scalars().first()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    await db.commit()

            await ws_manager.broadcast_to_job(job_id, {
                "job_id": job_id,
                "stage": "failed",
                "progress": 0,
                "message": f"Generation error: {str(e)}",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })

pipeline_orchestrator = PipelineOrchestrator()

