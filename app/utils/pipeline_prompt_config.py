from copy import deepcopy
from datetime import datetime
from textwrap import dedent
from typing import Any

import pytz
from bson import ObjectId

from config import constants
from config.db_connection import db


pipeline_prompts_collection = db[constants.PIPELINE_PROMPTS_COLLECTION]


DEFAULT_PROMPT_CONFIGS = {
    constants.RELEVANT_EXPERIENCE_PROMPT_KEY: {
        "prompt_name": "Relevant Experience Years",
        "description": "Calculates relevant and senior-level years from candidate experience text.",
        "system_prompt": dedent(
            """
            You are an expert resume analyst.

            Task:
            1. Parse the candidate's experience text.
            2. Identify periods that are relevant to the job description (industry,
            function, responsibilities).
            3. Exclude internships, part-time, and overlaps.
            4. Senior-level titles = Director, Sr Director, VP, SVP, EVP, C-level.

            Count full months, convert to whole years (round down).

            Respond ONLY with valid JSON:
            {"total_relevant_years": <int>, "senior_level_years": <int>}
            """
        ).strip(),
        "user_prompt": dedent(
            """
            CANDIDATE EXPERIENCE TEXT
            ------------------------
            {experience_text}

            JOB DESCRIPTION
            ---------------
            {job_description}

            Please return the JSON now.
            """
        ).strip(),
    },
    constants.METADATA_GENERATION_PROMPT_KEY: {
        "prompt_name": "Candidate Metadata Generation",
        "description": "Generates scored candidate metadata for the current matching pipeline.",
        "system_prompt": dedent(
            """
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

            Provide a Python-compatible dict (no markdown, no backticks) with EXACTLY:

            {
            "score": {
                "final_score": <int 0-100>,
                "reasoning": "<100-word explanation referencing JD, resume, Gong, recruiter summary>",
                "category_wise_score": "strategic business impact: N/20, sales enablement expertise: N/20, leadership execution ability: N/20, cultural fit: N/20, compensation & logistics inferring: N/20",
                "fit": "yes or no if final_score is greater than 75"
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

            Scoring (100 pts) uses five categories, with Leadership/Seniority weighted more heavily:

            1. Leadership / Seniority Execution Ability       - 40 pts
            2. Strategic Business Impact                      - 15 pts
            3. Sales Enablement Expertise                     - 15 pts
            4. Cultural Fit                                   - 15 pts
            5. Compensation & Logistics Inferring             - 15 pts

            Category_wise_score format MUST be:
            "leadership / seniority execution ability: N/40, strategic business impact: N/15, sales enablement expertise: N/15, cultural fit: N/15, compensation & logistics inferring: N/15"

            final_score = sum of the five category scores (max = 100).

            Notes:
            - For the Compensation you will be given a range, we can have a 15% tolerance. Beyond the 15%, their ranking should drop significantly. If candidates compensation is below the range then its fine, if its above the range then its not fine ranking should drop significantly.
            - For the Location you will be given a location, if its not under 50 miles of the location, their ranking should drop significantly, if its a remote location this condiation should not be applied. If its a remote location for the job description, this condition should not be applied.

            Hard caps and penalties (unchanged):
            - No demonstrable leadership -> final_score < 80.
            - <3 yrs senior enablement -> final_score < 70.
            - One or more short stints -> proportional deduction.

            reasoning must cite evidence from JD, resume, Gong transcripts, and recruiter summary.
            """
        ).strip(),
        "user_prompt": dedent(
            """
            Generate the metadata for the candidate below.

            TEXT BLOB
            ---------
            {text_blob}
            ---------
            """
        ).strip(),
    },
    constants.MATCH_SELECTION_PROMPT_KEY: {
        "prompt_name": "Candidate Match Selection",
        "description": "Performs final yes/no selection for candidates already scored as fit.",
        "system_prompt": dedent(
            """
            You are an expert recruiter specializing in analyzing candidates. You will be given a job description and a candidate summary. Your task is to select the suitable candidate for the job description. If based on positions experience required select the candidate who aligns with the experience required.
            You will be given a compensation range and a location. If the candidate's compensation range is not within the range of the jobs compensation range, skip that candidate.
            If the candidate's location is not within the range of the jobs location, skip that candidate.
            If its either lower or higher than the experience required skip those, if its within the range select the candidate. You need to respond with yes or no.
            """
        ).strip(),
        "user_prompt": "Job Description: {job_description}\n\nCandidate Summary: {candidate_summary}\n\n Job Compensation Range: {compensation_range}\n\nJob Location: {location}\n\nCandidate Current Location: {candidates_current_location}\n\nCandidate Compensation Range: {candidates_compensation_range}",
    },
}


def get_supported_prompt_keys() -> list[str]:
    return list(DEFAULT_PROMPT_CONFIGS.keys())


def _serialize_prompt_document(document: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(document)
    if "_id" in serialized:
        serialized["id"] = str(serialized.pop("_id"))
    for field in ("created_at", "updated_at", "disabled_at"):
        if serialized.get(field):
            serialized[field] = serialized[field].isoformat()
    previous_version_id = serialized.get("previous_version_id")
    if isinstance(previous_version_id, ObjectId):
        serialized["previous_version_id"] = str(previous_version_id)
    return serialized


def _build_default_prompt_document(prompt_key: str) -> dict[str, Any]:
    if prompt_key not in DEFAULT_PROMPT_CONFIGS:
        raise ValueError(f"Unsupported prompt_key: {prompt_key}")

    default_config = deepcopy(DEFAULT_PROMPT_CONFIGS[prompt_key])
    return {
        "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
        "prompt_key": prompt_key,
        "prompt_name": default_config["prompt_name"],
        "description": default_config["description"],
        "system_prompt": default_config["system_prompt"],
        "user_prompt": default_config["user_prompt"],
        "version": 1,
        "is_active": True,
        "source": "code_fallback",
    }


async def ensure_prompt_indexes() -> None:
    await pipeline_prompts_collection.create_index(
        [("pipeline", 1), ("prompt_key", 1), ("version", 1)],
        unique=True,
    )
    await pipeline_prompts_collection.create_index(
        [("pipeline", 1), ("prompt_key", 1), ("is_active", 1)],
    )


async def get_active_pipeline_prompt(prompt_key: str) -> dict[str, Any]:
    if prompt_key not in DEFAULT_PROMPT_CONFIGS:
        raise ValueError(f"Unsupported prompt_key: {prompt_key}")

    prompt_document = await pipeline_prompts_collection.find_one(
        {
            "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
            "prompt_key": prompt_key,
            "is_active": True,
        },
        sort=[("version", -1)],
    )
    if prompt_document:
        return prompt_document
    return _build_default_prompt_document(prompt_key)


async def render_pipeline_prompt(prompt_key: str, **kwargs: Any) -> tuple[str, str, dict[str, Any]]:
    prompt_document = await get_active_pipeline_prompt(prompt_key)
    try:
        user_prompt = prompt_document["user_prompt"].format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing prompt template value: {e.args[0]}") from e
    return prompt_document["system_prompt"], user_prompt, prompt_document


async def list_active_pipeline_prompts() -> list[dict[str, Any]]:
    prompt_documents = await pipeline_prompts_collection.find(
        {
            "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
            "is_active": True,
        }
    ).sort([("prompt_key", 1), ("version", -1)]).to_list(length=None)

    prompt_by_key = {document["prompt_key"]: document for document in prompt_documents}
    prompts = []
    for prompt_key in get_supported_prompt_keys():
        prompt_document = prompt_by_key.get(prompt_key, _build_default_prompt_document(prompt_key))
        prompts.append(_serialize_prompt_document(prompt_document))
    return prompts


async def create_new_prompt_version(prompt_key: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    if prompt_key not in DEFAULT_PROMPT_CONFIGS:
        raise ValueError(f"Unsupported prompt_key: {prompt_key}")
    if not system_prompt.strip():
        raise ValueError("system_prompt cannot be empty")
    if not user_prompt.strip():
        raise ValueError("user_prompt cannot be empty")

    now = datetime.now(pytz.UTC)
    await ensure_prompt_indexes()
    current_prompt = await pipeline_prompts_collection.find_one(
        {
            "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
            "prompt_key": prompt_key,
            "is_active": True,
        },
        sort=[("version", -1)],
    )

    if current_prompt:
        await pipeline_prompts_collection.update_one(
            {"_id": current_prompt["_id"]},
            {
                "$set": {
                    "is_active": False,
                    "disabled_at": now,
                    "updated_at": now,
                }
            },
        )

    default_prompt = DEFAULT_PROMPT_CONFIGS[prompt_key]
    next_version = 1 if not current_prompt else int(current_prompt.get("version", 0)) + 1
    new_prompt_document = {
        "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
        "prompt_key": prompt_key,
        "prompt_name": default_prompt["prompt_name"],
        "description": default_prompt["description"],
        "system_prompt": system_prompt.strip(),
        "user_prompt": user_prompt.strip(),
        "version": next_version,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "previous_version_id": current_prompt.get("_id") if current_prompt else None,
        "source": "database",
    }
    insert_result = await pipeline_prompts_collection.insert_one(new_prompt_document)
    created_prompt = await pipeline_prompts_collection.find_one({"_id": insert_result.inserted_id})
    return _serialize_prompt_document(created_prompt)


async def seed_default_pipeline_prompts() -> dict[str, int]:
    await ensure_prompt_indexes()
    inserted_count = 0
    skipped_count = 0
    now = datetime.now(pytz.UTC)

    for prompt_key, prompt_config in DEFAULT_PROMPT_CONFIGS.items():
        existing_prompt = await pipeline_prompts_collection.find_one(
            {
                "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
                "prompt_key": prompt_key,
                "is_active": True,
            },
            sort=[("version", -1)],
        )
        if existing_prompt:
            skipped_count += 1
            continue

        await pipeline_prompts_collection.insert_one(
            {
                "pipeline": constants.GENERATE_METADATA_PIPELINE_NAME,
                "prompt_key": prompt_key,
                "prompt_name": prompt_config["prompt_name"],
                "description": prompt_config["description"],
                "system_prompt": prompt_config["system_prompt"],
                "user_prompt": prompt_config["user_prompt"],
                "version": 1,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
                "source": "database",
            }
        )
        inserted_count += 1

    return {
        "inserted_count": inserted_count,
        "skipped_count": skipped_count,
    }