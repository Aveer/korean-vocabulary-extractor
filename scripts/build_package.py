#!/usr/bin/env python3
"""Build, smoke-test, and zip the packaged Korean Vocab Extractor app.

Run this script from any directory with the Python environment that should build
the app. On Windows it produces `dist/KoreanVocabExtractor/KoreanVocabExtractor.exe`;
on Linux/macOS it produces the platform-native executable with the same name.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


APP_NAME = "KoreanVocabExtractor"
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_REQUIREMENTS = ROOT_DIR / "backend" / "requirements.txt"
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
SPEC_FILE = ROOT_DIR / f"{APP_NAME}.spec"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
APP_DIR = DIST_DIR / APP_NAME


def _executable_name() -> str:
    return f"{APP_NAME}.exe" if os.name == "nt" else APP_NAME


def _command_name(name: str) -> str:
    return f"{name}.cmd" if os.name == "nt" else name


def _run(command: list[str | Path], cwd: Path = ROOT_DIR) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"\n> {printable}")
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def _ensure_frontend(skip_frontend: bool) -> None:
    if skip_frontend:
        if not (FRONTEND_DIST / "index.html").exists():
            raise RuntimeError("frontend/dist/index.html is missing; run without --skip-frontend")
        print(f"Frontend build already present: {FRONTEND_DIST}")
        return

    npm = _command_name("npm")
    _run([npm, "ci", "--prefer-offline"], cwd=FRONTEND_DIR)
    _run([npm, "run", "build"], cwd=FRONTEND_DIR)
    if not (FRONTEND_DIST / "index.html").exists():
        raise RuntimeError("frontend build did not create frontend/dist/index.html")


def _ensure_python_deps(skip_python_install: bool) -> None:
    if skip_python_install:
        print("Skipping Python dependency installation.")
        return
    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    _run([sys.executable, "-m", "pip", "install", "-r", BACKEND_REQUIREMENTS])


def _clean_outputs(clean: bool) -> None:
    if not clean:
        return
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    print("Removed previous PyInstaller dist/ and build/ outputs.")


def _build_with_pyinstaller() -> Path:
    if not SPEC_FILE.exists():
        raise RuntimeError(f"PyInstaller spec not found: {SPEC_FILE}")

    _run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", SPEC_FILE])
    executable = APP_DIR / _executable_name()
    if not executable.exists():
        raise RuntimeError(f"Packaged executable not found: {executable}")
    return executable


def _find_free_port(start_port: int) -> int:
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + 49}")


def _read_url(url: str, timeout: float = 10.0) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def _read_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    return json.loads(_read_url(url, timeout=timeout).decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any], timeout: float = 20.0) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _put_json(url: str, payload: dict[str, Any], timeout: float = 20.0) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _collect_process_output(process: subprocess.Popen[str]) -> str:
    if not process.stdout:
        return ""
    try:
        return process.stdout.read()
    except OSError:
        return ""


def _smoke_test(executable: Path, start_port: int, timeout: float, label: str = "packaged app") -> None:
    port = _find_free_port(start_port)
    base_url = f"http://127.0.0.1:{port}"
    command = [str(executable), "--no-browser", "--port", str(port)]

    print(f"\nSmoke-testing {label} at {base_url}")
    smoke_env = os.environ.copy()

    with tempfile.TemporaryDirectory(prefix="kve-smoke-data-") as smoke_data_dir:
        smoke_env["KVE_DATA_DIR"] = smoke_data_dir
        process = subprocess.Popen(
            command,
            cwd=executable.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=smoke_env,
        )

        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    output = _collect_process_output(process)
                    raise RuntimeError(f"packaged app exited before health check passed\n{output}")
                try:
                    health = _read_json(f"{base_url}/api/health", timeout=2.0)
                    if health.get("status") == "ok":
                        break
                except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                    time.sleep(1)
            else:
                raise RuntimeError(f"health check did not pass within {timeout:.0f}s")

            index_html = _read_url(f"{base_url}/", timeout=10.0).decode("utf-8", errors="replace")
            if "Korean Vocab Extractor" not in index_html:
                raise RuntimeError("frontend smoke test did not return the app HTML")

            dictionary_config = _read_json(f"{base_url}/api/dictionary-config", timeout=10.0)
            if not dictionary_config.get("bundledAvailable"):
                raise RuntimeError(f"bundled dictionary is unavailable in packaged app: {dictionary_config}")
            if dictionary_config.get("bundledEntryCount", 0) <= 0:
                raise RuntimeError(f"bundled dictionary has no entries in packaged app: {dictionary_config}")

            extraction = _post_json(
                f"{base_url}/api/extract-vocab",
                {
                    "text": "한국어 학습을 시작했습니다.",
                    "targetLevel": "ANY",
                    "wordCount": 3,
                    "includeSentenceTranslation": False,
                },
                timeout=30.0,
            )
            returned_count = extraction.get("meta", {}).get("returnedCount", 0)
            if returned_count < 1 or not extraction.get("cards"):
                raise RuntimeError(f"extraction smoke test returned no cards: {extraction}")
            stats_before = _read_json(f"{base_url}/api/study/stats", timeout=10.0)
            card = extraction["cards"][0]
            saved = _post_json(
                f"{base_url}/api/study/cards",
                {
                    "lemma": card["lemma"],
                    "sourceFragment": card["sourceFragment"],
                    "sourceSentence": card["sourceSentence"],
                    "display": card["display"],
                    "pos": card["pos"],
                    "level": card.get("level"),
                    "englishGlosses": card.get("englishGlosses", []),
                    "koreanDefinition": card.get("koreanDefinition"),
                    "sourceFragmentTranslation": card.get("sourceFragmentTranslation"),
                    "sourceSentenceTranslation": card.get("sourceSentenceTranslation"),
                    "studyLine": card.get("studyLine"),
                    "csvFront": card.get("csvFront"),
                    "csvBack": card.get("csvBack"),
                },
                timeout=20.0,
            )
            due = _read_json(f"{base_url}/api/study/reviews/due?limit=5", timeout=10.0)
            if due.get("dueCount", 0) < 1:
                raise RuntimeError(f"study due review smoke test returned no due cards: {due}")
            review = _post_json(f"{base_url}/api/study/reviews/{saved['id']}", {"rating": "good"}, timeout=20.0)
            if review.get("intervalDays", 0) < 1:
                raise RuntimeError(f"study review smoke test failed: {review}")
            stats_after = _read_json(f"{base_url}/api/study/stats", timeout=10.0)
            expected_xp = stats_before.get("xp", 0) + review.get("xpGained", 0)
            if stats_after.get("xp", 0) < expected_xp:
                raise RuntimeError("study stats smoke test did not include review XP")
            entry_count = dictionary_config.get("bundledEntryCount")
            print(
                "Smoke test passed: health, frontend, bundled dictionary "
                f"({entry_count} entries), extraction ({returned_count} cards), and study APIs."
            )
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


def _zip_app() -> Path:
    if not APP_DIR.exists():
        raise RuntimeError(f"App directory not found: {APP_DIR}")

    zip_path = DIST_DIR / f"{APP_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in APP_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(APP_DIR.parent))

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"ZIP created: {zip_path} ({size_mb:.2f} MB)")
    return zip_path


def _smoke_test_zip(zip_path: Path, start_port: int, timeout: float) -> None:
    if not zip_path.exists():
        raise RuntimeError(f"ZIP file not found for smoke test: {zip_path}")

    with tempfile.TemporaryDirectory(prefix="kve-zip-smoke-") as extract_dir:
        extract_root = Path(extract_dir)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)

        executable = extract_root / APP_NAME / _executable_name()
        if not executable.exists():
            matches = list(extract_root.rglob(_executable_name()))
            if not matches:
                raise RuntimeError(f"Extracted ZIP does not contain {_executable_name()}: {zip_path}")
            executable = matches[0]

        if os.name != "nt":
            executable.chmod(executable.stat().st_mode | 0o111)

        _smoke_test(executable, start_port, timeout, label="extracted ZIP")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and smoke-test the packaged app")
    parser.add_argument("--skip-frontend", action="store_true", help="reuse existing frontend/dist output")
    parser.add_argument("--skip-python-install", action="store_true", help="do not install backend requirements")
    parser.add_argument("--clean", action="store_true", help="remove previous dist/ and build/ outputs first")
    parser.add_argument("--no-smoke", action="store_true", help="skip packaged executable smoke test")
    parser.add_argument("--smoke-port", type=int, default=18765, help="first local port to try for smoke tests")
    parser.add_argument("--smoke-timeout", type=float, default=120.0, help="seconds to wait for packaged app startup")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    _clean_outputs(args.clean)
    _ensure_frontend(args.skip_frontend)
    _ensure_python_deps(args.skip_python_install)
    executable = _build_with_pyinstaller()
    if args.no_smoke:
        print("Skipping executable smoke test.")
    else:
        _smoke_test(executable, args.smoke_port, args.smoke_timeout)
    zip_path = _zip_app()
    if not args.no_smoke:
        _smoke_test_zip(zip_path, args.smoke_port + 100, args.smoke_timeout)

    print("\nBuild output:")
    print(f"  App folder: {APP_DIR}")
    print(f"  Executable: {executable}")
    print(f"  ZIP file:   {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
