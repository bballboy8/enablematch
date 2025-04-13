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
    job_description, conversation_transcript=None, resume_text=None, notes=None, source="Resume"
):
    """Create a detailed GPT prompt using the job description, conversation transcript, and resume text."""

    prompt = f"""
            Here is a Job Description. Resume Text, Summary of the Conversation Transcript and Notes(optional). Based on Rubric and Interpersonal Compatibility Guidelines Provide a clear decision (Suitable, Not Suitable, Requires Further Evaluation). 
            
            Job Description:
            {job_description}
            """

    if resume_text:
        prompt += f"\n\n{source} Content:\n{resume_text}"

    if conversation_transcript:
        prompt += f"\n\nConversation Transcript:\n{conversation_transcript}"

    if notes:
        prompt += f"\n\nNotes:\n{notes}"

    return prompt


def get_system_prompt():
    return f"""
        You are an expert recruiter specializing in summarizing and analyzing conversations between candidates and hiring managers to find the best fit candidate. You have additional deep expertise in sales enablement which provides guidance on more subtle points of candidate fit.  Your goal is to find best fit candidates based on the criteria detailed below:

        1.A level of sales enablement mastery as required for the role using the rubric below.  With that, consider their enablement successes and struggles- programs and initiatives they've run..  Examine closely for sales enablement best practices, highlights of program metrics, and their executive presence.  Also, examine for interpersonal dynamics within prior roles where they may have struggled and overcome obstacles or failed to do so. 
        2.Matching of what we deem as the essential requirements.  Extra weight should be given to any requirements around personality types and environment where they'd succeed.
        3.Matching of the job requirements as set forth in the transcripts with the hiring manager and any job description provided.  Weight the hiring manager's comments twice as important as those captured in the job description.
        4.Matching the level of the candidate with the level of the role to ensure they're not too junior or too senior for the role.  Note and factor in your analysis that some conversations happened years ago and that the candidate may have additional experience and roles in the meantime.
        5.When evaluating the fit of a candidate, factor in whether they've worked at a similarly-sized company in their past.  
        6.When evaluating the fit of a candidate, if they've worked in similar industries as the role, that makes them a better fit.  Unless otherwise noted in the requirements, a lack of having worked in a similar industry does not disqualify them.  


        Rubric Guidelines:

        1. Strategic Thinking & Vision 
        (Expert): Candidate demonstrates the ability to build a holistic, long-term enablement strategy that aligns with company objectives, articulates a clear vision, and balances short-term execution with future planning. They incorporate data-driven insights and buyer-centric approaches to continuously improve sales enablement.
        (Proficient): Candidate creates an enablement strategy that reflects company goals and buyer needs but lacks depth in certain areas (e.g., not as data-driven or scalable). Vision is clear but may need further refinement.
        (Competent): Candidate can articulate basic sales enablement strategies but struggles with creating long-term, scalable frameworks. Vision tends to be focused on short-term outcomes.
        (Developing): Candidate exhibits awareness of sales enablement strategy but relies heavily on established processes without much innovation. Focus is reactive rather than proactive.
        (Novice): Candidate lacks a clear strategic approach to sales enablement. Conversations focus only on tactical execution without considering long-term goals.
        
        2. Program Design & Execution
        (Expert): Candidate designs, implements, and scales enablement programs that engage sales teams effectively. They ensure content, coaching, and training are tailored to the sales cycle, supported by technology, and aligned with business outcomes.
        (Proficient): Candidate has experience building comprehensive enablement programs but may not have extensive experience in scaling them globally or leveraging the latest tools/technologies to their full potential.
        (Competent): Candidate has designed and delivered enablement programs but is still developing expertise in optimizing them for various audiences and sales cycles.
        (Developing): Candidate understands program design but has only been involved in executing pre-built programs or templates. Limited experience in full-cycle enablement.
        (Novice): Candidate lacks hands-on experience in enablement program design and execution, relying on external support or limited frameworks.
        
        3. Cross-Functional Collaboration
        (Expert): Candidate has a proven track record of collaborating across departments (sales, marketing, product, customer success, etc.). They effectively align enablement programs with broader business initiatives and lead cross-functional initiatives that drive performance.
        (Proficient): Candidate works well with other departments and contributes to collaborative projects. They may have led a few cross-functional efforts but could benefit from more complex experiences.
        (Competent): Candidate participates in cross-functional collaboration but tends to work in silos or lacks leadership experience in this area.
        (Developing): Candidate has limited experience in cross-functional work and primarily focuses on departmental responsibilities.
        (Novice): Candidate shows little to no experience working across departments and lacks an understanding of how to drive cross-functional success.
       
        4. Coaching & Development 
        (Expert): Candidate builds coaching programs tailored to different sales personas, leveraging insights to create impactful learning paths. They foster a culture of continuous learning and skill development within the sales organization.
        (Proficient): Candidate is skilled at coaching and mentoring sales teams but may not have led large-scale development programs. They show strong leadership but limited exposure to diverse learning technologies.
        (Competent): Candidate is proficient in coaching individuals or small teams but lacks experience in coaching at scale or creating formal coaching frameworks.
        (Developing): Candidate understands the value of coaching but has limited hands-on experience in formal development roles.
        (Novice): Candidate lacks coaching experience or understanding of structured development approaches for sales teams.
        
        5. Use of Technology & Tools 
        (Expert): Candidate demonstrates a deep understanding of sales enablement tools (CRM, sales content management, analytics) and uses them to enhance sales productivity. They can select, implement, and optimize tech solutions to support enablement at scale.
        (Proficient): Candidate is comfortable with a wide range of tools and has implemented some enablement technology but has room for optimization or scalability.
        (Competent): Candidate uses enablement tools effectively but may not have experience in implementing or selecting new technology. They focus on day-to-day use rather than long-term strategy.
        (Developing): Candidate has limited exposure to enablement tools and relies on basic platforms without a clear strategy for technology adoption.
        (Novice): Candidate is unfamiliar with key enablement tools and lacks experience integrating technology into enablement efforts.
        
        6. Measurement & Metrics 
        (Expert): Candidate establishes clear, measurable goals for enablement programs, using KPIs like sales velocity, conversion rates, and revenue growth. They use analytics to continuously improve and iterate on programs.
        (Proficient): Candidate tracks and reports on key metrics but may not fully optimize or leverage data to continuously iterate on programs.
        (Competent): Candidate has experience measuring enablement outcomes but lacks a data-driven approach to continually improve. They rely on basic KPIs.
        (Developing): Candidate demonstrates awareness of metrics but focuses on qualitative rather than quantitative assessment of success.
        (Novice): Candidate lacks experience with metrics and measurement in enablement. Conversations are vague or rely on anecdotal success stories.
        
        7. Alignment with Business Outcomes 
        (Expert): Candidate ensures that enablement is tightly integrated with business outcomes, driving revenue, customer retention, and productivity. They prioritize initiatives that align with the company's strategic goals and can communicate this clearly.
        (Proficient): Candidate effectively aligns enablement programs with broader business objectives but may lack experience in communicating direct impact to senior leadership.
        (Competent): Candidate demonstrates understanding of business outcomes but may focus more on sales performance without tying enablement to long-term company success.
        (Developing): Candidate has basic knowledge of how enablement contributes to business outcomes but doesn't actively align programs with strategic goals.
        (Novice): Candidate lacks awareness of the broader business context in which enablement operates. Focuses only on isolated training or content creation.
        
        8. Leadership & Influence 
        (Expert): Candidate is a visionary leader with proven influence over sales, marketing, and executive teams. They mentor other leaders and drive organizational change through enablement initiatives.
        (Proficient): Candidate leads effectively but may lack significant experience influencing executive leadership or shaping company-wide enablement culture.
        (Competent): Candidate is a capable leader within the enablement team but may not have broader influence across departments or at the executive level.
        (Developing): Candidate demonstrates emerging leadership qualities but has not yet established themselves as an influencer.
        (Novice): Candidate lacks leadership experience in enablement or sales and focuses on tactical, individual tasks.


        Interpersonal Compatibility Evaluation:
        
        To determine compatibility between candidates who will independently hold conversations with others, you need to analyze their transcripts with a sharper focus on how their working styles, communication approaches, and interpersonal dynamics would complement or clash in a shared work environment. This involves identifying alignment, contrasts, and adaptability in how they interact with third parties.
        Here-s a deeper and more nuanced guidelines to evaluating compatibility based on separate conversations:

        1. Communication Style Alignment
        Key Aspects to Evaluate:
        a. Clarity and Articulation: Does the candidate communicate in a way that would resonate with others? For example:
        - Is their tone adaptable or rigid?
        - Do they make their points accessible to a diverse audience?
        b. Pacing and Depth: Compare the transcript for conversational pacing. Would one candidate's rapid-fire delivery overwhelm another's more reflective or slower style?
        c. Question-Asking vs. Answer-Providing:
        - Does one candidate focus on listening and asking thoughtful questions?
        - Does the other focus on confidently presenting their viewpoints? Balance between these can foster collaboration.

        2. Approach to Building Rapport

        a. Openness and Relatability:
        - Does the candidate share anecdotes, humor, or relatable stories to build trust and rapport?
        - Is there alignment in how much personal context they offer in conversations?
        b. Validation and Empathy:
        - Does the candidate actively validate others' points of view?
        - Would a "dominant validator" work well with someone who needs affirmation to thrive?
        c. Formality vs. Casualness:
        - A highly formal candidate might clash with someone who is overly casual, leading to misunderstandings.

        3. Decision-Making and Problem-Solving Styles

        a. Analytical Depth:
        - Does one candidate dive deeply into problems while the other prefers quick, actionable solutions?
        - Assess how their styles would align in a task requiring joint problem-solving.
        b. Collaboration vs. Independence:
        - Does the candidate consistently seek input or prefer autonomy?
        - Would two highly independent thinkers struggle to compromise, or would one collaborator balance the other's lone-wolf tendencies?
        c. Bias for Action vs. Reflection:
        - Does the candidate favor rapid decision-making or careful deliberation?
        - Compatibility improves when individuals balance these traits.

        4. Energy Levels and Engagement
        a. Enthusiasm and Drive:
        - Does the candidate bring energy and passion to the conversation?
        - Would this energy level motivate or overwhelm a potential collaborator?
        b. Consistency in Engagement:
        - Does the candidate maintain focus and energy throughout, or do they lose steam?
        - Compare how they handle complex topics versus light interactions.
        c. Adaptability to Context:
        - Can they pivot their tone or approach depending on the subject matter or audience?

        5. Conflict Resolution Potential
        a. Response to Challenges:
        - How does the candidate handle difficult questions, misunderstandings, or feedback?
        - Look for evidence of diplomacy or defensiveness.
        b. Assertiveness vs. Agreeableness:
        - Does one candidate lean toward strong opinions while the other avoids confrontation?
        - Complementary styles can enhance resolution but polar opposites might clash.
        c. Focus on Solutions:
        - Does the candidate shift discussions toward actionable outcomes during moments of disagreement?

        6. Leadership vs. Collaboration Balance
        a. Authority in Conversation:
        - Does the candidate naturally take charge of discussions, or do they allow others to lead?
        - Openness to Other Perspectives:
        - Do they acknowledge and integrate others ideas, or focus primarily on their own expertise?
        b. Flexibility in Roles:
        - Would they adjust to being in a supportive role if the situation demands?

        7. Shared Vision and Values
        a. Alignment in Priorities:
        - Do both candidates emphasize similar goals or outcomes (e.g., customer success, innovation, efficiency)?
        b. Cultural Fit Indicators:
        - Look for language that reflects shared values or priorities (e.g., respect for team input, a focus on outcomes).
        c. Passion for the Role:
        - Does their motivation align with the responsibilities of the role and potential collaborators?

        8. Adaptability and Growth Orientation
        a. Willingness to Learn:
        - Does the candidate demonstrate humility and openness to constructive feedback?
        b. Adaptation to the Interviewer:
        - Do they adjust their communication style to match the tone and energy of the interviewer?
        c. Mindset Toward Collaboration:
        - Do they frame collaboration as an opportunity for mutual learning and growth?

        Quantitative Scoring:
        Generate total weighted scores (e.g., 0-100) and classify candidates as "Strong Fit," "Moderate Fit," or "Weak Fit."
        Behavioral Typing:
        Assign candidates to personas (e.g., "Strategic Thinker," "Empathetic Connector") for deeper matching insights.


        Scoring Methodology based on Rubrics adherence and Interpersonal Compatibility Guidelines:
        - 10: Candidate demonstrates expert-level proficiency in all areas of sales enablement.
        - 8-9: Candidate shows a high level of proficiency in most areas but may have minor gaps in one or two competencies.
        - 6-7: Candidate is competent in sales enablement but lacks depth in several key areas.
        - 4-5: Candidate is developing in sales enablement and may struggle with multiple competencies.
        - 2-3: Candidate has limited experience in sales enablement and lacks proficiency in most areas.
        - 0-1: Candidate lacks the foundational skills needed for sales enablement roles.

        Insights: Look at the candidate Source of Profile and see how well they fit for a given role. Reference Linkedin profile content like ("Users's six years of experience at Red Canary makes her a strong candidate for the role at Obsidian Security due to her deep domain expertise". Or "Since User has only worked at larger companies like Oracle and Salesforce, he would likely struggle adapting to the culture of a smaller startup like this.").  Also you need to be specific about the points and the source like if its Linkedin or their Resume it should be mentioned in the insights and the conversation summary.

        
        Based on Rubrics scores and Interpersonal Compatibility Guidelines Provide a clear decision (Suitable, Not Suitable, Requires Further Evaluation) and explain the reasons for your decision based on the conversation and role requirements. Your response should only be in RFC8259 compliant JSON format without deviation with the following keys: 

        - response: The key summary with specifics and evaluation of the candidate. 
        - quantitative_score: The total weighted score assigned to the candidate out of 100.
        - quantitative_decision: The decision based on the quantitative score (Strong Fit, Moderate Fit, Weak Fit).
        - behavioral_typing: The persona assigned to the candidate based on their behavior.
        - score: The score assigned to the candidate based on the evaluation out of 10. 
        - decision: The final decision (Suitable, Not Suitable, Requires Further Evaluation). 
        - comment: If someone doesn't get 10 out of 10, mention some comments on what would have made them a 10.
        - insight: Based on the Source Linkedin Profile content  or Resume content, give a one-liner insight on why the candidate is suitable or not suitable for the role as per example in the Insights section .

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


async def summarize_conversation(conversation_transcript, input_resume):
    try:
        conversation_transcript = "Here is the Users background and experience: " + input_resume + "and here is the conversation transcript: " + conversation_transcript
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert summarizer. You are going to extract the Strength, Weakness, Overall how is the conversation for job role and summarize the conversation. You are going to be a bit more critical in your analysis. Also you need to look for following points 1. Do the candidates refer to metrics? 2. Are they concise or long winded? 3. Do they minimize filler words? 4. Do they talk like an executive? Be sure to mention the key points of the conversation. 5.You always need to be specific about the points specific like if a candidate is talking about a project, you need to mention the project name, the role of the candidate in the project, the outcome of the project, and the impact of the project. You need to be very specific about the points. You need to check if a candidate has resume of linkedin profile and mention the points from there. 6. You need to mention the source of the content like if its from Linkedin or Resume.",
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
    
async def generate_skills_and_strength_of_candidate(conversation_transcript):
    try:
        conversation_transcript = "Here is the conversation transcript: " + conversation_transcript
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert summarizer. You are going to extract the Strength, Skills and Overall how is the conversation for job role and summarize the conversation. You are going to be a bit more critical in your analysis. Also you need to look for following points 1. Do the candidates refer to metrics? 2. Are they concise or long winded? 3. Do they minimize filler words? 4. Do they talk like an executive? Be sure to mention the key points of the conversation. 5.You always need to be specific about the points specific like if a candidate is talking about a project, you need to mention the project name, the role of the candidate in the project, the outcome of the project, and the impact of the project. You need to be very specific about the points.",
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


def create_comparing_prompt(
    job_description, candidate_1_blob, candidate_2_blob, candidate_1_id, candidate_2_id, candidate_1_ote, candidate_2_ote
):
    """Create a detailed GPT prompt using the job description, conversation transcript, and resume text."""

    prompt = f"""
    Candidate 1 ID: {candidate_1_id}
    Candidate 2 ID: {candidate_2_id}

    Candidate 1 Compensation: {candidate_1_ote}
    Candidate 2 Compensation: {candidate_2_ote}

    If any or both of the candidate compensation is not mentioned, then based on the candidate blob content, you need to mention the compensation of the candidate.

    ---

    ### Job Description:
    {job_description}

    ---

    ### Evaluation Criteria and Metadata Required

    Output Candidate Metadata Format:
    Provide the extracted data in the following JSON structure:

    {{
    "compensation_logistics": {{
        "compensation_range": "<Extracted or inferred from experience/role> Should be a number in USD Thousands like 80000 in Integer",
        "location_remote_flexibility": "<Remote/In-office/Hybrid based on location details> One word only",
        "role_level": "<Mapped role level: VP, Senior director, Director (or 'Head of'), Senior manager, Manager, Everything else>",
        "team_management_responsibilities": "<Extracted based on leadership roles>"
    }},
    "industry_market_gtm_motion_fit": {{
        "industry_domain_experience": "<Extracted industry expertise>",
        "gtm_motion_experience": "<Sales motion experience, e.g., B2B, PLG, Direct Sales>",
        "sales_segment_experience": "<Market segments such as SMB, Mid-Market, Enterprise>",
        "preferred_sales_methodology": "<Extracted sales methodology, e.g., Challenger, MEDDIC>"
    }},
    "strategic_business_impact_attributes": {{
        "executive_presence_influence": "<1-5 rating based on communication impact>",
        "pattern_recognition_foresight": "<1-5 rating based on strategic thinking>",
        "prioritization_focus": "<1-5 rating based on decision-making clarity>",
        "commercial_acumen_sales_mentality": "<1-5 rating based on revenue-driven mindset>",
        "comfort_with_ambiguity_iteration": "<1-5 rating based on adaptability>"
    }},
    "sales_enablement_expertise": {{
        "sales_rep_empathy_credibility": "<1-5 rating based on rapport with sales teams>",
        "challenger_diplomat_balance": "<1-5 rating based on assertiveness vs. diplomacy>",
        "psychology_learning_behavior_change": "<1-5 rating based on ability to influence learning>",
        "experience_with_revenue_enablement": "<1-5 rating based on sales enablement exposure>",
        "experience_sales_ecosystems": "<Extracted experience with AEs, SDRs, CS, etc.>"
    }},
    "leadership_execution_ability": {{
        "change_management_influence_without_authority": "<1-5 rating based on leadership style>",
        "bias_toward_execution": "<1-5 rating based on action-oriented approach>",
        "hands_on_delegation_balance": "<1-5 rating based on delegation skills>",
        "data_fluency_business_impact": "<1-5 rating based on data-driven decision-making>",
        "storytelling_narrative_framing": "<1-5 rating based on communication effectiveness>"
    }},
    "cultural_organizational_fit": {{
        "company_stage_fit": "<Startup/SMB/Mid-Market/Enterprise based on experience>",
        "resilience_ability_handle_resistance": "<1-5 rating based on perseverance>",
        "adaptability_speed_learning": "<1-5 rating based on ability to learn quickly>",
        "intellectual_curiosity_growth_mindset": "<1-5 rating based on self-driven learning>",
        "ownership_mentality_task_execution": "<1-5 rating based on initiative>"
    }},
    "cultural_environmental_factors": {{
        "political_savvy": "<1-5 rating based on ability to navigate org dynamics>",
        "personality_communication_fit": "<Extracted based on communication style>",
        "culture_dei_importance": "<1-5 rating based on diversity & inclusion perspective>",
        "role_type": "<Expansion/Hunter/Farmer based on sales motion>",
        "autonomy_handholding": "<1-5 rating based on independence>"
    }},
    "hidden_differentiators": {{
        "tailors_approach": "<1-5 rating based on customization skills>",
        "quantifies_past_impact": "<1-5 rating based on ability to demonstrate results>",
        "reads_room_adapts_pitch": "<1-5 rating based on situational awareness>",
        "asks_business_oriented_questions": "<1-5 rating based on depth of inquiry>",
        "confident_not_dogmatic": "<1-5 rating based on balanced confidence>"
    }}
    }}

    ---

    ### Instructions for Extraction:

    - **Identify Key Data:**  
    Extract details from job titles, responsibilities, achievements, and industry-specific terminology in the resume.  
    Analyze Gong transcripts for verbal cues on influence, confidence, adaptability, and expertise.

    - **Infer Numerical Ratings (1-5 Scale):**  
    Assign ratings based on context, keywords, and tone in conversations.  
    Example: A candidate demonstrating strong executive presence in a transcript may get a 5 for `"executive_presence_influence"`.

    - **Handle Missing or Implicit Data:**  
    If an attribute is not present, return `null` or provide a best-guess estimate.

    - **Ensure Contextual Accuracy:**  
    Extract industry, role level, and sales methodology accurately without assuming.  
    Use multiple data points across resume and transcripts to ensure reliable extraction.  
    In case of multiple values, return a comma-separated string.

    - Role Level Mapping:  
    All role levels must be mapped to one of the following categories: VP, Senior director, Director (or "Head of" roles), Senior manager, Manager, Everything else.


    ---

    ### Candidate 1 Content:
    {candidate_1_blob}

    ---

    ### Candidate 2 Content:
    {candidate_2_blob}

    ---

    ### Response Format:
    Return:
    - `candidate_1_metadata` (in the JSON structure above)
    - `candidate_2_metadata` (in the JSON structure above)
    - `selected_candidate_id`: The ID of the candidate who is more suitable for the role based on the job description and evaluation criteria.
    ---
    
    Important formatting instruction:
        Return only the JSON object with no extra text, explanation, or markdown formatting like triple backticks. Do not wrap the response in ```json or any other delimiters. Only return raw, parseable JSON.
    """

    return prompt
