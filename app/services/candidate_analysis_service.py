from utils import helper_functions
from logging_module import logger


async def analyze_candidate(job_description, transcript_json):
    """Analyze the candidate based on job description and transcript."""
    try:
        transcript = helper_functions.parse_transcript(transcript_json)
        if transcript.get("status_code") == 500:
            return transcript
        prompt = helper_functions.create_prompt(job_description, transcript)
        response = helper_functions.get_gpt_response(prompt)
        if response.get("status_code") == 500:
            return response
        return {"response": response, "status_code": 200}
    except Exception as e:
        logger.error(f"Error in analyzing candidate: {e}")
        return {
            "response": f"An error occurred while analyzing the candidate.{e}",
            "status_code": 500,
        }


async def test_gpt(user_id):
    """Test the GPT API by sending a sample prompt."""
    try:
        logger.info(f"Testing GPT API by {user_id}")
        response = helper_functions.test_gpt()
        return {"response": response, "status_code": 200}
    except Exception as e:
        logger.error(f"Error in testing GPT API: {e}")
        return {
            "response": f"An error occurred while testing the GPT API: {e}",
            "status_code": 500,
        }
