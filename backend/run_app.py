"""Korean Vocab Extractor — Packaged Application Entrypoint.

This module serves as the entry point for the packaged desktop application.
It starts the FastAPI backend, serves the built frontend as static files,
and opens the default browser automatically.

Usage (development):
    python run_app.py

Usage (packaged):
    KoreanVocabExtractor.exe
    KoreanVocabExtractor.exe --no-browser --port 8765
"""

import argparse
import os
import socket
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

# Resolve paths and fix sys.path for PyInstaller
if getattr(sys, "frozen", False):
    # Running as PyInstaller package — binaries are alongside the executable
    BASE_DIR = Path(sys.executable).parent
    # Ensure bundled modules are findable
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    # _MEIPASS: temp dir where PyInstaller extracts one-file archives (not needed for onedir)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and str(meipass) not in sys.path:
        sys.path.insert(0, meipass)
else:
    # Running as script in development
    BASE_DIR = Path(__file__).parent
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH, override=False)
root_env = BASE_DIR.parent / ".env"
if root_env != ENV_PATH and root_env.exists():
    load_dotenv(root_env, override=False)

def _find_frontend_dist() -> Path:
    meipass = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    candidates = [
        BASE_DIR / "frontend_dist",
        BASE_DIR.parent / "frontend" / "dist",
        BASE_DIR.parent / "frontend_dist",
        meipass / "frontend_dist",
        meipass / "_internal" / "frontend_dist",
        meipass / "backend" / "frontend_dist",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


HOST = "127.0.0.1"
DEFAULT_PORT = 8765
FRONTEND_DIST = _find_frontend_dist()


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


def _build_app(port: int = DEFAULT_PORT):
    """Build the FastAPI application with static file serving."""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles

    from api.extract_vocab import router as extract_router
    from api.study import router as study_router
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
    app.include_router(study_router, prefix="/api/study")

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
                    "health": "http://localhost:{port}/api/health".format(port=port),
                },
            )

    return app


def run(port: int = DEFAULT_PORT, open_browser: bool = True):
    """Start the Korean Vocab Extractor application."""
    actual_port = _find_free_port(port)
    url = f"http://{HOST}:{actual_port}"

    app = _build_app(actual_port)

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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI options used by package smoke tests and power users."""
    parser = argparse.ArgumentParser(description="Run Korean Vocab Extractor")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="start the local server without opening a browser window",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"preferred local port; the app uses the next free port if busy (default: {DEFAULT_PORT})",
    )
    return parser.parse_args(argv)


def _pause_on_error() -> None:
    """Keep double-clicked console windows open, but never block CI/non-interactive runs."""
    if not getattr(sys, "frozen", False) or not sys.stdin or not sys.stdin.isatty():
        return
    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    try:
        args = _parse_args()
        run(port=args.port, open_browser=not args.no_browser)
    except Exception:
        print("\n" + "=" * 50)
        print("  ERROR: Failed to start")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50)
        try:
            _pause_on_error()
        except EOFError:
            pass
        sys.exit(1)
