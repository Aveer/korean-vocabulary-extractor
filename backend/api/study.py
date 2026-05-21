"""Study subsystem API routes."""

from fastapi import APIRouter, HTTPException, Query

from api.models import StudyCardRequest, StudyCardResponse, StudyCardsResponse, StudyDueResponse, StudyLemmaStatusRequest, StudyLemmaStatusResponse, StudyReviewRequest, StudyReviewResponse, StudyStatsResponse
from study.service import count_cards, delete_card, due_reviews, list_cards, review_card, save_card, set_lemma_status, stats

router = APIRouter()


@router.post("/cards", response_model=StudyCardResponse)
async def create_card(request: StudyCardRequest):
    card = save_card(request.model_dump(by_alias=True, exclude_none=True))
    return StudyCardResponse(**card)


@router.get("/cards", response_model=StudyCardsResponse)
async def get_cards(limit: int = Query(100, ge=0, le=500), offset: int = Query(0, ge=0)):
    cards = list_cards(limit=limit, offset=offset)
    return StudyCardsResponse(cards=[StudyCardResponse(**card) for card in cards], total=count_cards())


@router.delete("/cards/{card_id}")
async def remove_card(card_id: int):
    if not delete_card(card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"deleted": True}


@router.put("/lemmas/{lemma}/status", response_model=StudyLemmaStatusResponse)
async def update_lemma_status(lemma: str, payload: StudyLemmaStatusRequest):
    try:
        return StudyLemmaStatusResponse(**set_lemma_status(lemma, payload.status))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/reviews/due", response_model=StudyDueResponse)
async def get_due(limit: int = Query(20, ge=1, le=100)):
    data = due_reviews(limit=limit)
    return StudyDueResponse(dueCount=data["dueCount"], cards=[StudyCardResponse(**card) for card in data["cards"]])


@router.post("/reviews/{card_id}", response_model=StudyReviewResponse)
async def submit_review(card_id: int, payload: StudyReviewRequest):
    try:
        return StudyReviewResponse(**review_card(card_id, payload.rating))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/stats", response_model=StudyStatsResponse)
async def get_stats():
    return StudyStatsResponse(**stats())
