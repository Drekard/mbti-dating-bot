import json
from fastapi import APIRouter, Depends
from bot.database.queries import ProfileRepo, UserRepo
from bot.database.models import SessionLocal
from api.auth import get_current_user, AuthResult
from api.schemas import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/api/profile", tags=["profile"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    user_repo = UserRepo(db)
    profile = repo.get_by_user(user.user_id)
    if not profile:
        profile = repo.create(user.user_id)

    db_user = user_repo.get_by_id(user.user_id)
    photos = profile.get_photo_ids()
    return ProfileResponse(
        user_id=profile.user_id,
        name=profile.name or "",
        gender=profile.gender or "",
        age=profile.age,
        mbti_type=profile.mbti_type or "",
        visibility_mode=profile.visibility_mode or "public",
        communication_form=profile.communication_form or "",
        description=profile.description or "",
        looking_for=profile.looking_for or "",
        is_visible=profile.is_visible,
        is_approved=profile.is_approved,
        is_admin=db_user.is_admin if db_user else False,
        photo_count=len(photos),
    )


@router.post("/create")
def create_profile(data: ProfileCreate, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    profile = repo.create(user.user_id)

    repo.update_field(user.user_id, "name", data.name or "")
    repo.update_field(user.user_id, "gender", data.gender or "")
    if data.age:
        repo.update_field(user.user_id, "age", data.age)
    repo.update_field(user.user_id, "mbti_type", data.mbti_type or "")
    repo.update_field(user.user_id, "visibility_mode", data.visibility_mode or "public")
    repo.update_field(user.user_id, "communication_form", data.communication_form or "")
    repo.update_field(user.user_id, "description", data.description or "")
    repo.update_field(user.user_id, "looking_for", data.looking_for or "")
    repo.update_field(user.user_id, "is_visible", True)
    repo.update_field(user.user_id, "is_approved", True)

    return {"status": "ok", "message": "Profile created"}


@router.post("/update")
def update_profile(data: ProfileUpdate, user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    repo.update_field(user.user_id, data.field, data.value)
    return {"status": "ok"}


@router.post("/publish")
def publish_profile(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    repo.update_field(user.user_id, "is_visible", True)
    repo.update_field(user.user_id, "is_approved", True)

    from bot.database.queries import NotificationRepo
    notif_repo = NotificationRepo(db)
    notif_repo.create(
        notif_type="new_profile",
        target_user_id=user.user_id,
        message=f"Новая анкета от Telegram user {user.user_id}",
    )

    return {"status": "ok", "message": "Profile published"}


@router.post("/hide")
def hide_profile(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    repo.update_field(user.user_id, "is_visible", False)
    return {"status": "ok", "message": "Profile hidden"}


@router.delete("/delete")
def delete_profile(user: AuthResult = Depends(get_current_user), db=Depends(get_db)):
    repo = ProfileRepo(db)
    repo.delete(user.user_id)
    return {"status": "ok", "message": "Profile deleted"}
