from logging_module import logger
from openai import OpenAI
from config import constants
import re
import json

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
                model="o4-mini",
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

    async def generate_metadata_via_ai(self, text_blob, experience_years, senior_level_years):
        try:
            system_prompt = """
                            You are an advanced Hiring Manager AI specializing in extracting structured candidate evaluation attributes from resumes and Gong transcripts of a candidate. Given unstructured input data, your task is to identify and extract key attributes into a structured JSON format.

                            Input:
                            Resume: A candidate's resume containing experience, skills, and background information.
                            Candidates Experience: A summary of the candidate's experience from the recruiter.
                            Gong Transcripts: Conversations, sales calls, and interviews that reveal the candidate's competencies, communication style, and strategic thinking.
                            Recruiter provided summary: A summary of the candidate provided by the recruiter.
                            Job Description: A job description of the role.
                            Experience Years: The number of years of experience the candidate has that is directly relevant to the role described in the job description.
                            Senior Level Experience Years: The number of years of experience the candidate has that is at the senior level.
                            Output Format:
                            Provide the extracted data in the following JSON structure:

                            {
                            "score": {
                                "final_score": "<Score out of 100 based on the candidate's resume, gong transcripts and recruiter provided summary ang attributes mentioned in the extracted data. 
                                The score should be based on the job description and the candidate's resume, gong transcripts and recruiter provided summary>",
                                "reasoning": "<Reasoning for the score> Should be atleast 100 words and be specific on what its reffering to in jd, resume, gong transcripts and recruiter provided summary>",
                                "category_wise_score": "<Category wise score which leads to the final_score>" Follow this format: "strategic business impact: 18/20, sales enablement expertise: 16/20, leadership execution ability: 14/20, cultural fit: 15/20, compensation & logistics inferring: 15/20."
                            },
                            "compensation_logistics": {
                                "compensation_range": "<Extracted or inferred from experience/role> Should be a number in USD Thousands like 80000 in Integer",
                                "location_remote_flexibility": "<Remote/In-office/Hybrid based on location details> One word only",
                                "role_level": "<Extracted from job titles and seniority> One word only",
                                "team_management_responsibilities": "<Extracted based on leadership roles>"
                            },
                            "industry_market_gtm_motion_fit": {
                                "industry_domain_experience": "<Extracted industry expertise>",
                                "gtm_motion_experience": "<Sales motion experience, e.g., B2B, PLG, Direct Sales>",
                                "sales_segment_experience": "<Market segments such as SMB, Mid-Market, Enterprise>",
                                "preferred_sales_methodology": "<Extracted sales methodology, e.g., Challenger, MEDDIC>"
                            },
                            "strategic_business_impact_attributes": {
                                "executive_presence_influence": "<1-5 rating based on communication impact>",
                                "pattern_recognition_foresight": "<1-5 rating based on strategic thinking>",
                                "prioritization_focus": "<1-5 rating based on decision-making clarity>",
                                "commercial_acumen_sales_mentality": "<1-5 rating based on revenue-driven mindset>",
                                "comfort_with_ambiguity_iteration": "<1-5 rating based on adaptability>"
                            },
                            "sales_enablement_expertise": {
                                "sales_rep_empathy_credibility": "<1-5 rating based on rapport with sales teams>",
                                "challenger_diplomat_balance": "<1-5 rating based on assertiveness vs. diplomacy>",
                                "psychology_learning_behavior_change": "<1-5 rating based on ability to influence learning>",
                                "experience_with_revenue_enablement": "<1-5 rating based on sales enablement exposure>",
                                "experience_sales_ecosystems": "<Extracted experience with AEs, SDRs, CS, etc.>"
                            },
                            "leadership_execution_ability": {
                                "change_management_influence_without_authority": "<1-5 rating based on leadership style>",
                                "bias_toward_execution": "<1-5 rating based on action-oriented approach>",
                                "hands_on_delegation_balance": "<1-5 rating based on delegation skills>",
                                "data_fluency_business_impact": "<1-5 rating based on data-driven decision-making>",
                                "storytelling_narrative_framing": "<1-5 rating based on communication effectiveness>"
                            },
                            "cultural_organizational_fit": {
                                "company_stage_fit": "<Startup/SMB/Mid-Market/Enterprise based on experience>",
                                "resilience_ability_handle_resistance": "<1-5 rating based on perseverance>",
                                "adaptability_speed_learning": "<1-5 rating based on ability to learn quickly>",
                                "intellectual_curiosity_growth_mindset": "<1-5 rating based on self-driven learning>",
                                "ownership_mentality_task_execution": "<1-5 rating based on initiative>"
                            },
                            "cultural_environmental_factors": {
                                "political_savvy": "<1-5 rating based on ability to navigate org dynamics>",
                                "personality_communication_fit": "<Extracted based on communication style>",
                                "culture_dei_importance": "<1-5 rating based on diversity & inclusion perspective>",
                                "role_type": "<Expansion/Hunter/Farmer based on sales motion>",
                                "autonomy_handholding": "<1-5 rating based on independence>"
                            },
                            "hidden_differentiators": {
                                "tailors_approach": "<1-5 rating based on customization skills>",
                                "quantifies_past_impact": "<1-5 rating based on ability to demonstrate results>",
                                "reads_room_adapts_pitch": "<1-5 rating based on situational awareness>",
                                "asks_business_oriented_questions": "<1-5 rating based on depth of inquiry>",
                                "confident_not_dogmatic": "<1-5 rating based on balanced confidence>"
                            }
                            }


                            Strict rules for Extraction and Evaluation:
                            Identify Key Data

                            Extract details from job titles, responsibilities, achievements, and industry-specific terminology in the resume.
                            Analyze Gong transcripts for verbal cues on influence, confidence, adaptability, and expertise.
                            Infer Numerical Ratings (1-5 Scale)

                            Assign ratings based on context, keywords, and tone in conversations.
                            Example: A candidate demonstrating strong executive presence in a transcript may get a 5 for "executive_presence_influence."
                            Handle Missing or Implicit Data

                            If compensation details are not explicit, infer from industry benchmarks and experience level.
                            If an attribute is not present, return null or provide a best-guess estimate.
                            Ensure Contextual Accuracy
                            In case of mutliple values send string of comma separted values.

                            Extract industry, role level, and sales methodology accurately without assuming.
                            Use multiple data points across resume and transcripts to ensure reliable extraction.
                            All the metrics/ratings should be relevant to the job description.
                            A good candidate for a VP of Enablement role should have several years at the VP, Sr Director, or Director level in a sales enablement role with good tenures at each.
                            It needs to weight years in relevant roles more than years in irrelevant roles.
                            Avoid overlapping experience.
                            If the candidate has experience in a role that is not relevant to the job description, it should not be considered.
                            For each penalty decrease the candidates score.
                            Stricly penalize the people who non relevant experience and decrease the score.
                            If the candidate has experience in a role that is not relevant to the job description, it should not be considered assign a very low score.
                    """
            prompt = f"""
                Generate metadata from the given text blob.  
                The metadata should strictly be based on the system prompt
                Provide the following data in a Python-compatible dictionary format, ready to be used with json.loads(). Do not include markdown formatting or string escaping in the output.
                **Text Blob:**  
                {text_blob}
                """

            response = await self.get_gpt_response(prompt, system_prompt)
            if response["status_code"] == 500:
                return response
            return {"metadata": response["response"], "status_code": 200}
        except Exception as e:
            logger.error(f"An error occurred while generating metadata: {e}")
            return {
                "message": f"An error occurred while generating metadata: {e}",
                "status_code": 500,
            }
        
    async def generate_metadata_via_ai_v2(self, text_blob: str):
        """
        Returns full candidate-metadata JSON, including detailed score breakdown.
        """
        try:
            # ───────────────────── FULL JSON SCHEMA ─────────────────────
            metadata_schema = """
            Provide a Python-compatible dict (no markdown, no backticks) with EXACTLY:

            {
            "score": {
                "final_score": <int 0-100>,
                "reasoning": "<100-word explanation referencing JD, resume, Gong, recruiter summary>",
                "category_wise_score": "strategic business impact: N/20, sales enablement expertise: N/20, leadership execution ability: N/20, cultural fit: N/20, compensation & logistics inferring: N/20",
                "fit": "yes or no if final_score is greater than 90"
            },
            "compensation_logistics": {
                "compensation_range": <int or null>,
                "location_remote_flexibility": "<Remote|In-office|Hybrid|null>",
                "role_level": "<string|null>",
                "team_management_responsibilities": "<string|null>"
            },
            "industry_market_gtm_motion_fit": {
                "industry_domain_experience": "<string|null>",
                "gtm_motion_experience": "<string|null>",
                "sales_segment_experience": "<string|null>",
                "preferred_sales_methodology": "<string|null>"
            },
            "strategic_business_impact_attributes": {
                "executive_presence_influence": "<1-5|null>",
                "pattern_recognition_foresight": "<1-5|null>",
                "prioritization_focus": "<1-5|null>",
                "commercial_acumen_sales_mentality": "<1-5|null>",
                "comfort_with_ambiguity_iteration": "<1-5|null>"
            },
            "sales_enablement_expertise": {
                "sales_rep_empathy_credibility": "<1-5|null>",
                "challenger_diplomat_balance": "<1-5|null>",
                "psychology_learning_behavior_change": "<1-5|null>",
                "experience_with_revenue_enablement": "<1-5|null>",
                "experience_sales_ecosystems": "<string|null>"
            },
            "leadership_execution_ability": {
                "change_management_influence_without_authority": "<1-5|null>",
                "bias_toward_execution": "<1-5|null>",
                "hands_on_delegation_balance": "<1-5|null>",
                "data_fluency_business_impact": "<1-5|null>",
                "storytelling_narrative_framing": "<1-5|null>"
            },
            "cultural_organizational_fit": {
                "company_stage_fit": "<Startup|SMB|Mid-Market|Enterprise|null>",
                "resilience_ability_handle_resistance": "<1-5|null>",
                "adaptability_speed_learning": "<1-5|null>",
                "intellectual_curiosity_growth_mindset": "<1-5|null>",
                "ownership_mentality_task_execution": "<1-5|null>"
            },
            "cultural_environmental_factors": {
                "political_savvy": "<1-5|null>",
                "personality_communication_fit": "<string|null>",
                "culture_dei_importance": "<1-5|null>",
                "role_type": "<Hunter|Farmer|Expansion|null>",
                "autonomy_handholding": "<1-5|null>"
            },
            "hidden_differentiators": {
                "tailors_approach": "<1-5|null>",
                "quantifies_past_impact": "<1-5|null>",
                "reads_room_adapts_pitch": "<1-5|null>",
                "asks_business_oriented_questions": "<1-5|null>",
                "confident_not_dogmatic": "<1-5|null>"
            }
            }
            If a field is not present, put null.
            """

            # ───────────────────── SCORING RULES ─────────────────────
            scoring_rubric = """
                Scoring (100 pts) uses five categories, with Leadership/Seniority weighted more heavily:

                1. Leadership / Seniority Execution Ability       — 40 pts
                2. Strategic Business Impact                      — 15 pts
                3. Sales Enablement Expertise                     — 15 pts
                4. Cultural Fit                                   — 15 pts
                5. Compensation & Logistics Inferring             — 15 pts

                Category_wise_score format MUST be:
                "leadership / seniority execution ability: N/40, strategic business impact: N/15, sales enablement expertise: N/15, cultural fit: N/15, compensation & logistics inferring: N/15"

                final_score = sum of the five category scores (max = 100).

                Notes:
                • For the Compensation you will be given a range, we can have a 15% tolerance. Beyond the 15%, their ranking should drop significantly.
                • For the Location you will be given a location, if its not under 100 miles of the location, their ranking should drop significantly, if its a remote location this condiation should not be applied.

                Hard caps and penalties (unchanged):
                • No demonstrable leadership → final_score < 80.  
                • <3 yrs senior enablement → final_score < 70.  
                • One or more short stints → proportional deduction.

                `reasoning` must cite evidence from JD, resume, Gong transcripts, and recruiter summary.
                """

            system_prompt = f"""
            You are an advanced Hiring-Manager AI.

            Strict rules for Extraction and Evaluation:
            Identify Key Data

            Extract details from job titles, responsibilities, achievements, and industry-specific terminology in the resume.
            Analyze Gong transcripts for verbal cues on influence, confidence, adaptability, and expertise.
            Infer Numerical Ratings (1-5 Scale)

            Assign ratings based on context, keywords, and tone in conversations.
            Example: A candidate demonstrating strong executive presence in a transcript may get a 5 for "executive_presence_influence."
            Handle Missing or Implicit Data

            If compensation details are not explicit, infer from industry benchmarks and experience level.
            If an attribute is not present, return null or provide a best-guess estimate.
            Ensure Contextual Accuracy
            In case of mutliple values send string of comma separted values.

            Extract industry, role level, and sales methodology accurately without assuming.
            Use multiple data points across resume and transcripts to ensure reliable extraction.
            All the metrics/ratings should be relevant to the job description.
            A good candidate for a VP of Enablement role should have several years at the VP, Sr Director, or Director level in a sales enablement role with good tenures at each.
            It needs to weight years in relevant roles more than years in irrelevant roles.
            The Heirarchy of the experience is as follows:
            VP > Sr Director > Director > Sr Manager > Manager > Senior > Junior
            Avoid overlapping experience.
            For each penalty decrease the candidates score.
            Stricly penalize the people who non relevant experience and decrease the score.
            Stricly penalize the people who are overqualified for the role and decrease the score.
            If the candidate has experience in a role that is not relevant to the job description, it should not be considered assign a very low score.

            {metadata_schema}

            {scoring_rubric}
            """

            prompt = f"""
            Generate the metadata for the candidate below.

            TEXT BLOB
            ─────────
            {text_blob}
            ─────────
            """

            llm_resp = await self.get_gpt_response(prompt=prompt,
                                                system_prompt=system_prompt)

            if llm_resp.get("status_code") == 500:
                return llm_resp

            # minimal sanity check
            try:
                _ = json.loads(llm_resp["response"].strip())
            except json.JSONDecodeError:
                return {"message": "LLM returned invalid JSON", "status_code": 500}

            return {"metadata": llm_resp["response"], "status_code": 200}

        except Exception as e:
            logger.error("generate_metadata_via_ai error: %s", e)
            return {"message": f"Error generating metadata: {e}", "status_code": 500}
        
    async def generate_relevant_experience_years_v2(self,
                                            experience_text: str,
                                            job_description: str):
        """
        Ask the LLM to compute:
        • total_relevant_years  – all full‑time, non‑overlapping years that
            match the JD’s industry / function.
        • senior_level_years   – subset of those years spent at Director+ titles
            (Director, Sr Director, VP, SVP, C‑level).

        Returns:
            {
            "relevant_experience_years": <int>,
            "senior_level_years": <int>,
            "status_code": 200
            }
        """
        try:
            # ── Prompt the model ────────────────────────────────────────
            system_prompt = """
            You are an expert resume analyst.

            Task:
            1. Parse the candidate’s experience text.
            2. Identify periods that are relevant to the job description (industry,
            function, responsibilities).
            3. Exclude internships, part‑time, and overlaps.
            4. Senior‑level titles = Director, Sr Director, VP, SVP, EVP, C‑level.

            Count full months, convert to **whole years (round down)**.

            Respond ONLY with valid JSON:
            {"total_relevant_years": <int>, "senior_level_years": <int>}
            """

            prompt = f"""
            CANDIDATE EXPERIENCE TEXT
            ────────────────────────
            {experience_text.strip()}

            JOB DESCRIPTION
            ───────────────
            {job_description.strip()}

            Please return the JSON now.
            """

            llm_resp = await self.get_gpt_response(system_prompt=system_prompt,
                                                prompt=prompt)

            if llm_resp.get("status_code") == 500:
                return llm_resp

            # ── Minimal validation / fallback ──────────────────────────
            try:
                data = json.loads(llm_resp["response"].strip())
                total_years  = int(data.get("total_relevant_years", 0))
                senior_years = int(data.get("senior_level_years", 0))
            except Exception:
                # Fallback: grab first two integers in response
                nums = re.findall(r"\d+", llm_resp["response"])
                total_years  = int(nums[0]) if nums else 0
                senior_years = int(nums[1]) if len(nums) > 1 else 0

            return {"relevant_experience_years": total_years,
                    "senior_level_years": senior_years,
                    "status_code": 200}

        except Exception as e:
            logger.exception("generate_relevant_experience_years error: %s", e)
            return {"message": f"Error generating experience years: {e}",
                    "status_code": 500}

    async def select_candidates_for_matching(self, job_description: str, candidate_summary: str):
        try:
            system_prompt = """
            You are an expert recruiter specializing in analyzing candidates. You will be given a job description and a candidate summary. Your task is to select the suitable candidate for the job description. If based on positions experience required select the candidate who aligns with the experience required. If its either lower or higher than the experience required skip those, if its within the range select the candidate. You need to respond with yes or no.
            """
            prompt = f"Job Description: {job_description}\n\nCandidate Summary: {candidate_summary}"
            response = await self.get_gpt_response(system_prompt=system_prompt, prompt=prompt)
            return response
        except Exception as e:
            logger.exception("Failed to select candidates for matching")
            return {
                "message": f"An error occurred while selecting candidates for matching: {str(e)}",
                "status_code": 500,
            }

        
    async def generate_relevant_experience_years(self, experience_text: str, job_description: str):
        try:
            prompt = f"""
            Experience:
            {experience_text.strip()}

            Job Description:
            {job_description.strip()}
            """

            system_prompt = """
            You are an expert at evaluating resumes against job descriptions.
            Your task is to estimate how many years of experience the candidate has that is directly relevant to the role described in the job description.
            Focus only on relevant industry or role-specific experience.
            Skip the short term experience or stints like internships, part-time jobs, etc.
            Avoid overlapping experience.
            A good candidate for a VP of Enablement role should have several years at the VP, Sr Director, or Director level in a sales enablement role with good tenures at each.
            It needs to weight years in relevant roles more than years in irrelevant roles.
            Respond with a single number (e.g., "5" for five years).
            """

            response = await self.get_gpt_response(system_prompt=system_prompt, prompt=prompt)

            if response.get("status_code") == 500:
                return response

            raw_output = response.get("response", "").strip()
            match = re.search(r"\d+(?:\.\d+)?", raw_output)
            experience_years = int(float(match.group(0))) if match else 0

            return {
                "relevant_experience_years": experience_years,
                "status_code": 200
            }

        except Exception as e:
            logger.exception("Failed to generate relevant experience years")
            return {
                "message": f"An error occurred while generating relevant experience years: {str(e)}",
                "status_code": 500,
            }