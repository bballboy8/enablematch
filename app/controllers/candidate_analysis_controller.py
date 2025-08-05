from fastapi import APIRouter, Depends
from logging_module import logger
from utils.dependencies import get_current_user_id
from services import candidate_analysis_service
from fastapi.responses import JSONResponse
from typing import Optional
from utils import helper_functions
from blueprints.candidate_analysis_blueprint import CandidateAnalysisRequestBody, CandidateSuggestionsRequestBody, DBCandidateAnalysisRequestBody
from fastapi.background import BackgroundTasks
from pydantic import BaseModel

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
    call_id: Optional[list[str]] = None,
    linkedin_profile_url: Optional[str] = None,
):
    """Analyze the candidate based on job description and transcript."""
    logger.info("Analyze candidate entry point")
    response = await candidate_analysis_service.analyze_candidate(
        request.job_description, call_id, salesforce_user_id, linkedin_profile_url
    )
    logger.info("Analyze candidate exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )

@router.post("/analyze-database-candidate")
async def analyze_database_candidate(
    request: DBCandidateAnalysisRequestBody,
    user_id: str = Depends(get_current_user_id)
):
    """Analyze the candidate based on job description and transcript."""
    logger.info("Analyze database candidate entry point")
    response = await candidate_analysis_service.analyze_database_candidate(
    db_id=request.db_user_id, job_description=request.job_description
    )
    logger.info("Analyze database candidate exit point")
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


@router.put("/generate-conversation-summary")
async def generate_conversation_summary(
    background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user_id)  
):
    """Generate a conversation summary based on the call transcript."""
    logger.info("Generate conversation summary entry point")
    background_tasks.add_task(candidate_analysis_service.generate_conversation_summary)
    background_tasks
    logger.info("Generate conversation summary exit point")
    return JSONResponse(
        content={"response": "Conversation summary generation has been initiated."},
        status_code=200,
    )

@router.get("/get-target-candidates")
async def get_target_candidates(background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user_id)):
    """Get the target candidates for the user."""
    logger.info("Get target candidates entry point")
    background_tasks.add_task(candidate_analysis_service.fetch_target_candidates)
    logger.info("Get target candidates exit point")
    return JSONResponse(
        content={"response": "Target candidates generation has been initiated."},
        status_code=200,
    )

@router.put("/upload-cooked-records-to-pinecone")
async def upload_cooked_records_to_pinecone(background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user_id)):
    """Upload the cooked records to Pinecone."""
    logger.info("Upload cooked records to Pinecone entry point")
    background_tasks.add_task(candidate_analysis_service.upload_cooked_records_to_pinecone)
    logger.info("Upload cooked records to Pinecone exit point")
    return JSONResponse(
        content={"response": "Cooked records upload to Pinecone has been initiated."},
        status_code=200,
    )

@router.post("/get-candidate-suggestions")
async def get_candidate_suggestions(request: CandidateSuggestionsRequestBody,  user_id: str = Depends(get_current_user_id)):
    """Get the candidate suggestions for the user."""
    logger.info("Get candidate suggestions entry point")
    response = await candidate_analysis_service.fetch_candidates_for_matching_job_description(request.job_description)
    logger.info("Get candidate suggestions exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )

@router.post("/get-candidate-suggestions-from-db")
async def get_candidate_suggestions_from_db(request: CandidateSuggestionsRequestBody,  user_id: str = Depends(get_current_user_id)):
    """Get the candidate suggestions for the user."""
    logger.info("Get candidate suggestions from db entry point")
    response = await candidate_analysis_service.fetch_candidates_from_db_for_matching_generating_job_description_score(request.job_description)
    logger.info("Get candidate suggestions from db exit point")
    return JSONResponse(
        content={"response": response}, status_code=response["status_code"]
    )

class GenerateMetadataForCandidatesRequestBody(BaseModel):
    number_of_candidates: int
    job_description: str
    compensation_range: str
    location: str


@router.post("/generate-metadata-for-candidates")
async def generate_metadata_for_candidates(background_tasks: BackgroundTasks, request: GenerateMetadataForCandidatesRequestBody, user_id: str = Depends(get_current_user_id)):
    """Generate metadata for the candidates."""
    logger.info("Generate metadata for candidates entry point")
    background_tasks.add_task(candidate_analysis_service.generate_metadata_of_candidates, number_of_candidates=request.number_of_candidates, job_description=request.job_description)
    logger.info("Generate metadata for candidates exit point")
    return JSONResponse(
        content={"response": "Metadata generation has been initiated."}, status_code=200
    )

@router.post("/select-candidates-for-matching")
async def select_candidates_for_matching(background_tasks: BackgroundTasks, request: CandidateSuggestionsRequestBody, user_id: str = Depends(get_current_user_id)):
    """Select the candidates for matching."""
    logger.info("Select candidates for matching entry point")
    background_tasks.add_task(candidate_analysis_service.select_candidates_for_matching, job_description=request.job_description)
    logger.info("Select candidates for matching exit point")
    return JSONResponse(
        content={"response": "Candidates selection has been initiated."}, status_code=200
    )
@router.get("/get-best-candidate")
async def get_best_candidate(job_description: str,background_task:BackgroundTasks,  user_id: str = Depends(get_current_user_id)):
    """Get the best candidate for the job description."""
    logger.info("Get best candidate entry point")
    background_task.add_task(candidate_analysis_service.get_the_top_candidate_for_jd, job_description=job_description)
    logger.info("Get best candidate exit point")
    return JSONResponse(
        content={"response": "Recieved"}, status_code=200
    )