"""API endpoints for vocabulary extraction."""

from fastapi import APIRouter, HTTPException

from api.models import ExtractVocabRequest, ExtractVocabResponse, VocabCard, ExtractMeta
from nlp.pipeline import ExtractionPipeline
from nlp.ranker import rank_candidates
from dictionary.provider import create_provider

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
    7. Ranking
    8. Format output
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

    if not candidates:
        return ExtractVocabResponse(
            cards=[],
            meta=ExtractMeta(
                input_length=len(request.text),
                candidate_count=0,
                returned_count=0,
                dictionary_provider="none",
            ),
        )

    # Stage 6: Dictionary lookup function
    def dict_lookup(lemma: str):
        return provider.lookup(lemma)

    # Stage 7-8: Ranking
    ranked = rank_candidates(
        candidates,
        target_level=request.target_level,
        word_count=request.word_count,
        dictionary_lookup=dict_lookup if provider.is_available() else None,
    )

    # Stage 9: Format output
    cards = []
    for rc in ranked:
        card = VocabCard(
            lemma=rc.lemma,
            display=rc.display,
            pos=rc.pos,
            english_glosses=rc.english_glosses or [],
            korean_definition=rc.korean_definition,
            source_sentence=rc.first_sentence,
            source_sentence_translation=None,
            level=rc.level,
            frequency_in_text=rc.frequency,
            reason=rc.reason,
        )
        cards.append(card)

    provider_name = "NIKL" if provider.is_available() else "none"

    return ExtractVocabResponse(
        cards=cards,
        meta=ExtractMeta(
            input_length=len(request.text),
            candidate_count=len(candidates),
            returned_count=len(cards),
            dictionary_provider=provider_name,
        ),
    )
