from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_db
from pydantic import BaseModel
from core import models
from datetime import datetime

router = APIRouter(prefix="/sites", tags=["Collaboration"])

class CommentRequest(BaseModel):
    comment: str
    author: str
    tag: str = "Info"

@router.post("/{site_number}/comment")
def add_site_comment(site_number: str, request: CommentRequest, db: Session = Depends(get_db)):
    db_comment = models.SiteComment(
        site_number=site_number,
        comment=request.comment,
        tag=request.tag,
        author=request.author,
        created_at=datetime.now()
    )
    db.add(db_comment)
    db.commit()
    return {"status": "success", "message": "Comment added"}

@router.get("/{site_number}/comments")
def get_site_comments(site_number: str, db: Session = Depends(get_db)):
    return db.query(models.SiteComment).filter(models.SiteComment.site_number == site_number).all()
