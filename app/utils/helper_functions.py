from datetime import datetime
from openai import OpenAI
from config import constants
from logging_module import logger
import pdfplumber
from services.salesforce_service import (
    get_salesforce_user_first_document,
    get_salesforce_user_notes,
)
from io import BytesIO

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
        transcript_sections = transcript_json.get("transcript", [])
        for section in transcript_sections:
            speaker_id = section.get("speakerId", "Unknown Speaker")
            sentences = section.get("sentences", [])
            for sentence in sentences:
                conversation_transcript += f"{speaker_id}: {sentence.get('text', '')}\n"
        return {"transcript": conversation_transcript.strip(), "status_code": 200}
    except Exception as e:
        return {
            "error": f"An error occurred while parsing the transcript: {e}",
            "status_code": 500,
        }


def create_prompt(
    job_description, conversation_transcript=None, resume_text=None, notes=None
):
    """Create a detailed GPT prompt using the job description, conversation transcript, and resume text."""

    prompt = f"""
            Here is a Job Description. Summarize the conversation and assess if the candidate is suitable for the role. 
            Provide your decision and the reasons. You need to put more weight on Resume Text, Notes and then Conversation Transcript to make a decision.

            Job Description:
            {job_description}
            """

    if resume_text:
        prompt += f"\n\nResume Text:\n{resume_text}"

    if conversation_transcript:
        prompt += f"\n\nConversation Transcript:\n{conversation_transcript}"

    if notes:
        prompt += f"\n\nNotes:\n{notes}"

    return prompt


def get_system_prompt():
    return f"""
        You are an expert Hiring Manager specializing in summarizing and analyzing conversations between candidates and hiring managers along with matching the resumes for the given job descriptions. Your goal is to:
        1. Go through the resume text, conversation transcript, and notes to evaluate the candidate's suitability for the role. Conversation Transcript and Notes are optional parameters; if they are not available, don't consider them.
        2. Focus on identifying tangible achievements, specific metrics, or concrete examples of the candidate's impact that align with the job description. If either the resume or the conversation transcript includes business metrics, prioritize them. If neither does, this is a notable issue. Both discussing metrics is more desirable.
        3. Cross-check the details in the resume with the conversation to spot inconsistencies or verify the depth of knowledge claimed.
        4. Consider the candidate's ability to explain their experiences and skills during the conversation. Depth of understanding and real-world application should be prioritized.
        5. Evaluate the candidate's communication abilities but assign it only 50% of the weight compared to other factors such as skills, experience, and alignment with the job requirements. Prioritize clarity and substance over interpersonal style.
        6. Pay special attention to the candidate's knowledge and experience with companies they've worked for. Match their previous company experience with the requirements of the job description. For example:
            - Experience in small companies should be valued for small company roles.
            - Experience in Specific Role focused companies should be highlighted.
        
        7. Provide a clear decision (Suitable, Not Suitable, or Requires Further Evaluation) and explain the reasons for your decision based on the conversation and role requirements.
        9. If the candidate lacks seniority, give them low scores. If they have seniority, give them a high score.

        Also, you need to look for the following points:
        1. Do the candidates refer to metrics (either in their resume or during the conversation)?
        2. Are they concise or long-winded?
        3. Do they minimize filler words?
        4. Do they demonstrate a business-oriented mindset relevant to the role (e.g., cybersecurity knowledge for a cybersecurity role)?

        Focus on evaluating the candidate's alignment with the job description, their overall suitability for the role, and the authenticity of their claims. 

        Your response should only be in RFC8259 compliant JSON format without deviation with the following keys:
        - response: The summary and evaluation of the candidate.
        - score: The score assigned to the candidate based on the evaluation out of 10.
        - decision: The final decision (Suitable, Not Suitable, Requires Further Evaluation).
        - reasons: The detailed reasons supporting your decision, including specific examples from the resume or conversation transcript.
        - comment: If someone doesn't get 10 out of 10, mention some comments on why they weren't a 10.
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


async def parse_pdf_file(resume):
    try:
        if not resume.filename.endswith(".pdf"):
            return {
                "error": "Invalid file format. Please upload a PDF file.",
                "status_code": 400,
            }

        resume_text = ""
        with pdfplumber.open(resume.file) as pdf:
            for page in pdf.pages:
                resume_text += page.extract_text() or ""

        return {"resume_text": resume_text, "status_code": 200}
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return {
            "error": "An error occurred while parsing the resume.",
            "status_code": 500,
        }


async def get_content_of_pdf_from_salesforce_user(salesforce_user_id):
    try:
        response = await get_salesforce_user_first_document(salesforce_user_id)

        if response.get("status_code") != 200:
            return response

        file_content_bytes = response["response"]["file_content"]

        file_content = ""
        with pdfplumber.open(BytesIO(file_content_bytes)) as pdf:
            for page in pdf.pages:
                file_content += page.extract_text() or ""

        return {"file_content": file_content, "status_code": 200}

    except Exception as e:
        logger.error(f"Error fetching file content from Salesforce: {e}", exc_info=True)
        return {
            "error": "An error occurred while fetching file content.",
            "status_code": 500,
        }


async def get_salesforce_user_notes_first_record(salesforce_user_id):
    try:
        response = await get_salesforce_user_notes(salesforce_user_id)

        if response.get("status_code") != 200:
            return response

        notes = response["response"]

        if len(notes) == 0:
            return {
                "error": "No notes found for the user.",
                "status_code": 404,
            }

        note_body = notes[0].get("Content", "")
        note_title = notes[0].get("Title", "")
        note_string = f"Note Title: {note_title}\nNote Body: {note_body}"

        return {"notes": note_string, "status_code": 200}

    except Exception as e:
        logger.error(f"Error fetching file content from Salesforce: {e}", exc_info=True)
        return {
            "error": "An error occurred while fetching file content.",
            "status_code": 500,
        }


async def summarize_conversation(conversation_transcript):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert summarizer. You are going to extract the Strength, Weakness, Overall how is the conversation for job role and summarize the conversation. You are going to be a bit more critical in your analysis. Also you need to look for following points 1. Do the candidates refer to metrics? 2. Are they concise or long winded? 3. Do they minimize filler words? 4. Do they talk like an executive?",
                },
                {"role": "user", "content": conversation_transcript},
            ],
        )
        finish_reason = response.choices[0].finish_reason
        response_data = response.choices[0].message.content
        return {
            "response": response_data,
            "finish_reason": finish_reason,
            "status_code": 200,
        }
    except Exception as e:
        return {
            "response": f"An error occurred while processing the request: {e}",
            "status_code": 500,
        }
