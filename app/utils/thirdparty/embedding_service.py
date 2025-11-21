"""
Embedding Service using OpenAI.
"""
from logging_module import logger
from config import constants
from openai import AsyncOpenAI


class EmbeddingService:
    """
    Embedding service using OpenAI API.
    Supports: text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002
    """
    
    def __init__(self, model: str = None):
        """
        Initialize OpenAI embedding service.
        
        Args:
            model: Model name. If None, uses default from constants.
        """
        self.openai_client = AsyncOpenAI(api_key=constants.OPENAI_API_KEY)
        self.model = model or constants.EMBEDDING_MODEL
        logger.info(f"Initialized OpenAI embedding service with model: {self.model}")
    
    async def generate_embedding(self, text: str) -> dict:
        """
        Generate embedding for given text using OpenAI.
        
        Args:
            text: Input text to embed
            
        Returns:
            dict with status_code and embedding
        """
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model=self.model
            )
            return {
                "status_code": 200,
                "embedding": response.data[0].embedding
            }
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return {
                "status_code": 500,
                "message": f"OpenAI embedding error: {e}"
            }
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        Useful for vector database configuration.
        """
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return dimensions.get(self.model, 1536)
