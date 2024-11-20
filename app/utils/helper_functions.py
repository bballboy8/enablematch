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
        conversation_transcript = ""
        call_transcripts = transcript_json.get("callTranscripts", [])
        for call_entry in call_transcripts:
            transcript_sections = call_entry.get("transcript", [])
            for section in transcript_sections:
                speaker_id = section.get("speakerId", "Unknown Speaker")
                sentences = section.get("sentences", [])
                for sentence in sentences:
                    conversation_transcript += (
                        f"{speaker_id}: {sentence.get('text', '')}\n"
                    )

        return {"transcript": conversation_transcript.strip(), "status_code": 200}
    except Exception as e:
        return {
            "error": f"An error occurred while parsing the transcript: {e}",
            "status_code": 500,
        }


def create_prompt(job_description, conversation_transcript):
    """Create a detailed GPT prompt using the job description and transcript."""
    return f"""
            Here is a conversation transcript between a candidate and a hiring manager, along with the job description. Summarize the conversation and assess if the candidate is suitable for the role. Provide your decision and the reasons.

            Job Description:
            {job_description}

            Conversation Transcript:
            {conversation_transcript}
            """


def get_system_prompt():
    return f"""

        You are an expert job evaluator specializing in summarizing and analyzing conversations between candidates and hiring managers. Your goal is to:
        1. Generate a concise summary of the conversation, highlighting key points about the candidate's skills, experiences, and communication abilities.
        2. Assess whether the candidate is a good fit for the given role description.
        3. Provide a clear decision (Suitable, Not Suitable, or Requires Further Evaluation) and explain the reasons for your decision based on the conversation and role requirements.
        Focus on evaluating the candidate's alignment with the job description and their overall suitability for the role.
        Your response should be professional, detailed, and well-structured to help the hiring manager make an informed decision.
        Your response should consist of a dictionary with the following keys
        - response: The summary and evaluation of the candidate.
        - score: The score assigned to the candidate based on the evaluation.
        - decision: The final decision (Suitable, Not Suitable, Requires Further Evaluation).
        - reasons: The detailed reasons supporting your decision.
        And should be parsed in the following format:
        response:**Summary and evaluation of the candidate**
        score:**Score assigned to the candidate**
        decision:**Final decision**
        reasons:**Detailed reasons supporting your decision**
    """


def get_gpt_response(prompt, system_prompt):
    """Send the prompt to GPT API and return the response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
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
    system_prompt = "You are an expert conversationalist. Please respond to the user's message with a friendly greeting"
    response = get_gpt_response(prompt, system_prompt)
    if response["status_code"] == 500:
        return response
    response = f"Response from Mode: {response['response']} Reason for completion: {response['finish_reason']} Prompt tokens: {response['prompt_tokens']} Completion tokens: {response['completion_tokens']}"
    return response
