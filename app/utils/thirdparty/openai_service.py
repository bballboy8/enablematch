from logging_module import logger
from openai import OpenAI
from config import constants


class OpenAIService:
    def __init__(self):
        """
        Initialize the OpenAI service with the API key from the constants file.
        """
        self.openai_client = OpenAI(
            api_key=constants.OPENAI_API_KEY,
        )

    async def get_gpt_response(self, prompt: str, system_prompt: str) -> dict:
        """
        Send the prompt to the GPT API asynchronously and return the response.

        Args:
            prompt (str): The user's input prompt for the GPT model.
            system_prompt (str): The system prompt that sets the context or behavior for GPT.

        Returns:
            dict: A dictionary containing the GPT response, finish reason, token usage, and status code.
            Keys:
                - response (str): The GPT model's response.
                - finish_reason (str): The reason why the generation ended (e.g., 'stop', 'length').
                - prompt_tokens (int): Number of tokens in the input prompt.
                - completion_tokens (int): Number of tokens in the generated response.
                - status_code (int): HTTP-like status code (200 for success, 500 for error).
        """
        try:
            logger.info("Sending prompt to OpenAI GPT API...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            if "errors" in response:
                logger.error(
                    f"An error occurred while processing the request: {response['errors']}"
                )
                return {
                    "response": f"An error occurred while processing the request: {response['errors']}",
                    "status_code": 500,
                }
            finish_reason = response.choices[0].finish_reason
            response_data = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            return {
                "response": response_data,
                "finish_reason": finish_reason,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "status_code": 200,
            }
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {e}")
            return {
                "response": f"An error occurred while processing the request: {e}",
                "status_code": 500,
            }

    async def test_openai_for_chat_completion(self):
        """
        Test the GPT API for Chat Completion asynchronously by sending a sample prompt.

        Returns:
            str: A formatted string containing the GPT model's response, reason for completion,
            and token usage, or an error message if the request fails.
        """
        try:
            prompt = "Hi there! How are you doing today?"
            system_prompt = "You are an expert conversationalist. Please respond to the user's message with a friendly greeting."
            response = await self.get_gpt_response(prompt, system_prompt)
            if response["status_code"] == 500:
                return response

            message = (
                f"Response from Model: {response['response']}\n"
                f"Reason for completion: {response['finish_reason']}\n"
                f"Prompt tokens: {response['prompt_tokens']}\n"
                f"Completion tokens: {response['completion_tokens']}"
            )
            return {"message": message, "status_code": 200}
        except Exception as e:
            logger.error(f"An error occurred while testing the OpenAI API: {e}")
            return {
                "message": f"An error occurred while testing the OpenAI API: {e}",
                "status_code": 500,
            }

    async def generate_text_embeddings(self, text):
        try:
            embedding_model = constants.EMBEDDING_MODEL
            response = self.openai_client.embeddings.create(
                input=text,
                model=embedding_model
            )
            return {"status_code": 200 , "embedding": response.data[0].embedding}
        except Exception as e:
            logger.error(f"An error occurred while Generating the embeddings via API: {e}")
            return {
                "message": f"An error occurred while Generating the embeddings via OpenAI API: {e}",
                "status_code": 500,
            }
        
    async def get_experience_required(self, job_description):
        try:
            prompt = f"""
                Extract the required years of experience from the job description.  
                If a range is explicitly mentioned, return it as is.  
                If only a minimum or maximum experience is mentioned, infer the missing value based on the job description.  
                If no experience is specified, estimate a reasonable range based on the role and responsibilities.  

                **Output format:**  
                Strictly return the result in the format: `min-max` (e.g., `3-5`, `5-10`).  

                **Job Description:**  
                {job_description}
                """

            system_prompt = "Extract the minimum and maximum years of experience required from the job description and return it strictly in the 'min-max' format. If a single number is mentioned, assume it as the minimum and infer the maximum based on context."
            response = await self.get_gpt_response(prompt, system_prompt)
            if response["status_code"] == 500:
                return response
            return {"experience_required": response["response"], "status_code": 200}
        except Exception as e:
            logger.error(f"An error occurred while getting the experience required: {e}")
            return {
                "message": f"An error occurred while getting the experience required: {e}",
                "status_code": 500,
            }