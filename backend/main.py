"""Korean Vocab Extractor - FastAPI Backend"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.extract_vocab import router as extract_router

app = FastAPI(
    title="Korean Vocab Extractor",
    description="Extract study-ready vocabulary from Korean text",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract_router, prefix="/api")
