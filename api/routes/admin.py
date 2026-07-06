from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from bot.database.queries import ProfileRepo, UserRepo, NotificationRepo, ComplaintRepo
from bot.database.models import SessionLocal, AdminNote
from api.auth import get_current_user, AuthResult
from api.schemas import AdminProfileResponse
from bot.config import ADMIN_IDS, BOT_TOKEN

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
    profiles = repo.get_pending()

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


@router.post("/reject/{user_id}")
def reject_profile(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    repo = ProfileRepo(db)
    repo.reject(user_id)
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


@router.post("/unban/{user_id}")
def unban_user(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    user_repo = UserRepo(db)
    user_repo.unban(user_id)
    return {"status": "ok"}


@router.post("/warn/{user_id}")
def warn_user(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from bot.config import BOT_TOKEN
    import asyncio
    from aiogram import Bot
    db_user = user_repo.get_by_id(user_id) if (user_repo := UserRepo(db)) else None
    if db_user:
        db_user.warn_count += 1
        db.commit()
    return {"status": "ok"}


@router.post("/mute/{user_id}")
def mute_user(user_id: int, days: int = 3, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from bot.database.models import User
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.muted_until = datetime.utcnow() + timedelta(days=days)
        db.commit()
    return {"status": "ok"}


@router.post("/unmute/{user_id}")
def unmute_user(user_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from bot.database.models import User
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.muted_until = None
        db.commit()
    return {"status": "ok"}


@router.get("/users")
def get_users(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from bot.database.models import User, Profile
    from sqlalchemy import func
    users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
    result = []
    for u in users:
        profile = db.query(Profile).filter(Profile.user_id == u.id).first()
        result.append({
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "mbti_type": profile.mbti_type if profile else None,
            "is_banned": u.is_banned,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return result


@router.get("/complaints")
def get_complaints(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from bot.database.models import Complaint, User
    complaints = db.query(Complaint).filter(Complaint.status == "open").order_by(Complaint.created_at.desc()).all()
    result = []
    for c in complaints:
        from_user = db.query(User).filter(User.id == c.from_user_id).first()
        to_user = db.query(User).filter(User.id == c.to_user_id).first()
        result.append({
            "id": c.id,
            "from_user": from_user.username if from_user else str(c.from_user_id),
            "to_user": to_user.username if to_user else str(c.to_user_id),
            "reason": c.reason,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.post("/complaints/{complaint_id}/resolve")
def resolve_complaint(complaint_id: int, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    from bot.database.models import Complaint
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if complaint:
        complaint.status = "resolved"
        complaint.admin_action = "resolved"
        db.commit()
    return {"status": "ok"}


@router.post("/note/{user_id}")
def add_note(user_id: int, text: str, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    check_admin(user)
    note = AdminNote(user_id=user_id, admin_id=user.user_id, text=text)
    db.add(note)
    db.commit()
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
