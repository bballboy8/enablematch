from pydantic import BaseModel



class CandidateAnalysisRequestBody(BaseModel):
    job_description: str

class CandidateSuggestionsRequestBody(BaseModel):
    job_description: str