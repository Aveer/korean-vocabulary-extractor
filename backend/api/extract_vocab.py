"""API endpoints for vocabulary extraction and dictionary configuration."""

from fastapi import APIRouter, HTTPException

from api.models import (
    ExtractVocabRequest,
    ExtractVocabResponse,
    VocabCard,
    ExtractMeta,
    DictionaryConfigRequest,
    DictionaryConfigResponse,
)
from nlp.pipeline import ExtractionPipeline
from nlp.ranker import rank_candidates
from nlp.translator import SentenceTranslator
from dictionary.provider import create_provider, get_config, save_config
from dictionary.bundled import BundledProvider
from study.service import get_lemma_status, get_saved_card_id

router = APIRouter()

# Lazy initialization
_pipeline = None
_provider = None


def _get_pipeline() -> ExtractionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ExtractionPipeline()
    return _pipeline


def _get_provider():
    global _provider
    if _provider is None:
        _provider = create_provider()
    return _provider


def _build_study_line(card_data: dict) -> str:
    """Build study line: '(glosses) Korean fragment. (lemma) = English translation.'"""
    glosses = ", ".join(card_data.get("english_glosses", []))
    gloss_part = f"({glosses})" if glosses else "(—)"
    fragment = card_data.get("source_fragment", card_data.get("source_sentence", ""))
    lemma = card_data.get("lemma", "")
    translation = card_data.get("source_fragment_translation", "")

    line = f"{gloss_part} {fragment} ({lemma})"
    if translation:
        line += f" = {translation}"
    return line.strip()


def _build_csv_fields(card_data: dict) -> tuple[str, str]:
    """Build CSV front/back fields."""
    glosses = ", ".join(card_data.get("english_glosses", []))
    gloss_part = f"({glosses})" if glosses else "(—)"
    fragment = card_data.get("source_fragment", card_data.get("source_sentence", ""))
    lemma = card_data.get("lemma", "")
    translation = card_data.get("source_fragment_translation", "")

    front = f"{gloss_part} {fragment} ({lemma})".strip()
    back = translation.strip() if translation else ""
    return front, back


@router.post("/extract-vocab", response_model=ExtractVocabResponse)
async def extract_vocab(request: ExtractVocabRequest):
    """Extract vocabulary from Korean text.

    Runs the full extraction pipeline:
    1. Input normalization
    2. Sentence splitting
    3. Morphological analysis (Kiwi)
    4. Candidate filtering
    5. Lemmatization & merging
    6. Dictionary lookup
    7. Ranking (level-aware)
    8. Format output with study lines
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Please provide Korean text")

    if len(request.text) > 100000:
        raise HTTPException(
            status_code=400,
            detail="Input text is too long (max 100,000 characters)",
        )

    try:
        return _extract(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not extract vocabulary: {str(e)}",
        )


def _extract(request: ExtractVocabRequest) -> ExtractVocabResponse:
    """Run the full extraction pipeline."""
    pipeline = _get_pipeline()
    provider = _get_provider()

    # Stages 1-5: NLP pipeline (normalize, split, tokenize, filter, merge)
    sentences, candidates = pipeline.extract(request.text)

    candidate_count_before = len(candidates)

    if not candidates:
        return ExtractVocabResponse(
            cards=[],
            meta=ExtractMeta(
                inputLength=len(request.text),
                candidateCount=0,
                returnedCount=0,
                dictionaryProvider="none",
                selectedTargetLevel=request.target_level,
                candidateCountBeforeFiltering=candidate_count_before,
            ),
        )

    # Stage 6: Dictionary lookup function
    def dict_lookup(lemma: str):
        return provider.lookup(lemma)

    # Stage 7-8: Ranking (level-aware)
    ranked = rank_candidates(
        candidates,
        target_level=request.target_level,
        word_count=max(request.word_count * 3, request.word_count),
        dictionary_lookup=dict_lookup if provider.is_available() else None,
    )

    # Build level distribution for debug metadata
    level_distribution = {}
    for rc in ranked:
        level = rc.level or "unknown"
        level_distribution[level] = level_distribution.get(level, 0) + 1

    # Filter by study status after ranking, before final formatting
    filtered = []
    for rc in ranked:
        status = get_lemma_status(rc.lemma)
        if status == "known" and request.exclude_known:
            continue
        if status == "ignored" and request.exclude_ignored:
            continue
        filtered.append((rc, status))
        if len(filtered) >= request.word_count:
            break

    # Stage 9: Format output with study lines
    translator = SentenceTranslator() if request.include_sentence_translation else None
    cards = []
    for rc, status in filtered:
        fragment = rc.source_fragment or rc.first_sentence
        sentence = rc.first_sentence
        if translator is not None:
            fragment_translation = translator.translate(fragment)
            sentence_translation = (
                translator.translate(sentence)
                if fragment != sentence
                else fragment_translation
            )
        else:
            fragment_translation = None
            sentence_translation = None

        card_data = {
            "lemma": rc.lemma,
            "english_glosses": rc.english_glosses or [],
            "source_fragment": fragment,
            "source_fragment_translation": fragment_translation,
        }

        study_line = _build_study_line(card_data)
        csv_front, csv_back = _build_csv_fields(card_data)

        card = VocabCard(
            lemma=rc.lemma,
            display=rc.display,
            pos=rc.pos,
            englishGlosses=rc.english_glosses or [],
            koreanDefinition=rc.korean_definition,
            sourceSentence=sentence,
            sourceSentenceTranslation=sentence_translation,
            sourceFragment=fragment,
            sourceFragmentTranslation=fragment_translation,
            studyLine=study_line,
            csvFront=csv_front,
            csvBack=csv_back,
            level=rc.level,
            difficultyScore=rc.difficulty_score,
            frequencyInText=rc.frequency,
            reason=rc.reason,
            studyStatus=status,
            savedCardId=get_saved_card_id(rc.lemma, fragment),
        )
        cards.append(card)

    provider_name = type(provider).__name__.replace("Provider", "")

    return ExtractVocabResponse(
        cards=cards,
        meta=ExtractMeta(
            inputLength=len(request.text),
            candidateCount=len(candidates),
            returnedCount=len(cards),
            dictionaryProvider=provider_name,
            selectedTargetLevel=request.target_level,
            candidateCountBeforeFiltering=candidate_count_before,
            levelDistribution=level_distribution,
        ),
    )


@router.get("/dictionary-config", response_model=DictionaryConfigResponse)
async def get_dictionary_config():
    """Get current dictionary configuration."""
    config = get_config()
    bundled = BundledProvider()
    return DictionaryConfigResponse(
        provider=config.get("provider", "bundled"),
        api_key_set=bool(config.get("api_key", "").strip()),
        bundled_available=bundled.is_available(),
        bundled_entry_count=bundled.entry_count,
        bundled_source=bundled.source,
    )


@router.put("/dictionary-config", response_model=DictionaryConfigResponse)
async def set_dictionary_config(request: DictionaryConfigRequest):
    """Update dictionary configuration.

    - provider: 'bundled' or 'nikl'
    - api_key: optional NIKL API key (required if provider is 'nikl')
    """
    if request.provider == "nikl" and not request.api_key:
        raise HTTPException(
            status_code=400,
            detail="API key is required for NIKL provider",
        )

    config = {
        "provider": request.provider,
        "api_key": request.api_key or "",
    }
    save_config(config)

    # Reset provider so next request picks up new config
    global _provider
    _provider = None

    bundled = BundledProvider()
    return DictionaryConfigResponse(
        provider=request.provider,
        api_key_set=bool(request.api_key),
        bundled_available=bundled.is_available(),
        bundled_entry_count=bundled.entry_count,
        bundled_source=bundled.source,
    )
