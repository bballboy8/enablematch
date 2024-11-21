from config import constants
from simple_salesforce import Salesforce
from logging_module import logger
import requests
import base64


class SalesforceApiService:
    def __init__(self):
        self.sf = Salesforce(
            username=constants.SALESFORCE_USERNAME,
            password=constants.SALESFORCE_PASSWORD,
            security_token=constants.SALESFORCE_SECURITY_TOKEN,
            domain=constants.SALESFORCE_DOMAIN,
        )

    def get_salesforce_data(self, query):
        """
        Example query: SELECT Id, Name FROM Account
        """
        return self.sf.query_all(query)

    def get_salesforce_data_by_id(self, object_name, object_id):
        """
        Example query: SELECT Id, Name FROM Account WHERE Id = '0012w00000e2Z
        """
        return self.sf.query(f"SELECT * FROM {object_name} WHERE Id = '{object_id}'")

    def create_salesforce_contact(self, full_name, email):
        """
        Example contact_data: {"LastName": "John Doe", "Email": "example@gmail.com"}
        """
        contact_data = {"LastName": full_name, "Email": email}
        return self.sf.Contact.create(contact_data)

    def get_salesforce_contacts(self):
        return self.sf.query_all("SELECT Id, Name, Email FROM Contact")

    def upload_file_to_salesforce(self, file_name, file_content, linked_entity_id):
        """
        Uploads a file to Salesforce and links it to a specific record.

        :param file_name: Name of the file to upload.
        :param file_content: Content of the file in binary format.
        :param linked_entity_id: Salesforce record ID to link the file to.
        :return: ContentDocumentId of the uploaded file.
        """
        try:
            encoded_content = base64.b64encode(file_content).decode("utf-8")
            content_version = {
                "Title": file_name.split(".")[0],
                "PathOnClient": file_name,
                "VersionData": encoded_content,
            }

            content_version_response = self.sf.ContentVersion.create(content_version)

            content_document_id = self.sf.query(
                f"SELECT ContentDocumentId FROM ContentVersion WHERE Id = '{content_version_response['id']}'"
            )["records"][0]["ContentDocumentId"]

            self.sf.ContentDocumentLink.create(
                {
                    "ContentDocumentId": content_document_id,
                    "LinkedEntityId": linked_entity_id,
                    "ShareType": "V",
                    "Visibility": "AllUsers",
                }
            )

            return content_document_id
        except Exception as e:
            logger.error(f"Error uploading file to Salesforce: {e}")
            return None

    def get_linked_files(self, linked_entity_id):
        """
        Get files linked to a specific record in Salesforce.

        :param linked_entity_id: Salesforce record ID.
        :return: List of files linked to the record.
        """
        try:
            query = f"SELECT ContentDocumentId FROM ContentDocumentLink WHERE LinkedEntityId = '{linked_entity_id}'"
            content_document_links = self.sf.query(query)["records"]
            content_document_ids = [
                link["ContentDocumentId"] for link in content_document_links
            ]

            files = []
            for content_document_id in content_document_ids:
                file_info = self.sf.query(
                    f"SELECT Id, Title FROM ContentDocument WHERE Id = '{content_document_id}'"
                )["records"][0]
                files.append(file_info)
            return files
        except Exception as e:
            logger.error(f"Error fetching linked files from Salesforce: {e}")
            return None

    def download_file_from_salesforce(self, content_document_id):
        """
        Download a file from Salesforce.

        :param content_document_id: ContentDocumentId of the file.
        :return: File content.
        """
        try:
            query = f"SELECT VersionData FROM ContentVersion WHERE ContentDocumentId = '{content_document_id}'"
            version_data_url = self.sf.query(query)["records"][0]["VersionData"]

            base_url = self.sf.sf_instance
            full_url = f"https://{base_url}{version_data_url}"

            headers = {"Authorization": f"Bearer {self.sf.session_id}"}
            response = requests.get(full_url, headers=headers)
            if response.status_code == 200:
                return {"file_content": response.content, "status_code": 200}
            else:
                return {
                    "message": "Error downloading file from Salesforce",
                    "status_code": 500,
                }
        except Exception as e:
            logger.error(f"Error downloading file from Salesforce: {e}")
            return None
