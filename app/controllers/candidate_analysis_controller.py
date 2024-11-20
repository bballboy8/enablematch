from fastapi import APIRouter, Request, Depends
import services 
from logging_module import logger
from fastapi.security import OAuth2PasswordRequestForm
from utils.dependencies import get_current_user_id
from services import candidate_analysis_service
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/test-gpt")
async def test_gpt(user_id:str="user"):
    """Test the GPT API by sending a sample prompt."""
    logger.info("Test GPT entry point")
    response = await candidate_analysis_service.test_gpt(user_id)
    logger.info("Test GPT exit point")
    return JSONResponse(content={"response": response}, status_code=response["status_code"])


@router.post("/analyze-candidate")
async def analyze_candidate(job_description: str, call_id: str):
    """Analyze the candidate based on job description and transcript."""
    logger.info("Analyze candidate entry point")
    response = await candidate_analysis_service.analyze_candidate(job_description, call_id)
    logger.info("Analyze candidate exit point")
    return JSONResponse(content={"response": response}, status_code=response["status_code"])