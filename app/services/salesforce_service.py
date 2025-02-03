from utils.thirdparty.salesforce_api_service import SalesforceApiService
from logging_module import logger
from config.db_connection import db
from config import constants

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

async def attach_note_to_salesforce_user(note_title, note_body, linked_entity_id):
    """Attach a note to a resume in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        response = salesforce_instance.attach_note_to_salesforce_user(note_title, note_body, linked_entity_id)
        return {"response": response, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while attaching a note to the resume: {e}")
        return {
            "response": f"An error occurred while attaching a note to the resume: {e}",
            "status_code": 500,
        }


async def get_salesforce_user_notes(linked_entity_id):
    """Get notes attached to a specific record in Salesforce."""
    try:
        salesforce_instance = SalesforceApiService()
        notes = salesforce_instance.get_salesforce_user_notes(linked_entity_id)
        if notes["status_code"] == 500:
            return notes
        return {"response": notes["notes"], "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching notes from Salesforce: {e}")
        return {
            "response": f"An error occurred while fetching notes from Salesforce: {e}",
            "status_code": 500,
        }

async def get_salesforce_users():
    """Get users from Salesforce and insert only new users."""
    try:
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        salesforce_instance = SalesforceApiService()
        
        users = salesforce_instance.get_salesforce_users()
        users = users['users']

        # Extract Salesforce user IDs from the fetched users
        fetched_user_ids = {user['Id'] for user in users}
        
        # Find existing user IDs in the database
        existing_users = await salesforce_users_collection.find(
            {"Id": {"$in": list(fetched_user_ids)}},
            {"Id": 1}
        ).to_list(length=None)
        existing_user_ids = {user['Id'] for user in existing_users}
        
        # Filter out users that already exist in the database
        new_users = [
            user
            for user in users if user['Id'] not in existing_user_ids
        ]
        
        # Insert only new users
        if new_users:
            await salesforce_users_collection.insert_many(new_users)
        
        return {"response": "Synced succesfully", "status_code": 200}
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error while fetching Salesforce users: {e}")
        return {
            "response": f"An error occurred while fetching the Salesforce users: {e}",
            "status_code": 500,
        }
    
async def fetch_gong_records_by_salesforce_user_id(salesforce_user_id:str):
    """Fetch Gong records by Salesforce user ID."""
    try:
        salesforce_instance = SalesforceApiService()
        gong_records = salesforce_instance.fetch_gong_records_by_salesforce_user_id(salesforce_user_id)
        return {"response": gong_records, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching Gong records by Salesforce user ID: {e}")
        return {
            "response": f"An error occurred while fetching Gong records by Salesforce user ID: {e}",
            "status_code": 500,
        }
    

async def get_each_table_count():
    """Get count of each table."""
    try:
        salesforce_instance = SalesforceApiService()
        count = salesforce_instance.get_each_table_count()
        return {"response": count, "status_code": 200}
    except Exception as e:
        logger.error(f"Error while fetching count of each table: {e}")
        return {
            "response": f"An error occurred while fetching count of each table: {e}",
            "status_code": 500,
        }