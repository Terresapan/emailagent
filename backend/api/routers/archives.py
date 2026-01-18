from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db import get_db, ArchivedItem
from schemas import ArchivedItemCreate, ArchivedItemResponse

router = APIRouter()

@router.post("/", response_model=ArchivedItemResponse)
def archive_item(item: ArchivedItemCreate, db: Session = Depends(get_db)):
    """Archive an intelligence item."""
    # Check if already exists
    exists = db.query(ArchivedItem).filter(
        ArchivedItem.item_type == item.item_type,
        ArchivedItem.reference_id == item.reference_id
    ).first()
    
    if exists:
        # Update existing record if data was not previously saved
        if item.data and not exists.data:
            exists.data = item.data
            db.commit()
            db.refresh(exists)
        return exists

    db_item = ArchivedItem(
        item_type=item.item_type,
        reference_id=item.reference_id,
        title=item.title,
        summary=item.summary,
        data=item.data
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[ArchivedItemResponse])
def get_archives(db: Session = Depends(get_db)):
    """Get all archived items."""
    return db.query(ArchivedItem).order_by(ArchivedItem.created_at.desc()).all()


@router.get("/{id}", response_model=ArchivedItemResponse)
def get_archive(id: int, db: Session = Depends(get_db)):
    """Get a specific archived item."""
    item = db.query(ArchivedItem).filter(ArchivedItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{id}")
def delete_archive(id: int, db: Session = Depends(get_db)):
    """Remove an item from archives."""
    item = db.query(ArchivedItem).filter(ArchivedItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"status": "success"}
