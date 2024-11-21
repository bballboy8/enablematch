from utils.thirdparty.salesforce_api_service import SalesforceApiService
from logging_module import logger


async def get_salesforce_data(query):
    """Get data from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        data = salesforce_instance.get_salesforce_data(query)
        if data:
            return {"response": data, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while fetching data from Salesforce.{data}",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while fetching Salesforce data: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce data.{e}",
            "status_code": 500,
        }
    
async def create_salesforce_contact(full_name,email):
    """Create a contact in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        data = salesforce_instance.create_salesforce_contact(full_name,email)
        if data:
            return {"response": data, "status_code": 200}
        else:
            return {
                "response": f"An error occurred while creating a contact in Salesforce.{full_name} {email}",
                "status_code": 500,
            }

    except Exception as e:
        logger.error(f"Error while creating Salesforce contact: {e}")
        return {
            "response": f"An error occurred while creating the Salesforce contact.{e}",
            "status_code": 500,
        }
    
async def get_salesforce_contacts():
    """Get contacts from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        contacts = salesforce_instance.get_salesforce_contacts()
        return {"response": contacts, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching Salesforce contacts: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce contacts: {e}",
            "status_code": 500,
        }
    
async def get_salesforce_contacts():
    """Get contacts from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        contacts = salesforce_instance.get_salesforce_contacts()
        return {"response": contacts, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching Salesforce contacts: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce contacts: {e}",
            "status_code": 500,
        }


async def upload_resume_to_a_user(record_id, file):
    """Upload a file to Salesforce and link it to a record."""
    try:
        salesforce_instance = SalesforceApiService()

        file_contents = await file.read()
        file_name = file.filename

        content_document_id = salesforce_instance.upload_file_to_salesforce(
            file_name=file_name, file_content=file_contents, linked_entity_id=record_id
        )
        return {
            "message": "File uploaded successfully",
            "content_document_id": content_document_id,
        }
    except Exception as e:
        logger.error(f"Error while uploading file to Salesforce: {e}")
        return {
            "message": f"An error occurred while uploading the file to Salesforce: {e}"
        }

async def get_linked_files_from_salesforce(linked_entity_id):
    """Get files linked to a specific record in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        files = salesforce_instance.get_linked_files(linked_entity_id)
        return {"response": files, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching linked files from Salesforce: {e}")
        return {
            "response": f"An error occurred while fetching linked files from Salesforce: {e}",
            "status_code": 500,
        }
    
async def download_file_from_salesforce(content_document_id):
    """Download a file from Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        file_content = salesforce_instance.download_file_from_salesforce(content_document_id)
        if file_content:
            with open("downloaded_file.pdf", "wb") as file:
                file.write(file_content["file_content"])

        return {"response": "Downloaded", "status_code": 200}
    except Exception as e:
        logger.error(f"Error while downloading file from Salesforce: {e}")
        return {
            "response": f"An error occurred while downloading the file from Salesforce: {e}",
            "status_code": 500,
        }
    
async def get_salesforce_user_first_document(salesforce_user_id):
    """Get the first document linked to a user in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        document = salesforce_instance.get_salesforce_user_first_document(salesforce_user_id)
        if document["status_code"] == 500:
            return document
        return {"response": document, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching the first document linked to the user: {e}")
        return {
            "response": f"An error occurred while fetching the first document linked to the user: {e}",
            "status_code": 500,
        }