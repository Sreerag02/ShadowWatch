# created by Deepa

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import EntityResponse, EntitySummaryResponse
from services.entity_service import get_all_entities, get_entity_summary

router = APIRouter(
    prefix="/entities",
    tags=["entities"]
)

@router.get("/", response_model=List[EntityResponse])
def list_entities(db: Session = Depends(get_db)):
    """
    Returns a list of all assessed organizations.
    """
    return get_all_entities(db)

@router.get("/{entity_id}", response_model=EntitySummaryResponse)
def get_entity(entity_id: str, db: Session = Depends(get_db)):
    """
    Returns entity details along with summary counts of its operational data.
    """
    return get_entity_summary(db, entity_id=entity_id)