from utils import helper_functions
from logging_module import logger
from utils.thirdparty import gong_api_service
import json
from services import proxy_curl_service
from config.db_connection import db
from config import constants
import pandas as pd
from bson import ObjectId
from utils.thirdparty.pinecone_service import PineConeDBService
from datetime import datetime, date
from utils.thirdparty.openai_service import OpenAIService


async def analyze_database_candidate(job_description, db_id):
    try:
        logger.info(f"Processing record {db_id}")
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        targeted_candidates_collection = db[constants.TARGET_CANDIDATE_COLLECTION]
        candidate = await targeted_candidates_collection.find_one({"user_id": db_id}, {"_id": 0})
        if not candidate:
            return None
        notes = ""
        salesforce_notes = await salesforce_users_collection.find_one({"_id": ObjectId(db_id)}, {"Summary_of_Candidate__c": 1})
        if salesforce_notes:
            notes = salesforce_notes.get("Summary_of_Candidate__c", "")

        input_transcript = candidate.get("conversation_summary", "")
        input_resume = candidate.get("input_resume", "")
        prompt = helper_functions.create_prompt(job_description, input_transcript, input_resume, notes, "linkedin")
        system_prompt = helper_functions.get_system_prompt()

        response = await asyncio.to_thread(helper_functions.get_gpt_response, prompt, system_prompt)

        if response.get("status_code") == 500:
            logger.error(f"Error processing record {db_id}: {response['response']}")
            return None

        raw_response = response.get('response', '')
        cleaned_json_string = raw_response.strip('```json').strip('```').strip()
        formatted_response = json.loads(cleaned_json_string)
        candidate["gpt_response"] = formatted_response
        # Delete input_resume and conversation_summary
        del candidate["input_resume"]
        del candidate["conversation_summary"]
        logger.info(f"Record {db_id} processed successfully")
        return {"status_code": 200, "response": candidate}
    except Exception as e:
        logger.error(f"Error in analyzing database candidate: {e}")
        return {
            "response": f"An error occurred while analyzing the database candidate: {e}",
            "status_code": 500,
        }


async def analyze_candidate(job_description, call_id, salesforce_user_id, linkedin_profile_url=None):
    """Analyze the candidate based on job description and transcript."""
    try:
        # Salesforce Resume
        source = 'LinkedIn' if linkedin_profile_url else 'Resume'
        # LinkedIn Profile
        if linkedin_profile_url:
            logger.info(f"Fetching resume content for candidate with linkedin_profile_url {linkedin_profile_url}")
            resume_response = await proxy_curl_service.get_linkedin_person(linkedin_profile_url)
            if resume_response.get("status_code") != 200:
                return resume_response
            input_resume = await proxy_curl_service.get_key_value_concatenation(resume_response["data"])
            input_resume = f"Source: LinkedIn\n{input_resume}"
            logger.info(f"Linkedin content fetched successfully for candidate with linkedin_profile_url {linkedin_profile_url}")

        else:
            logger.info(f"Fetching resume content for candidate with salesforce_user_id {salesforce_user_id}")
            resume_response = await helper_functions.get_content_of_pdf_from_salesforce_user(salesforce_user_id)
            if resume_response.get("status_code") != 200:
                return resume_response       
            input_resume = resume_response["file_content"]
            input_resume = f"Source: Resume\n{input_resume}"
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
                summarized_conversation_response = await helper_functions.summarize_conversation(formatted_transcript_response["transcript"], input_resume)
                if summarized_conversation_response.get("status_code") == 500:
                    continue

                formatted_transcript += summarized_conversation_response["response"]
                conversation_summary[call_transcripts[i]["callId"]] = summarized_conversation_response["response"]
            input_transcript = formatted_transcript
            logger.info(f"Transcript fetched successfully for candidate with call_id {call_id}")
        else:
            input_transcript = ""

        prompt = helper_functions.create_prompt(job_description, input_transcript, input_resume, notes, source ) 
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

async def process_transcript_by_id(transcript_id):
    try:
        logger.info(f"Processing transcript by id: {transcript_id}")
        transcript = await db[constants.USERS_GONG_TRANSCRIPT_COLLECTION].find_one({"_id": ObjectId(transcript_id)})
        if not transcript:
            return
        transcript_text = transcript.get("transcript", "")
        if "conversation_summary" in transcript:
            return
        conversation_summary = await helper_functions.generate_skills_and_strength_of_candidate(transcript_text)
        if conversation_summary.get("status_code") == 500:
            return
        await db[constants.USERS_GONG_TRANSCRIPT_COLLECTION].update_one(
            {"_id": ObjectId(transcript_id)},
            {"$set": {"conversation_summary": conversation_summary["response"]}},
        )
        logger.info(f"Conversation summary generated for transcript by id: {transcript_id}")
    except Exception as e:
        logger.error(f"Error in processing transcript by id: {e}")
        return {
            "response": f"An error occurred while processing transcript by id: {e}",
            "status_code": 500,
        }

import asyncio
async def generate_conversation_summary():
    try:
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        users = await salesforce_users_collection.find({"gong_transcript_ids": {"$exists": True}}).to_list(length=None)
        if not users:
            return {
                "response": "User not found.",
                "status_code": 404,
            }
        for i, user in enumerate(users):
            gong_transcript_ids = user.get("gong_transcript_ids", [])
            print(f"Lenght of gong_transcript_ids: {len(gong_transcript_ids)}")
            await asyncio.gather(*[process_transcript_by_id(transcript_id) for transcript_id in gong_transcript_ids])

            logger.info(f"Conversation summary generated for {i+1} users.")

        return {
            "response": "Conversation summary generated successfully.",
            "status_code": 200,
        }
    except Exception as e:
        logger.error(f"Error in generating conversation summary: {e}")
        return {
            "response": f"An error occurred while generating conversation summary: {e}",
            "status_code": 500,
        }


async def fetch_target_candidates():
    try:
        logger.info("Fetching target candidates")
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        target_candidates_collection = db[constants.TARGET_CANDIDATE_COLLECTION]
        users_gong_transcript_collection = db[
            constants.USERS_GONG_TRANSCRIPT_COLLECTION
        ]
        users_linkedin_profile_collection = db[
            constants.USERS_LINKEDIN_PROFILE_COLLECTION
        ]

        users = await salesforce_users_collection.find(
            {
                "gong_transcript_ids": {"$exists": True},
                "linkedin_profile": {"$exists": True},
            }
        ).to_list(None)
        if not users:
            return {
                "response": "User not found.",
                "status_code": 404,
            }
        logger.info(f"Total users found: {len(users)}")

        target_candidates = []
        for i, user in enumerate(users):
            gong_transcript_ids = user.get("gong_transcript_ids", [])
            conversation_summary = []
            for transcript_id in gong_transcript_ids:
                transcript = await users_gong_transcript_collection.find_one(
                    {"_id": ObjectId(transcript_id)}
                )
                if not transcript:
                    continue
                conversation_summary.append(transcript.get("conversation_summary", ""))
            user_profile = await users_linkedin_profile_collection.find_one(
                {"_id": ObjectId(user.get("linkedin_profile", ""))}
            )
            if not user_profile:
                continue
            input_resume = await proxy_curl_service.get_key_value_concatenation(
                user_profile
            )
            target_candidates.append(
                {
                    "user_id": str(user.get("_id", "")),
                    "conversation_summary": " ".join(conversation_summary),
                    "input_resume": input_resume,
                }
            )

        cooked_target_candidates = []
        for candidate in target_candidates:
            metadata = {
                "conversation_summary": candidate["conversation_summary"],
                "input_resume": candidate["input_resume"],
            }
            text = metadata["conversation_summary"] + metadata["input_resume"]
            cooked_target_candidates.append(
                {"id": candidate["user_id"], "text": text, "metadata": metadata}
            )
            if not await target_candidates_collection.find_one(
                {"id": candidate["user_id"]}
            ):
                await target_candidates_collection.insert_one(candidate)


        logger.info("Target candidates fetched successfully.")
        return {
            "response": target_candidates,
            "status_code": 200,
        }
    except Exception as e:
        logger.error(f"Error in fetching target candidates: {e}")
        return {
            "response": f"An error occurred while fetching target candidates: {e}",
            "status_code": 500,
        }

async def upload_cooked_records_to_pinecone():
    try:
        pinecone_client = PineConeDBService()
        target_candidates_collection = db[constants.TARGET_CANDIDATE_COLLECTION]
        target_candidates = await target_candidates_collection.find({}).to_list(None)
        cooked_target_candidates = []
        for candidate in target_candidates:
            metadata = {
                "conversation_summary": candidate["conversation_summary"],
                "input_resume": candidate["input_resume"],
            }
            text = metadata["conversation_summary"] + metadata["input_resume"]
            cooked_target_candidates.append(
                {"id": candidate["user_id"], "text": text, "metadata": metadata}
            )
        logger.info("Uploading cooked records to Pinecone")
        await pinecone_client.upsert_data(cooked_target_candidates)
    except Exception as e:
        logger.error(f"Error in uploading cooked records to Pinecone: {e}")
        return {
            "response": f"An error occurred while uploading cooked records to Pinecone: {e}",
            "status_code": 500,
        }
    
import asyncio

import asyncio
import json

async def process_record(record, job_description):
    try:
        logger.info(f"Processing record {record['id']}")
        targeted_candidates_collection = db[constants.TARGET_CANDIDATE_COLLECTION]
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        record_id = record["id"]
        candidate = await targeted_candidates_collection.find_one({"user_id": record_id}, {"_id": 0})
        if not candidate:
            return None
        
        notes = ""
        salesforce_notes = await salesforce_users_collection.find_one({"_id": ObjectId(record_id)}, {"Summary_of_Candidate__c": 1})
        if salesforce_notes:
            notes = salesforce_notes.get("Summary_of_Candidate__c", "")

        candidate["exp"] = record["experience_years"]
        input_transcript = candidate.get("conversation_summary", "")
        input_resume = candidate.get("input_resume", "")
        prompt = helper_functions.create_prompt(job_description, input_transcript, input_resume, notes, "linkedin")
        system_prompt = helper_functions.get_system_prompt()
        system_prompt += f"Candidate Actual Experience: {record['experience_years']} years\n"
        response = await asyncio.to_thread(helper_functions.get_gpt_response, prompt, system_prompt)

        if response.get("status_code") == 500:
            logger.error(f"Error processing record {record_id}: {response['response']}")
            return None

        raw_response = response.get('response', '')
        cleaned_json_string = raw_response.strip('```json').strip('```').strip()
        formatted_response = json.loads(cleaned_json_string)
        candidate["gpt_response"] = formatted_response
        # Delete input_resume and conversation_summary
        del candidate["input_resume"]
        del candidate["conversation_summary"]
        logger.info(f"Record {record_id} processed successfully")
        return candidate
    except Exception as e:
        logger.error(f"Error processing record {record_id}: {e}")
        return None


def merge_intervals(intervals):
    intervals.sort()
    merged = []
    
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    
    return merged

def calculate_work_experience(experiences):
    current_date = date.today()
    intervals = []
    
    for exp in experiences:
        start = exp.get('starts_at')
        if start is None:
            continue
        end = exp.get('ends_at') or {'day': current_date.day, 'month': current_date.month, 'year': current_date.year}
        
        start_date = date(start['year'], start['month'], start['day'])
        end_date = date(end['year'], end['month'], end['day'])
        
        intervals.append((start_date, end_date))
    
    merged_intervals = merge_intervals(intervals)
    total_days = sum((end - start).days for start, end in merged_intervals)
    
    return total_days / 365

async def fetch_candidates_from_db_for_matching_generating_job_description_score(job_description):
    try:
        target_candidates_collection = db[constants.TARGET_CANDIDATE_COLLECTION]
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        users_linkedin_profile_collection = db[constants.USERS_LINKEDIN_PROFILE_COLLECTION]
        target_candidates = await target_candidates_collection.find({}).to_list(None)

        openai_client = OpenAIService()
        response = await openai_client.get_experience_required(job_description)
        if response["status_code"] != 200:
            return response
        experience_required = (response.get("experience_required", "0-4")).split("-")
        min_experience = int(experience_required[0])
        max_experience = int(experience_required[1])
        print(min_experience, max_experience)
        query_result = []
        for candidate in target_candidates:
            try:
                salesforce_user = await salesforce_users_collection.find_one({"_id": ObjectId(candidate["user_id"])})
                if not salesforce_user:
                    continue
                linkedin_profile = salesforce_user.get("linkedin_profile", "")
                user_profile = await users_linkedin_profile_collection.find_one({"_id": ObjectId(linkedin_profile)})
                if not user_profile:
                    continue
                experience_years = [ {'starts_at': experience.get("starts_at"), "ends_at": experience.get("ends_at"), "company" : experience.get("company")} for experience in user_profile.get('experiences', [])]
                experience_years = calculate_work_experience(experience_years)
                if experience_years < min_experience or experience_years > max_experience:
                    continue

                query_result.append({
                    "id": str(salesforce_user["_id"]),
                    "experience_years": experience_years
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Error processing record {candidate['user_id']}: {e}")
                continue

        query_result = sorted(query_result, key=lambda x: x["experience_years"], reverse=True)
        print(query_result, len(query_result))

        tasks = [process_record(record, job_description) for record in query_result]
        results = await asyncio.gather(*tasks)
        # Filter out None results
        query_result = [res for res in results if res]
        # Convert to DataFrame
        df = pd.DataFrame(query_result)
        # Define file name with timestamp
        file_name = f"candidate_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        # Save DataFrame to an Excel file
        df.to_excel(file_name, index=False)
        return {"status_code": 200, "response": query_result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to query Pinecone index: {e}")
        return {"status_code": 500, "response": str(e)}


async def fetch_candidates_for_matching_job_description(job_description):
    try:
        pinecone_client = PineConeDBService()
        response = await pinecone_client.query_data(job_description, 100)

        if response["status_code"] != 200:
            return response

        records = [record for record in response["response"]["matches"]]
        query_result = []
        tasks = [process_record(record, job_description) for record in records]
        results = await asyncio.gather(*tasks)
        # Filter out None results
        query_result = [res for res in results if res]

          # Convert to DataFrame
        df = pd.DataFrame(query_result)

        # Define file name with timestamp
        file_name = f"candidate_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Save DataFrame to an Excel file
        df.to_excel(file_name, index=False)

        return {"status_code": 200, "response": query_result}

    except Exception as e:
        logger.error(f"Failed to query Pinecone index: {e}")
        return {"status_code": 500, "response": str(e)}


async def generate_metadata_of_candidates(number_of_candidates: int):
    try:
        logger.info("Fetching target candidates")
        openai_client = OpenAIService()
        salesforce_users_collection = db[constants.SALESFORCE_USERS_COLLECTION]
        users_gong_transcript_collection = db[
            constants.USERS_GONG_TRANSCRIPT_COLLECTION
        ]
        users_linkedin_profile_collection = db[
            constants.USERS_LINKEDIN_PROFILE_COLLECTION
        ]

        users = await salesforce_users_collection.find(
            {
                "gong_transcript_ids": {"$exists": True},
                "linkedin_profile": {"$exists": True},
            }
        ).to_list(length=number_of_candidates)

        if not users:
            return {
                "response": "User not found.",
                "status_code": 404,
            }
        logger.info(f"Total users found: {len(users)}")

        target_candidates = []
        for i, user in enumerate(users):
            gong_transcript_ids = user.get("gong_transcript_ids", [])
            conversation_summary = []
            for transcript_id in gong_transcript_ids:
                transcript = await users_gong_transcript_collection.find_one(
                    {"_id": ObjectId(transcript_id)}
                )
                if not transcript:
                    continue
                conversation_summary.append(transcript.get("transcript", ""))
            user_profile = await users_linkedin_profile_collection.find_one(
                {"_id": ObjectId(user.get("linkedin_profile", ""))}
            )
            if not user_profile:
                continue

            experience_years = [ {'starts_at': experience.get("starts_at"), "ends_at": experience.get("ends_at"), "company" : experience.get("company")} for experience in user_profile.get('experiences', [])]
            
            experience_years = calculate_work_experience(experience_years)
            
            print(experience_years)

            input_resume = await proxy_curl_service.get_key_value_concatenation(
                user_profile
            )

            input_resume = f"Total Experience: {experience_years} years\n{input_resume}"

            text_blob = " ".join(conversation_summary) + input_resume

            response = await openai_client.generate_metadata_via_ai(text_blob)
            print(response)
            if response["status_code"] != 200:
                continue

            metadata = json.loads(response["metadata"])
            target_candidates.append(
                {
                    "user_id": str(user.get("_id", "")),
                    "metadata": metadata,
                    "experience_years": experience_years
                }
            )

        return {
            "response": target_candidates,
            "status_code": 200,
        }
    except Exception as e:
        logger.error(f"Error in fetching target candidates: {e}")
        return {
            "response": f"An error occurred while fetching target candidates: {e}",
            "status_code": 500,
        }