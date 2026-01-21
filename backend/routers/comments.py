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
    status: str = "Open"

@router.post("/{site_number}/comment")
def add_site_comment(site_number: str, request: CommentRequest, db: Session = Depends(get_db)):
    db_comment = models.SiteComment(
        site_number=site_number,
        comment=request.comment,
        tag=request.tag,
        status=request.status,
        author=request.author,
        created_at=datetime.now(),
        is_resolved=1 if request.status == "Resolved" else 0
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    # Parse @mentions
    import re
    mentions = re.findall(r'@(\w+)', request.comment)
    for handle in mentions:
        alert = models.UserAlert(
            user_handle=f"@{handle}",
            message=f"You were mentioned in a comment for Site {site_number} by {request.author}",
            comment_id=db_comment.id
        )
        db.add(alert)
    
    db.commit()
    return {"status": "success", "message": "Comment added", "id": db_comment.id}

@router.get("/{site_number}/comments")
def get_site_comments(site_number: str, db: Session = Depends(get_db)):
    return db.query(models.SiteComment).filter(models.SiteComment.site_number == site_number).all()
