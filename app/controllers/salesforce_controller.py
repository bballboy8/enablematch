from fastapi import APIRouter, Depends, File, UploadFile
from logging_module import logger
from utils.dependencies import get_current_user_id
from services import salesforce_service
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter()




@router.get("/get-salesforce-data")
async def get_salesforce_data(query: str, user_id: str = Depends(get_current_user_id)):
    """Get data from Salesforce."""
    logger.info("Get Salesforce Data entry point")
    response = await salesforce_service.get_salesforce_data(query)
    logger.info("Get Salesforce Data exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.get("/get-salesforce-contacts")
async def get_salesforce_contacts(user_id: str = Depends(get_current_user_id)):
    """Get contacts from Salesforce."""
    logger.info("Get Salesforce Contacts entry point")
    response = await salesforce_service.get_salesforce_contacts()
    logger.info("Get Salesforce Contacts exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.post("/create-salesforce-contact")
async def create_salesforce_contact(full_name: str, email: str, user_id: str = Depends(get_current_user_id)):
    """Create a contact in Salesforce."""
    logger.info("Create Salesforce Contact entry point")
    response = await salesforce_service.create_salesforce_contact(full_name, email)
    logger.info("Create Salesforce Contact exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.post("/upload-resume")
async def upload_resume_to_a_user(file: UploadFile = File(...), record_id: Optional[str] = None, user_id: str = Depends(get_current_user_id)):
    """
    Endpoint to upload a file to Salesforce and link it to a record.
    
    Parameters:
    - record_id: Salesforce record ID to link the file to.
    - file: The file to upload.
    
    Returns:
    - The ContentDocumentId of the uploaded file.
    """
    logger.info("Upload Resume entry point")
    response = await salesforce_service.upload_resume_to_a_user(record_id, file)
    logger.info("Upload Resume exit point")
    return JSONResponse(content=response, status_code=200)

@router.get("/get-linked-files")
async def get_linked_files_from_salesforce(linked_entity_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Endpoint to get files linked to a specific record in Salesforce.
    
    Parameters:
    - linked_entity_id: Salesforce record/user ID.
    
    Returns:
    - List of files linked to the record/user.
    """
    logger.info("Get Linked Files entry point")
    response = await salesforce_service.get_linked_files_from_salesforce(linked_entity_id)
    logger.info("Get Linked Files exit point")
    return JSONResponse(content=response, status_code=response["status_code"])


@router.get("/download-file")
async def download_file_from_salesforce(content_document_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Endpoint to download a file from Salesforce.
    
    Parameters:
    - content_document_id: ContentDocumentId of the file.
    
    Returns:
    - File content.
    """
    logger.info("Download File entry point")
    response = await salesforce_service.download_file_from_salesforce(content_document_id)
    logger.info("Download File exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.get("/get-salesforce-user-first-document")
async def get_salesforce_user_first_document(salesforce_user_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Endpoint to get the first document linked to a specific user in Salesforce.
    
    Parameters:
    - salesforce_user_id: Salesforce user ID.
    
    Returns:
    - ContentDocumentId of the first document linked to the user.
    """
    logger.info("Get Salesforce User First Document entry point")
    response = await salesforce_service.get_salesforce_user_first_document(salesforce_user_id)
    logger.info("Get Salesforce User First Document exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.post("/attach-note-to-user")
async def attach_note_to_user( note_title: str, note_body: str, salesforce_user_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Endpoint to attach a note to a Salesforce in Salesforce.
    
    Parameters:
    - note_title: Title of the note.
    - note_body: Body of the note.
    - salesforce_user_id: Salesforce user ID.
    
    Returns:
    - Success message.
    """
    logger.info("Attach Note to Resume entry point")
    response = await salesforce_service.attach_note_to_salesforce_user(note_title, note_body, salesforce_user_id)
    logger.info("Attach Note to Resume exit point")
    return JSONResponse(content=response, status_code=response["status_code"])

@router.get("/get-salesforce-user-notes")
async def get_salesforce_user_notes(salesforce_user_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Endpoint to get notes attached to a specific user in Salesforce.
    
    Parameters:
    - salesforce_user_id: Salesforce user ID.
    
    Returns:
    - List of notes attached to the user.
    """
    logger.info("Get Salesforce User Notes entry point")
    response = await salesforce_service.get_salesforce_user_notes(salesforce_user_id)
    logger.info("Get Salesforce User Notes exit point")
    return JSONResponse(content=response, status_code=response["status_code"])