import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi_utils.tasks import repeat_every
import services
from config import constants
from routers import (
    auth_router,
    candidate_analysis_router,
    gong_router,
    salesforce_router,
    pinecone_router,
)


@repeat_every(seconds=60*10, wait_first=True)
async def salesforce_user_sync():
    try:
        await asyncio.sleep(60)
        print("Running salesforce_user_sync")
        response = await services.salesforce_service.sync_salesforce_users()
        print(response)
    except Exception as e:
        print(f"Error in salesforce_user_sync: {e}")



async def startup_lifespan():
    pass

project = FastAPI(on_startup=[startup_lifespan])

# Check if static directory is present or not
static_dir = "static"

if not os.path.isdir(static_dir):
    os.makedirs(static_dir)

project.mount("/static", StaticFiles(directory=static_dir), name=static_dir)

# CORS middleware
project.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline Update


# Root endpoint
@project.get("/")
async def read_root():
    return {"message": "Welcome to my FastAPI application!"}


# Include routers
project.include_router(auth_router.router, prefix="/api", tags=["Authentication"])
project.include_router(candidate_analysis_router.router, prefix="/api", tags=["Candidate Analysis"])
project.include_router(gong_router.router, prefix="/api", tags=["Gong"])
project.include_router(salesforce_router.router, prefix="/api", tags=["Salesforce"])
project.include_router(pinecone_router.router, prefix="/api", tags=["Pinecone"])
