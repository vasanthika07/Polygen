import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.prompt import PromptAnalyzeRequest, PromptSpecification
from app.services.prompt_engine import prompt_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompt", tags=["Prompt Understanding Engine"])

@router.post(
    "/analyze",
    response_model=PromptSpecification,
    status_code=status.HTTP_200_OK,
    summary="Analyze and parse natural-language 3D asset prompt"
)
async def analyze_prompt(request: PromptAnalyzeRequest) -> PromptSpecification:
    """
    Parses natural-language descriptions into structured 3D generation specifications.
    Extracts object type, materials, colors, style, surface details, lighting,
    special effects, geometry/texture requirements, negative prompts, and model adapters.

    Note: This service performs natural language prompt analysis and specification synthesis;
    it does not generate 3D assets or binary geometry.
    """
    try:
        specification = prompt_engine.analyze(request)
        return specification
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error analyzing prompt '{request.prompt}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze prompt: {str(e)}"
        )

