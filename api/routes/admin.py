from fastapi import APIRouter, Depends, HTTPException
from bot.database.queries import ProfileRepo, UserRepo, NotificationRepo
from bot.database.models import SessionLocal
from api.auth import get_current_user, AuthResult
from api.schemas import AdminProfileResponse
from bot.config import ADMIN_IDS

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_admin(user: AuthResult):
    if user.user_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/profiles/new", response_model=list[AdminProfileResponse])
def get_new_profiles(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    repo = ProfileRepo(db)
    profiles = repo.get_new_profiles(limit=20)

    result = []
    for p in profiles:
        photos = p.get_photo_ids()
        result.append(AdminProfileResponse(
            user_id=p.user_id,
            username=None,
            name=p.name or "",
            gender=p.gender or "",
            age=p.age,
            mbti_type=p.mbti_type or "",
            communication_form=p.communication_form or "",
            description=p.description or "",
            looking_for=p.looking_for or "",
            visibility_mode=p.visibility_mode or "public",
            is_visible=p.is_visible,
            is_approved=p.is_approved,
            is_rejected=p.is_rejected,
            photo_count=len(photos),
        ))
    return result


@router.get("/profiles/all", response_model=list[AdminProfileResponse])
def get_all_profiles(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    repo = ProfileRepo(db)
    profiles = repo.get_all_profiles(limit=50)

    result = []
    for p in profiles:
        photos = p.get_photo_ids()
        result.append(AdminProfileResponse(
            user_id=p.user_id,
            username=None,
            name=p.name or "",
            gender=p.gender or "",
            age=p.age,
            mbti_type=p.mbti_type or "",
            communication_form=p.communication_form or "",
            description=p.description or "",
            looking_for=p.looking_for or "",
            visibility_mode=p.visibility_mode or "public",
            is_visible=p.is_visible,
            is_approved=p.is_approved,
            is_rejected=p.is_rejected,
            photo_count=len(photos),
        ))
    return result


@router.post("/approve/{user_id}")
def approve_profile(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    repo = ProfileRepo(db)
    repo.approve(user_id)
    return {"status": "ok"}


@router.post("/hide/{user_id}")
def hide_profile(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    repo = ProfileRepo(db)
    repo.hide(user_id)
    return {"status": "ok"}


@router.post("/ban/{user_id}")
def ban_user(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    user_repo = UserRepo(db)
    user_repo.ban(user_id)
    return {"status": "ok"}


@router.get("/stats")
def get_stats(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from sqlalchemy import func
    from bot.database.models import User, Profile, Match, Like

    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_profiles": db.query(func.count(Profile.user_id)).filter(Profile.is_approved == True).scalar(),
        "total_matches": db.query(func.count(Match.id)).scalar(),
        "total_likes": db.query(func.count(Like.id)).filter(Like.type == "like").scalar(),
    }
