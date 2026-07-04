import json
from fastapi import APIRouter, Depends, Query
from typing import Optional
from bot.database.queries import ProfileRepo, UserRepo, LikeRepo
from bot.database.models import SessionLocal
from api.auth import get_current_user, AuthResult
from api.schemas import BrowseProfileResponse, LikeRequest, StatsResponse

router = APIRouter(prefix="/api", tags=["browse", "likes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/browse", response_model=list[BrowseProfileResponse])
def browse_profiles(
    mbti_filter: Optional[str] = Query(None),
    limit: int = Query(10),
    user: AuthResult = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = ProfileRepo(db)
    user_repo = UserRepo(db)

    can_view, _ = user_repo.can_view(user.user_id)
    if not can_view:
        return []

    profiles = repo.get_for_browse(
        exclude_user_id=user.user_id,
        mbti_filter=mbti_filter,
        limit=limit,
    )

    user_repo.increment_views(user.user_id)

    result = []
    for p in profiles:
        photos = p.get_photo_ids()
        result.append(BrowseProfileResponse(
            user_id=p.user_id,
            name=p.name or "",
            gender=p.gender or "",
            age=p.age,
            mbti_type=p.mbti_type or "",
            communication_form=p.communication_form or "",
            description=p.description or "",
            looking_for=p.looking_for or "",
            photo_urls=[],
        ))

    return result


@router.post("/like")
def send_like(req: LikeRequest, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = LikeRepo(db)
    match = repo.add_like(user.user_id, req.target_user_id, req.like_type)

    if match:
        return {"status": "ok", "match": True}
    return {"status": "ok", "match": False}


@router.get("/stats", response_model=StatsResponse)
def get_stats(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    stats = repo.get_stats(user.user_id)
    return StatsResponse(
        likes_received=stats.get("likes_received", 0),
        matches=stats.get("matches", 0),
        avg_rating=stats.get("avg_rating"),
        total_reviews=stats.get("total_reviews", 0),
    )


@router.get("/who-liked-me")
def who_liked_me(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    user_repo = UserRepo(db)
    if not user_repo.has_premium(user.user_id):
        return {"error": "Premium required"}

    like_repo = LikeRepo(db)
    profile_repo = ProfileRepo(db)
    who = like_repo.get_who_liked_me(user.user_id)

    result = []
    for uid in who:
        p = profile_repo.get_by_user(uid)
        if p:
            result.append({
                "user_id": uid,
                "mbti_type": p.mbti_type,
                "age": p.age,
                "communication_form": p.communication_form,
            })

    return {"users": result}
