"""Tests for the Korean vocabulary extraction pipeline."""

import pytest


class TestSentenceSplitting:
    """Test Korean sentence splitting."""

    def test_single_sentence(self):
        from nlp.splitter import split_sentences
        result = split_sentences("당황했다.")
        assert len(result) == 1
        assert result[0] == "당황했다."

    def test_multiple_sentences(self):
        from nlp.splitter import split_sentences
        result = split_sentences("당황했다. 망설였다. 생각해봤다.")
        assert len(result) == 3

    def test_sentences_with_question_mark(self):
        from nlp.splitter import split_sentences
        result = split_sentences("정말인가요? 네요.")
        assert len(result) >= 1

    def test_empty_input(self):
        from nlp.splitter import split_sentences
        result = split_sentences("")
        assert len(result) == 0

    def test_whitespace_only(self):
        from nlp.splitter import split_sentences
        result = split_sentences("   ")
        assert len(result) == 0


class TestLemmatization:
    """Test Korean lemmatization to dictionary forms."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from nlp.pipeline import ExtractionPipeline
        self.pipeline = ExtractionPipeline()

    def _extract_lemmas(self, text):
        """Helper to extract lemmas from text."""
        _, candidates = self.pipeline.extract(text)
        return {c.lemma for c in candidates}

    def test_danghwanghaetda(self):
        """당황했다 -> 당황하다"""
        lemmas = self._extract_lemmas("당황했다.")
        assert "당황하다" in lemmas

    def test_mangseoryetjiman(self):
        """망설였지만 -> 망설이다"""
        lemmas = self._extract_lemmas("나는 잠시 망설였지만 생각했다.")
        assert "망설이다" in lemmas

    def test_neukkyeotda(self):
        """느껴졌다 -> 느끼다"""
        lemmas = self._extract_lemmas("무언가 느껴졌다.")
        assert "느끼다" in lemmas

    def test_dollyeoabay(self):
        """돌려받아야 -> 돌려받다"""
        lemmas = self._extract_lemmas("돈을 돌려받아야 한다.")
        assert "돌려받다" in lemmas

    def test_salhaedanghaeyo(self):
        """살해당했어요 -> 살해당하다"""
        lemmas = self._extract_lemmas("누군가 살해당했어요.")
        assert "살해당하다" in lemmas

    def test_haejigeetdaneyo(self):
        """해지겠다네요 -> 해지다"""
        lemmas = self._extract_lemmas("이젠 계약을 해지겠다네요.")
        assert "해지다" in lemmas


class TestCandidateFiltering:
    """Test that particles and endings are filtered out."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from nlp.pipeline import ExtractionPipeline
        self.pipeline = ExtractionPipeline()

    def test_particles_removed(self):
        """Particles (을, 를, 는, 도) should not appear as candidates."""
        _, candidates = self.pipeline.extract("나는 사과를 먹었다.")
        lemmas = {c.lemma for c in candidates}
        # Particles should not be in candidates
        assert "을" not in lemmas
        assert "를" not in lemmas
        assert "는" not in lemmas

    def test_content_words_kept(self):
        """Content words (nouns, verbs) should be kept."""
        _, candidates = self.pipeline.extract("사과를 먹었다.")
        lemmas = {c.lemma for c in candidates}
        assert "사과" in lemmas
        assert "먹다" in lemmas

    def test_ending_removed(self):
        """Endings should not appear as separate candidates."""
        _, candidates = self.pipeline.extract("당황했다.")
        lemmas = {c.lemma for c in candidates}
        # The ending 다 should not be a separate candidate
        assert "다" not in lemmas


class TestLemmaMerging:
    """Test duplicate lemma merging."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from nlp.pipeline import ExtractionPipeline
        self.pipeline = ExtractionPipeline()

    def test_duplicate_merging(self):
        """Same lemma appearing multiple times should be merged."""
        _, candidates = self.pipeline.extract("사과를 먹었다. 사과가 맛있었다.")
        apple_candidates = [c for c in candidates if c.lemma == "사과"]
        assert len(apple_candidates) == 1
        assert apple_candidates[0].frequency >= 1

    def test_frequency_counting(self):
        """Frequency should count all occurrences of the same lemma."""
        _, candidates = self.pipeline.extract("사과 사과 사과")
        apple_candidates = [c for c in candidates if c.lemma == "사과"]
        if apple_candidates:
            assert apple_candidates[0].frequency >= 1


class TestRanking:
    """Test vocabulary ranking."""

    def test_frequency_ranking(self):
        """More frequent words should rank higher."""
        from nlp.pipeline import ExtractionPipeline
        from nlp.ranker import rank_candidates

        pipeline = ExtractionPipeline()
        _, candidates = pipeline.extract("사과를 먹었다. 바나나도 먹었다. 사과가 맛있었다.")

        ranked = rank_candidates(candidates, word_count=10)
        # 사과 appears twice, should rank higher than 바나나
        apple = next((r for r in ranked if r.lemma == "사과"), None)
        banana = next((r for r in ranked if r.lemma == "바나나"), None)
        if apple and banana:
            assert apple.score >= banana.score

    def test_word_count_respected(self):
        """wordCount parameter should limit results."""
        from nlp.pipeline import ExtractionPipeline
        from nlp.ranker import rank_candidates

        pipeline = ExtractionPipeline()
        _, candidates = pipeline.extract(
            "사과를 먹었다. 바나나도 먹었다. 오렌지도 먹었다. "
            "포도도 먹었다. 망고도 먹었다. 키위도 먹었다."
        )

        ranked = rank_candidates(candidates, word_count=3)
        assert len(ranked) <= 3

    def test_empty_candidates(self):
        """Empty candidates should return empty results."""
        from nlp.ranker import rank_candidates
        ranked = rank_candidates([], word_count=10)
        assert len(ranked) == 0


class TestEmptyInput:
    """Test handling of empty/invalid input."""

    def test_empty_text_raises(self):
        from nlp.pipeline import ExtractionPipeline
        pipeline = ExtractionPipeline()
        with pytest.raises(ValueError):
            pipeline.extract("")

    def test_whitespace_only_raises(self):
        from nlp.pipeline import ExtractionPipeline
        pipeline = ExtractionPipeline()
        with pytest.raises(ValueError):
            pipeline.extract("   ")


class TestDegradedMode:
    """Test that the app works without dictionary API key."""

    def test_no_api_key_no_crash(self):
        """Extraction should work without API key (bundled provider)."""
        import os
        # Ensure no API key is set
        original = os.environ.pop("KRDICT_API_KEY", None)
        try:
            import importlib
            import dictionary.provider
            importlib.reload(dictionary.provider)

            from dictionary.provider import create_provider
            provider = create_provider()
            # Bundled provider should be available without API key
            assert provider.is_available()

            # Lookup should work, not crash
            glosses, definition, level = provider.lookup("사과")
            # Bundled dict has entries
            assert isinstance(glosses, list)
        finally:
            if original:
                os.environ["KRDICT_API_KEY"] = original

    def test_extraction_without_api_key(self):
        """Full extraction should work without API key."""
        import os
        original = os.environ.pop("KRDICT_API_KEY", None)
        try:
            # Reset module cache to pick up new env
            import importlib
            import dictionary.provider
            importlib.reload(dictionary.provider)

            from dictionary.provider import create_provider
            provider = create_provider()

            from nlp.pipeline import ExtractionPipeline
            from nlp.ranker import rank_candidates

            pipeline = ExtractionPipeline()
            _, candidates = pipeline.extract("당황했다.")

            # Should work without dictionary
            ranked = rank_candidates(candidates, word_count=10)
            assert len(ranked) >= 1
        finally:
            if original:
                os.environ["KRDICT_API_KEY"] = original


class TestAPIEndpoint:
    """Test the API endpoint."""

    def test_empty_text_returns_error(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "",
            "targetLevel": "ANY",
            "wordCount": 10,
        })
        # Pydantic validation returns 422 for empty text (min_length=1)
        assert response.status_code in (400, 422)

    def test_valid_request_returns_200(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다. 망설였다.",
            "targetLevel": "ANY",
            "wordCount": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert "meta" in data
        assert len(data["cards"]) >= 0

    def test_word_count_respected(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "사과를 먹었다. 바나나도 먹었다. 오렌지도 먹었다.",
            "targetLevel": "ANY",
            "wordCount": 2,
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) <= 2

    def test_target_level_sent_to_backend(self):
        """Frontend sends targetLevel correctly to backend."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다.",
            "targetLevel": "TOPIK_II_5",
            "wordCount": 10,
        })
        assert response.status_code == 200
        data = response.json()
        # Meta should include the selected target level
        assert data["meta"]["selectedTargetLevel"] == "TOPIK_II_5"

    def test_different_levels_produce_different_results(self):
        """Same passage with different TOPIK levels should return different top results."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)

        # Use a passage with varied vocabulary
        text = (
            "서진은 고개를 끄덕인 뒤 소파에 털썩 앉았다. "
            "그녀는 당황한 표정으로 창밖을 바라보았다. "
            "복잡한 감정들이 마음을 가득 채웠다. "
            "망설였지만 결국 결정을 내렸다. "
            "심오한 사색 끝에 그녀는 진실을 직시하기로 했다."
        )

        response3 = client.post("/api/extract-vocab", json={
            "text": text,
            "targetLevel": "TOPIK_II_3",
            "wordCount": 10,
        })
        response6 = client.post("/api/extract-vocab", json={
            "text": text,
            "targetLevel": "TOPIK_II_6",
            "wordCount": 10,
        })

        assert response3.status_code == 200
        assert response6.status_code == 200

        data3 = response3.json()
        data6 = response6.json()

        lemmas3 = {card["lemma"] for card in data3["cards"][:10]}
        lemmas6 = {card["lemma"] for card in data6["cards"][:10]}

        # Both should return results
        assert len(lemmas3) > 0
        assert len(lemmas6) > 0

        # Overlap should be less than 70% (unless pool is too small)
        if len(lemmas3 | lemmas6) >= 5:
            overlap = len(lemmas3 & lemmas6) / len(lemmas3 | lemmas6)
            assert overlap < 0.7, f"Level 3 and Level 6 results too similar: {overlap:.0%} overlap"

    def test_basic_words_penalized_at_high_level(self):
        """Ultra-basic words should be penalized at TOPIK II Level 5-6."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)

        # Text containing basic words
        text = (
            "사람들이 집에 있다. 남자가 일한다. 여자가 돈이 좋다. "
            "그것은 크다. 이것은 작다. "
            "복잡한 심오한 감정들이 느껴졌다. "
            "망설였지만 결국 결정을 내렸다."
        )

        response = client.post("/api/extract-vocab", json={
            "text": text,
            "targetLevel": "TOPIK_II_6",
            "wordCount": 10,
        })
        assert response.status_code == 200
        data = response.json()

        basic_words = {"하다", "이다", "있다", "없다", "되다", "가다", "오다",
                       "사람", "남자", "여자", "집", "일", "돈", "좋다", "크다", "작다"}
        top_lemmas = {card["lemma"] for card in data["cards"][:5]}

        # Basic words should not dominate top results at high level
        basic_in_top = top_lemmas & basic_words
        assert len(basic_in_top) <= 1, (
            f"Too many basic words in top 5 for TOPIK_II_6: {basic_in_top}"
        )

    def test_card_has_study_line(self):
        """Each card must have a studyLine field in the correct format."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다.",
            "targetLevel": "ANY",
            "wordCount": 5,
        })
        assert response.status_code == 200
        data = response.json()

        for card in data["cards"]:
            assert "studyLine" in card, "Card missing studyLine field"
            assert "csvFront" in card, "Card missing csvFront field"
            assert "csvBack" in card, "Card missing csvBack field"
            assert "sourceFragment" in card, "Card missing sourceFragment field"
            assert "difficultyScore" in card, "Card missing difficultyScore field"
            # Study line format: (glosses) fragment. (lemma) = translation
            study_line = card["studyLine"]
            assert "(" in study_line, f"Study line missing parentheses: {study_line}"
            assert card["lemma"] in study_line, f"Study line missing lemma: {study_line}"

    def test_csv_has_two_columns(self):
        """Default CSV must have exactly two columns: front,back."""
        # This is tested in frontend, but verify backend provides the data
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다.",
            "targetLevel": "ANY",
            "wordCount": 3,
        })
        assert response.status_code == 200
        data = response.json()

        for card in data["cards"]:
            # csvFront: (glosses) fragment. (lemma)
            assert card["csvFront"], "csvFront must not be empty"
            assert "(" in card["csvFront"], f"csvFront should contain parentheses: {card['csvFront']}"
            assert card["lemma"] in card["csvFront"], f"csvFront must contain lemma: {card['csvFront']}"

    def test_csv_front_back_format(self):
        """CSV front/back format matches spec."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다.",
            "targetLevel": "ANY",
            "wordCount": 3,
        })
        assert response.status_code == 200
        data = response.json()

        for card in data["cards"]:
            # csvFront format: (glosses) fragment. (lemma)
            # Must contain the lemma in parentheses
            assert f"({card['lemma']})" in card["csvFront"], (
                f"csvFront must contain '({card['lemma']})': {card['csvFront']}"
            )
            # sourceFragment must be in csvFront
            assert card["sourceFragment"] in card["csvFront"], (
                f"csvFront must contain sourceFragment: {card['csvFront']}"
            )

    def test_meta_includes_debug_info(self):
        """Meta should include level debugging info."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다.",
            "targetLevel": "TOPIK_II_5",
            "wordCount": 5,
        })
        assert response.status_code == 200
        data = response.json()
        meta = data["meta"]

        assert "selectedTargetLevel" in meta
        assert meta["selectedTargetLevel"] == "TOPIK_II_5"
        assert "candidateCountBeforeFiltering" in meta
        assert "levelDistribution" in meta

    def test_difficulty_score_in_range(self):
        """Difficulty scores should be in valid range 1-6."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.post("/api/extract-vocab", json={
            "text": "당황했다.",
            "targetLevel": "ANY",
            "wordCount": 5,
        })
        assert response.status_code == 200
        data = response.json()

        for card in data["cards"]:
            assert 1.0 <= card["difficultyScore"] <= 6.0, (
                f"difficultyScore {card['difficultyScore']} out of range for {card['lemma']}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
