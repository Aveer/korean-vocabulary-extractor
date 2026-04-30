"""Korean Vocab Extractor — Packaged Application Entrypoint.

This module serves as the entry point for the packaged Windows application.
It starts the FastAPI backend, serves the built frontend as static files,
and opens the default browser automatically.

Usage (development):
    python run_app.py

Usage (packaged):
    KoreanVocabExtractor.exe
"""

import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Resolve paths relative to the running executable (PyInstaller) or script
if getattr(sys, "frozen", False):
    # Running as PyInstaller package
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as script in development
    BASE_DIR = Path(__file__).parent

FRONTEND_DIST = BASE_DIR / "frontend_dist"
HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _find_free_port(start_port: int = DEFAULT_PORT, max_attempts: int = 10) -> int:
    """Find an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return port
            except OSError:
                continue
    raise OSError(f"No free port found in range {start_port}-{start_port + max_attempts}")


def _build_app() -> FastAPI:
    """Build the FastAPI application with static file serving."""
    from api.extract_vocab import router as extract_router
    from config_paths import get_config_path, get_cache_file

    # Print config paths for debugging
    print(f"Config: {get_config_path()}")
    print(f"Cache:  {get_cache_file()}")

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

    # API health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    # Include API routes
    app.include_router(extract_router, prefix="/api")

    # Serve frontend static files
    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
    else:
        # Fallback: return a helpful message if frontend is not built
        @app.get("/")
        async def fallback_root():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Frontend not built. Run 'npm run build' in the frontend/ directory.",
                    "health": "http://localhost:{port}/api/health".format(port=DEFAULT_PORT),
                },
            )

    return app


def run(port: int = DEFAULT_PORT, open_browser: bool = True):
    """Start the Korean Vocab Extractor application.

    Args:
        port: TCP port to listen on (default: 8765).
        open_browser: Whether to open the default browser automatically.
    """
    actual_port = _find_free_port(port)
    url = f"http://{HOST}:{actual_port}"

    app = _build_app()

    print("=" * 50)
    print("  Korean Vocab Extractor")
    print("=" * 50)
    print(f"  Server: {url}")
    print(f"  API:    {url}/api/extract-vocab")
    print(f"  Health: {url}/api/health")
    print("=" * 50)
    print("  Press Ctrl+C to stop.")
    print("=" * 50)

    if open_browser:
        def _open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(url)
        threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(
        app,
        host=HOST,
        port=actual_port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    run()
