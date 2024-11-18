from fastapi import APIRouter
from controllers.candidate_analysis_controller import router as candidate_analysis_router

router = APIRouter()

router.include_router(candidate_analysis_router, prefix="/candidate-analysis", tags=["Candidate Analysis"])
