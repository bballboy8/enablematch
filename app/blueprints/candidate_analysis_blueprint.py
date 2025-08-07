from pydantic import BaseModel



class CandidateAnalysisRequestBody(BaseModel):
    job_description: str

class CandidateSuggestionsRequestBody(BaseModel):
    job_description: str
    compensation_range: str
    location: str

class DBCandidateAnalysisRequestBody(BaseModel):
    db_user_id: str
    job_description: str