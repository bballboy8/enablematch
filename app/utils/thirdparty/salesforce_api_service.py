from config import constants
from simple_salesforce import Salesforce
from logging_module import logger

class SalesforceApiService:
    def __init__(self):
        self.sf = Salesforce(
            username=constants.SALESFORCE_USERNAME,
            password=constants.SALESFORCE_PASSWORD,
            security_token=constants.SALESFORCE_SECURITY_TOKEN,
            domain=constants.SALESFORCE_DOMAIN
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
    
    def create_salesforce_data(self, object_name, data):
        """
            Example data: { 'Name': 'Test Account', 'Phone': '1234567890' }
        """
        return self.sf.object_name.create(data) 




