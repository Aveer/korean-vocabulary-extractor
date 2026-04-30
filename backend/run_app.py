"""Korean Vocab Extractor — Packaged Application Entrypoint.

This module serves as the entry point for the packaged Windows application.
It starts the FastAPI backend, serves the built frontend as static files,
and opens the default browser automatically.

Usage (development):
    python run_app.py

Usage (packaged):
    KoreanVocabExtractor.exe
"""

import os
import socket
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

# Resolve paths and fix sys.path for PyInstaller
if getattr(sys, "frozen", False):
    # Running as PyInstaller package — binaries are alongside the executable
    BASE_DIR = Path(sys.executable).parent
    # Ensure bundled modules are findable
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    # _MEIPASS: temp dir where PyInstaller extracts one-file archives (not needed for onedir)
    if hasattr(sys, "_MEIPASS"):
        if str(sys._MEIPASS) not in sys.path:
            sys.path.insert(0, sys._MEIPASS)
else:
    # Running as script in development
    BASE_DIR = Path(__file__).parent
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

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


def _build_app():
    """Build the FastAPI application with static file serving."""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles

    from api.extract_vocab import router as extract_router
    from config_paths import get_config_path, get_cache_file

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
        print(f"Frontend: {FRONTEND_DIST}")
    else:
        print(f"WARNING: Frontend not found at {FRONTEND_DIST}")

        @app.get("/")
        async def fallback_root():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Frontend not built.",
                    "health": "http://localhost:{port}/api/health".format(port=DEFAULT_PORT),
                },
            )

    return app


def run(port: int = DEFAULT_PORT, open_browser: bool = True):
    """Start the Korean Vocab Extractor application."""
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

    import uvicorn
    uvicorn.run(
        app,
        host=HOST,
        port=actual_port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("\n" + "=" * 50)
        print("  ERROR: Failed to start")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50)
        print("\nPress Enter to exit...")
        try:
            input()
        except EOFError:
            pass
        sys.exit(1)
