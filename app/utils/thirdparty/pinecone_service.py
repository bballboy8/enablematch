from config import constants
from logging_module import logger
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import uuid
from utils.thirdparty.openai_service import OpenAIService
import uuid
from itertools import islice
from config.db_connection import db

class PineConeDBService:
    def __init__(self):
        """
        Initialize the Pinecone service with the API key from the constants file.
        """
        self.pinecone_client = Pinecone(
            api_key=constants.PINECONEDB_API_KEY
        )

    def reinitialize_pinecone_client(self):
        """
        Reinitialize the Pinecone client with the API key from the constants file.
        """
        self.pinecone_client = Pinecone(
            api_key=constants.PINECONEDB_API_KEY,
        )
        logger.info("Pinecone client reinitialized.")

    async def test_connection(self):
        """
        Test the Pinecone DB connection by listing indexes or checking API reachability.
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            response = self.pinecone_client.list_indexes()
            logger.info("Pinecone DB connection successful")
            return {"status_code": 200, "response": "Pinecone working properly"}
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone DB: {e}")
            return {"status_code": 500, "response": f"{e}"}

    async def create_index(self, index_name, dimension=1536, metric="cosine"):
        """
        Create a Pinecone index if it does not exist.
        Args:
            index_name (str): The name of the index.
            dimension (int): The dimensionality of the vectors.
            metric (str): Similarity metric (e.g., cosine, euclidean).
        Returns:
            dict: Response with status code and message.
        """
        try:
            existing_index = [
                index["name"] for index in self.pinecone_client.list_indexes()
            ]
            if index_name not in existing_index:
                self.pinecone_client.create_index(
                    index_name,
                    dimension=dimension,
                    metric=metric,
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info(f"Index {index_name} created successfully.")
                return {
                    "status_code": 200,
                    "response": f"Index '{index_name}' created.",
                }
            else:
                logger.info(
                    f"Index {index_name} already exists.",
                )
                return {
                    "status_code": 200,
                    "response": f"Index '{index_name}' already exists.",
                }
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return {"status_code": 500, "response": str(e)}

    
    async def upsert_data(self, data):
        """
        Embed and upsert data into the specified Pinecone index in batches of 100.
        
        Args:
            data (list[dict]): A list of dictionaries containing the records.
        
        Returns:
            dict: Response with status code and message.
        """
        try:
            index = self.pinecone_client.Index(constants.PINECONE_INDEX)

            async def process_batch(batch):
                upsert_list = []
                for record in batch:
                    if not isinstance(record, dict):
                        logger.warning(f"Skipping invalid record: {record}")
                        continue
                    record_id = record.get("id", str(uuid.uuid4()))
                    record_text = record.get("text")
                    embedding = await self._generate_embedding(record_text)

                    if embedding["status_code"] != 200:
                        return embedding
                    
                    logger.debug(f"Embedding generated for record {record_id}")
                    embedding_value = embedding["response"]
                    upsert_list.append(
                        {"id": record_id, "values": embedding_value, "metadata": {'id':record_id}}
                    )

                if upsert_list:
                    index.upsert(upsert_list)
                    logger.debug(f"{len(upsert_list)} records upserted.")

                    return {"status_code": 200, "response": f"{len(upsert_list)} records upserted."}
                return {"status_code": 400, "response": "No valid records to upsert."}

            def batch_generator(iterable, batch_size=10):
                it = iter(iterable)
                while batch := list(islice(it, batch_size)):
                    yield batch

            results = []
            for batch in batch_generator(data, 10):
                result = await process_batch(batch)
                results.append(result)

            return {"status_code": 200, "response": f"Total {sum(len(r['response'].split()[0]) for r in results if r['status_code'] == 200)} records upserted."}

        except Exception as e:
            logger.error(f"Error upserting data: {e}")
            return {"status_code": 500, "response": str(e)}


    async def query_data(self, query_text, top_k=3, index_name=None,  retry_count=0, max_retries=5):
        """
        Query the specified Pinecone index using a text query.
        Args:
            query_text (str): The query text.
            top_k (int): Number of top results to retrieve.
        Returns:
            dict: Response with status code and query results.
        """
        try:
            if index_name:
                index = self.pinecone_client.Index(index_name)
            else:
                index = self.pinecone_client.Index(constants.PINECONE_INDEX)
            query_embedding = await self._generate_embedding(query_text)
            if query_embedding["status_code"] != 200:
                return query_embedding
            query_embedding = query_embedding["response"]
            results = index.query(
                vector=query_embedding, top_k=top_k, include_metadata=True
            )

            if results.get("matches"):
                return {"status_code": 200, "response": results}

            return {"status_code": 404, "response": "No matching records found."}
        except Exception as e:
            logger.error(f"Failed to query index {constants.PINECONE_INDEX}: {e}")
            if "Max retries exceeded with url" in str(e):
                if retry_count < max_retries:
                    logger.info(f"Retrying query_data... Attempt {retry_count + 1}/{max_retries}")
                    self.reinitialize_pinecone_client()
                    return await self.query_data(query_text, top_k, index_name, retry_count + 1, max_retries)
                else:
                    logger.error("Max retries reached. Query failed.")
            return {"status_code": 500, "response": str(e)}

    async def _generate_embedding(self, text):
        """
        Generate an embedding for the given text using OpenAI's Embedding API.
        Args:
            text (str): The text to embed.
            engine (str): The embedding model to use.
        Returns:
            list: The embedding vector.
        """
        try:
            openai_client = OpenAIService()
            response = await openai_client.generate_text_embeddings(text)
            if response["status_code"] != 200:
                return response
            embeddings = response["embedding"]
            return {"status_code": 200, "response": embeddings}
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return {"status_code": 500, "response": str(e)}

    async def populate_cooked_records(self, cooked_record, index_name):
        try:
            if index_name:
                index = self.pinecone_client.Index(index_name)
            else:
                index = self.pinecone_client.Index(constants.PINECONE_INDEX)
            index.upsert(cooked_record)
            return {
                "status_code": 200,
                "response": "Record upserted",
            }
        except Exception as e:
            logger.error(f"Failed to Populate Cooked Record: {e}")
            return {"status_code": 500, "response": str(e)}
        
    async def create_new_index(self, index_name):
        try:
            logger.debug(f"Inside Create Knowledge Book Service:{index_name}")
            self.pinecone_client.create_index(
                index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            return {
                "status_code": 200,
                "response": f"Index '{index_name}' created.",
            }
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return {"status_code": 500, "response": str(e)}

    async def get_existing_indexes(self):
        try:
            existing_index = [
                index["name"] for index in self.pinecone_client.list_indexes()
            ]
            return {
                "status_code": 200,
                "response": existing_index,
            }
        except Exception as e:
            logger.error(f"Failed to get existing indexes: {e}")
            return {"status_code": 500, "response": str(e)}
        
    async def delete_index(self, index_name):
        try:
            self.pinecone_client.delete_index(index_name)
            return {
                "status_code": 200,
                "response": f"Index '{index_name}' deleted.",
            }
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return {"status_code": 500, "response": str(e)}