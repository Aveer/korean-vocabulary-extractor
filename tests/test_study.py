"""Tests for the study subsystem."""

from __future__ import annotations

import importlib
import sqlite3

from fastapi.testclient import TestClient


def _make_client(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    config_paths = importlib.import_module("config_paths")
    study_db = importlib.import_module("study.db")
    extract_vocab = importlib.import_module("api.extract_vocab")
    study_api = importlib.import_module("api.study")
    main_mod = importlib.import_module("main")

    importlib.reload(config_paths)
    importlib.reload(study_db)
    importlib.reload(study_api)
    importlib.reload(extract_vocab)
    importlib.reload(main_mod)
    return TestClient(main_mod.app)


def test_schema_init_and_no_raw_text_persistence(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    unique_text = "고유문장12345. 사과를 먹었다."
    client.get("/api/study/stats")
    client.post(
        "/api/extract-vocab",
        json={"text": unique_text, "targetLevel": "ANY", "wordCount": 2, "includeSentenceTranslation": False},
    )
    db_path = tmp_path / "KoreanVocabExtractor" / "study.sqlite3"
    assert db_path.exists()
    with open(db_path, "rb") as f:
        assert unique_text.encode("utf-8") not in f.read()


def test_save_list_and_review_flow(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    extraction = client.post(
        "/api/extract-vocab",
        json={"text": "사과를 먹었다. 바나나도 먹었다.", "targetLevel": "ANY", "wordCount": 3, "includeSentenceTranslation": False},
    ).json()
    card = extraction["cards"][0]
    saved = client.post("/api/study/cards", json=card).json()
    assert saved["id"] > 0
    assert saved["englishGlosses"] == card["englishGlosses"]
    assert saved["studyLine"]
    assert saved["difficultyScore"] >= 1.0
    assert saved["frequencyInText"] >= 1
    assert saved["reason"]
    listed = client.get("/api/study/cards").json()["cards"]
    assert len(listed) == 1
    assert listed[0]["englishGlosses"] == card["englishGlosses"]
    due = client.get("/api/study/reviews/due").json()
    assert due["dueCount"] == 1
    assert due["cards"][0]["englishGlosses"] == card["englishGlosses"]
    assert due["cards"][0]["studyLine"]
    review = client.post(f"/api/study/reviews/{saved['id']}", json={"rating": "good"}).json()
    assert review["intervalDays"] >= 1
    saved_again = client.post("/api/study/cards", json=card).json()
    assert saved_again["id"] == saved["id"]
    assert saved_again["intervalDays"] == review["intervalDays"]
    assert saved_again["repetitions"] >= 1
    assert client.get("/api/study/reviews/due").json()["dueCount"] == 0
    stats = client.get("/api/study/stats").json()
    assert stats["totalCards"] == 1
    assert stats["xp"] > 0


def test_known_and_ignored_filter_behavior(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    extracted = client.post(
        "/api/extract-vocab",
        json={"text": "사과를 먹었다. 바나나도 먹었다.", "targetLevel": "ANY", "wordCount": 5, "includeSentenceTranslation": False},
    ).json()
    lemma = extracted["cards"][0]["lemma"]
    saved = client.post("/api/study/cards", json=extracted["cards"][0]).json()
    assert saved["studyStatus"] == "new"
    assert client.get("/api/study/reviews/due").json()["dueCount"] >= 1
    client.put(f"/api/study/lemmas/{lemma}/status", json={"status": "known"})
    assert client.get("/api/study/reviews/due").json()["dueCount"] == 0
    assert client.get("/api/study/stats").json()["dueCount"] == 0
    filtered = client.post(
        "/api/extract-vocab",
        json={"text": "사과를 먹었다. 바나나도 먹었다.", "targetLevel": "ANY", "wordCount": 5, "includeSentenceTranslation": False},
    ).json()
    assert all(card["lemma"] != lemma for card in filtered["cards"])
    unfiltered = client.post(
        "/api/extract-vocab",
        json={"text": "사과를 먹었다. 바나나도 먹었다.", "targetLevel": "ANY", "wordCount": 5, "includeSentenceTranslation": False, "excludeKnown": False},
    ).json()
    assert any(card["lemma"] == lemma for card in unfiltered["cards"])


def test_dictionary_config_uses_frontend_aliases(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    config = client.get("/api/dictionary-config").json()
    assert "apiKeySet" in config
    assert "bundledAvailable" in config
    assert "bundledEntryCount" in config
    assert "bundledSource" in config
    assert "api_key_set" not in config
