from fastapi import APIRouter, Depends
from logging_module import logger
from utils.dependencies import get_current_user_id
from services import candidate_analysis_service
from fastapi.responses import JSONResponse
from typing import Optional
from utils import helper_functions
from blueprints.candidate_analysis_blueprint import CandidateAnalysisRequestBody

router = APIRouter()


@router.post("/test-gpt")
async def test_gpt(user_id: str = Depends(get_current_user_id)):
    """Test the GPT API by sending a sample prompt."""
    logger.info("Test GPT entry point")
    response = await candidate_analysis_service.test_gpt(user_id)
    logger.info("Test GPT exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )


@router.post("/analyze-candidate")
async def analyze_candidate(
    request: CandidateAnalysisRequestBody,
    salesforce_user_id: str,
    call_id: Optional[str] = "",
    user_id: str = Depends(get_current_user_id),
):
    """Analyze the candidate based on job description and transcript."""
    logger.info("Analyze candidate entry point")
    response = await candidate_analysis_service.analyze_candidate(
        request.job_description, call_id, salesforce_user_id
    )
    logger.info("Analyze candidate exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )


@router.get("/get-content-of-pdf-from-salesforce-user")
async def get_content_of_pdf_from_salesforce_user(salesforce_user_id: str, user_id: str = Depends(get_current_user_id)):
    """Get the content of the first PDF file from a Salesforce user."""
    logger.info("Get content of PDF from Salesforce user entry point")
    response = await helper_functions.get_content_of_pdf_from_salesforce_user(
        salesforce_user_id
    )
    logger.info("Get content of PDF from Salesforce user exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )
