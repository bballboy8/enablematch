from datetime import datetime
from openai import OpenAI
from config import constants

client = OpenAI(
    api_key=constants.OPENAI_API_KEY,
)

def convert_datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def convert_object_datetime_keys_to_str(obj):
    if isinstance(obj, dict):
        return {str(k): convert_datetime_to_str(v) for k, v in obj.items()}
    return obj


def parse_transcript(transcript_json):
    """Extract and combine transcript text from JSON data."""
    try:
        transcript = ""
        for entry in transcript_json.get("callTranscripts", []):
            for section in entry.get("transcript", []):
                for sentence in section.get("sentences", []):
                    transcript += sentence["text"] + " "
        return {"transcript": transcript.strip(), "status_code": 200}
    except Exception as e:
        return {"error": f"An error occurred while parsing the transcript: {e}", "status_code": 500}


def create_prompt(job_description, transcript):
    """Create a detailed GPT prompt using the job description and transcript."""
    return f"""
            You are a job interviewer. Based on the following job description and candidate transcript, assess if the candidate is a good fit.

            Job Description:
            {job_description}

            Candidate Transcript:
            {transcript}

            Evaluate the candidate's communication skills, technical abilities, and alignment with the job role. Provide a detailed assessment and your recommendation.
            """


def get_gpt_response(prompt):
    """Send the prompt to GPT API and return the response."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert job interviewer."},
                {"role": "user", "content": prompt}
            ]
        )
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
        return {
            "response": f"An error occurred while processing the request: {e}",
            "status_code": 500,
        }

def test_gpt():
    """Test the GPT API by sending a sample prompt."""
    prompt = "Hi there! How are you doing today?"
    response = get_gpt_response(prompt)
    if response["status_code"] == 500:
        return response
    response = f"Response from Mode: {response['response']} Reason for completion: {response['finish_reason']} Prompt tokens: {response['prompt_tokens']} Completion tokens: {response['completion_tokens']}"
    return response