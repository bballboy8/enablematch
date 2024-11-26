from utils import helper_functions
from logging_module import logger
from utils.thirdparty import gong_api_service
import json


async def analyze_candidate(job_description, call_id, salesforce_user_id):
    """Analyze the candidate based on job description and transcript."""
    try:
        # Salesforce Resume
        logger.info(f"Fetching resume content for candidate with salesforce_user_id {salesforce_user_id}")
        resume_response = await helper_functions.get_content_of_pdf_from_salesforce_user(salesforce_user_id)
        if resume_response.get("status_code") != 200:
            return resume_response       
        input_resume = resume_response["file_content"]
        logger.info(f"Resume content fetched successfully for candidate with salesforce_user_id {salesforce_user_id}")


        # Salesforce Notes
        logger.info(f"Fetching notes content for candidate with salesforce_user_id {salesforce_user_id}")
        notes_response = await helper_functions.get_salesforce_user_notes_first_record(salesforce_user_id)
        if notes_response.get("status_code") != 200:
            notes_response["notes"] = ""
        notes = notes_response["notes"]
        logger.info(f"Notes content fetched successfully for candidate with salesforce_user_id {salesforce_user_id}")
        
        # Gong Transcript
        conversation_summary = {}
        if call_id:
            logger.info(f"Analyzing candidate with call_id {call_id}")
            transcript = await gong_api_service.get_call_transcript_by_call_id(call_id)
            if transcript.get("status_code") == 500:
                return transcript
            formatted_transcript = ""
            call_transcripts = transcript["response"]["callTranscripts"]

            for i in range(len(call_transcripts)):
                transcript = call_transcripts[i]
                formatted_transcript_response = helper_functions.parse_transcript(transcript)
                if formatted_transcript_response.get("status_code") == 500:
                    continue
                # Summnarize the transcript
                summarized_conversation_response = await helper_functions.summarize_conversation(formatted_transcript_response["transcript"])
                if summarized_conversation_response.get("status_code") == 500:
                    continue

                formatted_transcript += summarized_conversation_response["response"]
                conversation_summary[call_transcripts[i]["callId"]] = summarized_conversation_response["response"]
            input_transcript = formatted_transcript
            logger.info(f"Transcript fetched successfully for candidate with call_id {call_id}")
        else:
            input_transcript = ""

        prompt = helper_functions.create_prompt(job_description, input_transcript, input_resume, notes)
        system_prompt = helper_functions.get_system_prompt()
        response = helper_functions.get_gpt_response(prompt, system_prompt)
        if response.get("status_code") == 500:
            return response
        raw_response = response.get('response', '')
        cleaned_json_string = raw_response.strip('```json').strip('```').strip()
        formatted_response = json.loads(cleaned_json_string)
        return {
            "response": formatted_response,
            "call_id": call_id,
            "salesforce_user_id": salesforce_user_id,
            "conversation_summary": conversation_summary,
            "status_code": 200,
            "message": "Candidate analysis completed successfully.",
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
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
