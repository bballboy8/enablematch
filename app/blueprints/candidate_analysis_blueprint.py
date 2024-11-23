from pydantic import BaseModel



class CandidateAnalysisRequestBody(BaseModel):
    job_description: str