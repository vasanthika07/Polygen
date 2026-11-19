import os
import trimesh
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.config import settings
from processing.mesh_optimizer import mesh_optimizer, PolygonBudgetPreset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimizer", tags=["Mesh Optimization Engine"])

class AnalyzeMeshRequest(BaseModel):
    asset_id: Optional[str] = Field(None, description="ID of an existing generated asset")
    mesh_path: Optional[str] = Field(None, description="Local path to an OBJ, PLY or GLB mesh file")

class OptimizeMeshRequest(BaseModel):
    asset_id: Optional[str] = Field(None, description="ID of an existing asset to optimize")
    mesh_path: Optional[str] = Field(None, description="Local path to input mesh file")
    budget_preset: str = Field(default="medium", description="Polygon budget preset: 'low', 'medium', 'high', 'custom'")
    custom_budget: Optional[int] = Field(None, description="Arbitrary polygon budget integer when using 'custom'")
    normalize_bounds: bool = Field(default=True, description="Center mesh at origin and scale to unit bounds")
    align_ground: bool = Field(default=True, description="Align mesh bottom with ground plane y=0")
    target_scale: Optional[float] = Field(default=1.0, description="Target bounding scale dimension")
    remove_duplicates: bool = Field(default=True, description="Remove duplicate vertices and degenerate faces")

@router.get("/presets", status_code=status.HTTP_200_OK)
async def get_budget_presets() -> Dict[str, Any]:
    """
    Returns available standard polygon budget presets and recommended use-cases.
    """
    return {
        "presets": {
            "low": {
                "name": "Mobile & WebGL LOD",
                "target_polygons": mesh_optimizer.PRESETS[PolygonBudgetPreset.LOW],
                "description": "Lightweight LOD for mobile browsers, AR, and massive crowd instances.",
            },
            "medium": {
                "name": "Standard Real-Time Asset",
                "target_polygons": mesh_optimizer.PRESETS[PolygonBudgetPreset.MEDIUM],
                "description": "Balanced budget for desktop games, VR environments, and digital twins.",
            },
            "high": {
                "name": "Hero Asset & Cinematic",
                "target_polygons": mesh_optimizer.PRESETS[PolygonBudgetPreset.HIGH],
                "description": "High-fidelity geometry for hero props, close-up inspection, and rendering.",
            },
            "custom": {
                "name": "User-Defined Budget",
                "target_polygons": None,
                "description": "Specify an exact arbitrary triangle target budget.",
            },
        }
    }

@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_mesh_topology(request: AnalyzeMeshRequest) -> Dict[str, Any]:
    """
    Inspects 3D mesh topology and returns polygon counts, surface metrics, and LOD recommendations.
    """
    file_path = None
    if request.mesh_path and os.path.exists(request.mesh_path):
        file_path = request.mesh_path
    elif request.asset_id:
        candidate_glb = os.path.join(settings.STORAGE_EXPORTS_DIR, f"{request.asset_id}.glb")
        candidate_obj = os.path.join(settings.STORAGE_PROCESSED_DIR, f"{request.asset_id}_cleaned.obj")
        if os.path.exists(candidate_glb):
            file_path = candidate_glb
        elif os.path.exists(candidate_obj):
            file_path = candidate_obj

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mesh not found for asset_id '{request.asset_id}' or path '{request.mesh_path}'."
        )

    try:
        mesh = trimesh.load(file_path, process=False)
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)])
        
        analysis = mesh_optimizer.analyze_mesh(mesh)
        analysis["file_path"] = file_path
        analysis["file_size_bytes"] = os.path.getsize(file_path)
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze mesh at '{file_path}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/optimize", status_code=status.HTTP_200_OK)
async def optimize_mesh(request: OptimizeMeshRequest) -> Dict[str, Any]:
    """
    Executes quadric decimation, vertex optimization, UV/material preservation,
    and bounding normalization, returning a comprehensive optimization report.
    """
    file_path = None
    asset_id = request.asset_id or "custom_mesh"

    if request.mesh_path and os.path.exists(request.mesh_path):
        file_path = request.mesh_path
    elif request.asset_id:
        candidate_glb = os.path.join(settings.STORAGE_EXPORTS_DIR, f"{request.asset_id}.glb")
        candidate_obj = os.path.join(settings.STORAGE_PROCESSED_DIR, f"{request.asset_id}_cleaned.obj")
        if os.path.exists(candidate_glb):
            file_path = candidate_glb
        elif os.path.exists(candidate_obj):
            file_path = candidate_obj

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mesh not found for asset_id '{request.asset_id}' or path '{request.mesh_path}'."
        )

    try:
        mesh = trimesh.load(file_path, process=False)
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)])

        out_name = f"{asset_id}_optimized_{request.budget_preset}.glb"
        out_path = os.path.join(settings.STORAGE_EXPORTS_DIR, out_name)

        optimized_mesh, report = mesh_optimizer.optimize(
            mesh=mesh,
            budget_preset=request.budget_preset,
            custom_budget=request.custom_budget,
            normalize_bounds=request.normalize_bounds,
            align_ground=request.align_ground,
            target_scale=request.target_scale,
            remove_duplicates=request.remove_duplicates,
            input_file_path=file_path,
            output_file_path=out_path,
        )

        return {
            "status": "SUCCESS",
            "optimized_file_path": out_path,
            "optimized_file_name": out_name,
            "report": report,
        }
    except Exception as e:
        logger.error(f"Optimization failed for '{file_path}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mesh optimization failed: {str(e)}"
        )
