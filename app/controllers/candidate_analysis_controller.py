from fastapi import APIRouter
from logging_module import logger
from utils.dependencies import get_current_user_id
from services import candidate_analysis_service
from fastapi.responses import JSONResponse
from typing import Optional
from utils import helper_functions

router = APIRouter()


@router.post("/test-gpt")
async def test_gpt(user_id: str = "user"):
    """Test the GPT API by sending a sample prompt."""
    logger.info("Test GPT entry point")
    response = await candidate_analysis_service.test_gpt(user_id)
    logger.info("Test GPT exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )


@router.post("/analyze-candidate")
async def analyze_candidate(
    job_description: str,
    salesforce_user_id: str,
    call_id: Optional[str] = "",
):
    """Analyze the candidate based on job description and transcript."""
    logger.info("Analyze candidate entry point")
    response = await candidate_analysis_service.analyze_candidate(
        job_description, call_id, salesforce_user_id
    )
    logger.info("Analyze candidate exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )


@router.get("/get-content-of-pdf-from-salesforce-user")
async def get_content_of_pdf_from_salesforce_user(salesforce_user_id: str):
    """Get the content of the first PDF file from a Salesforce user."""
    logger.info("Get content of PDF from Salesforce user entry point")
    response = await helper_functions.get_content_of_pdf_from_salesforce_user(
        salesforce_user_id
    )
    logger.info("Get content of PDF from Salesforce user exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )
