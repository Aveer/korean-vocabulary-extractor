"""Korean Vocab Extractor - FastAPI Backend"""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env", override=False)
root_env = ROOT_DIR / ".env"
if root_env != BACKEND_DIR / ".env" and root_env.exists():
    load_dotenv(root_env, override=False)

from api.extract_vocab import router as extract_router
from api.study import router as study_router

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
app.include_router(study_router, prefix="/api/study")
