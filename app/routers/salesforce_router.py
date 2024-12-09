from fastapi import APIRouter
from controllers.salesforce_controller import router as salesforce_router

router = APIRouter()

router.include_router(salesforce_router, prefix="/salesforce", tags=["Salesforce"])
