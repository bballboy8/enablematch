import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auth_router,
    candidate_analysis_router,
    gong_router
)





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