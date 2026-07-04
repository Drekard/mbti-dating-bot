from datetime import datetime, date
import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from bot.database.models import (
    User, Profile, Like, Match, Review, Complaint,
    Referral, AdminNotification, AdCampaign
)


class UserRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, user_id: int, username: str = None,
                      first_name: str = None, last_name: str = None,
                      referred_by: int = None) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referred_by=referred_by,
                last_view_reset=date.today(),
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            if referred_by:
                referral = Referral(
                    referrer_id=referred_by,
                    referred_id=user_id,
                )
                self.db.add(referral)
                referrer = self.db.query(User).filter(User.id == referred_by).first()
                if referrer:
                    referrer.referral_count += 1
                self.db.commit()
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def is_banned(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        return user.is_banned if user else True

    def is_admin(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        return user.is_admin if user else False

    def has_premium(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user or not user.is_premium:
            return False
        if user.premium_expires_at and user.premium_expires_at < datetime.utcnow():
            user.is_premium = False
            self.db.commit()
            return False
        return True

    def grant_premium(self, user_id: int, days: int):
        user = self.get_by_id(user_id)
        if not user:
            return
        user.is_premium = True
        if user.premium_expires_at and user.premium_expires_at > datetime.utcnow():
            user.premium_expires_at = user.premium_expires_at + __import__('datetime').timedelta(days=days)
        else:
            user.premium_expires_at = datetime.utcnow() + __import__('datetime').timedelta(days=days)
        self.db.commit()

    def can_view(self, user_id: int, daily_limit: int = 10) -> Tuple[bool, int]:
        user = self.get_by_id(user_id)
        if not user:
            return False, 0

        if user.last_view_reset != date.today():
            user.daily_views = 0
            user.last_view_reset = date.today()
            self.db.commit()

        remaining = daily_limit - user.daily_views
        if user.is_premium:
            return True, 999

        if remaining <= 0:
            return False, 0

        return True, remaining

    def increment_views(self, user_id: int):
        user = self.get_by_id(user_id)
        if user and user.last_view_reset == date.today():
            user.daily_views += 1
            self.db.commit()

    def ban(self, user_id: int):
        user = self.get_by_id(user_id)
        if user:
            user.is_banned = True
            self.db.commit()

    def unban(self, user_id: int):
        user = self.get_by_id(user_id)
        if user:
            user.is_banned = False
            self.db.commit()


class ProfileRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int) -> Profile:
        profile = self.db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def get_by_user(self, user_id: int) -> Optional[Profile]:
        return self.db.query(Profile).filter(Profile.user_id == user_id).first()

    def update_field(self, user_id: int, field: str, value):
        profile = self.get_by_user(user_id)
        if not profile:
            profile = self.create(user_id)

        if field == "photo_file_ids":
            existing = profile.get_photo_ids()
            if isinstance(value, list):
                existing.extend(value)
            else:
                existing.append(value)
            profile.photo_file_ids = json.dumps(existing)
        elif field == "remove_photo":
            existing = profile.get_photo_ids()
            if isinstance(value, int) and 0 <= value < len(existing):
                existing.pop(value)
                profile.photo_file_ids = json.dumps(existing)
        else:
            setattr(profile, field, value)

        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_pending(self) -> List[Profile]:
        return self.db.query(Profile).filter(
            Profile.is_approved == False,
            Profile.is_visible == True,
        ).all()

    def get_new_profiles(self, limit: int = 20) -> List[Profile]:
        return self.db.query(Profile).filter(
            Profile.is_approved == True,
            Profile.is_rejected == False,
        ).order_by(Profile.created_at.desc()).limit(limit).all()

    def get_updated_profiles(self, limit: int = 20) -> List[Profile]:
        return self.db.query(Profile).filter(
            Profile.is_approved == True,
            Profile.is_rejected == False,
            Profile.updated_at > Profile.created_at,
        ).order_by(Profile.updated_at.desc()).limit(limit).all()

    def get_all_profiles(self, limit: int = 50) -> List[Profile]:
        return self.db.query(Profile).order_by(Profile.created_at.desc()).limit(limit).all()

    def approve(self, user_id: int):
        profile = self.get_by_user(user_id)
        if profile:
            profile.is_approved = True
            profile.is_rejected = False
            self.db.commit()

    def reject(self, user_id: int):
        profile = self.get_by_user(user_id)
        if profile:
            profile.is_approved = False
            profile.is_rejected = True
            self.db.commit()

    def hide(self, user_id: int):
        profile = self.get_by_user(user_id)
        if profile:
            profile.is_visible = False
            self.db.commit()

    def get_for_browse(self, exclude_user_id: int, mbti_filter: str = None,
                       city_filter: str = None, limit: int = 1) -> List[Profile]:
        query = self.db.query(Profile).filter(
            Profile.user_id != exclude_user_id,
            Profile.is_approved == True,
            Profile.is_visible == True,
            Profile.is_rejected == False,
            Profile.mbti_type != "",
        )

        already_liked = self.db.query(Like.to_user_id).filter(
            Like.from_user_id == exclude_user_id
        ).subquery()

        query = query.filter(Profile.user_id.notin_(already_liked))

        if mbti_filter:
            query = query.filter(Profile.mbti_type == mbti_filter)

        return query.limit(limit).all()

    def toggle_visibility(self, user_id: int) -> bool:
        profile = self.get_by_user(user_id)
        if profile:
            profile.is_visible = not profile.is_visible
            profile.updated_at = datetime.utcnow()
            self.db.commit()
            return profile.is_visible
        return False

    def delete(self, user_id: int):
        profile = self.get_by_user(user_id)
        if profile:
            self.db.delete(profile)
            self.db.commit()

    def get_stats(self, user_id: int) -> dict:
        profile = self.get_by_user(user_id)
        if not profile:
            return {}

        likes_received = self.db.query(func.count(Like.id)).filter(
            Like.to_user_id == user_id, Like.type == "like"
        ).scalar()

        matches_count = self.db.query(func.count(Match.id)).filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        ).scalar()

        avg_rating = self.db.query(func.avg(Review.rating)).filter(
            Review.to_user_id == user_id
        ).scalar()

        return {
            "likes_received": likes_received,
            "matches": matches_count,
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "total_reviews": self.db.query(func.count(Review.id)).filter(
                Review.to_user_id == user_id
            ).scalar(),
        }


class LikeRepo:
    def __init__(self, db: Session):
        self.db = db

    def add_like(self, from_user_id: int, to_user_id: int, like_type: str) -> Optional[Match]:
        existing = self.db.query(Like).filter(
            Like.from_user_id == from_user_id,
            Like.to_user_id == to_user_id,
        ).first()

        if existing:
            existing.type = like_type
        else:
            self.db.add(Like(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                type=like_type,
            ))

        self.db.commit()

        if like_type == "like":
            reverse = self.db.query(Like).filter(
                Like.from_user_id == to_user_id,
                Like.to_user_id == from_user_id,
                Like.type == "like",
            ).first()

            if reverse:
                user1, user2 = sorted([from_user_id, to_user_id])
                existing_match = self.db.query(Match).filter(
                    Match.user1_id == user1,
                    Match.user2_id == user2,
                ).first()

                if not existing_match:
                    match = Match(user1_id=user1, user2_id=user2)
                    self.db.add(match)
                    self.db.commit()
                    return match

        return None

    def get_who_liked_me(self, user_id: int) -> List[int]:
        result = self.db.query(Like.from_user_id).filter(
            Like.to_user_id == user_id,
            Like.type == "like",
        ).all()
        return [r[0] for r in result]


class MatchRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_my_matches(self, user_id: int) -> List[Tuple[int, Profile]]:
        matches = self.db.query(Match).filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        ).all()

        result = []
        for m in matches:
            other_id = m.user2_id if m.user1_id == user_id else m.user1_id
            profile = self.db.query(Profile).filter(Profile.user_id == other_id).first()
            if profile:
                result.append((other_id, profile))
        return result


class ReviewRepo:
    def __init__(self, db: Session):
        self.db = db

    def add_review(self, from_user_id: int, to_user_id: int,
                   rating: int, text: str = None) -> Review:
        existing = self.db.query(Review).filter(
            Review.from_user_id == from_user_id,
            Review.to_user_id == to_user_id,
        ).first()

        if existing:
            existing.rating = rating
            existing.text = text
            self.db.commit()
            self.db.refresh(existing)
            return existing

        review = Review(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            rating=rating,
            text=text,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review


class ComplaintRepo:
    def __init__(self, db: Session):
        self.db = db

    def add_complaint(self, from_user_id: int, to_user_id: int, reason: str) -> Complaint:
        complaint = Complaint(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reason=reason,
        )
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get_complaint_count(self, user_id: int) -> int:
        return self.db.query(func.count(Complaint.id)).filter(
            Complaint.to_user_id == user_id
        ).scalar()


class NotificationRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notif_type: str, target_user_id: int = None,
               message: str = None) -> AdminNotification:
        notif = AdminNotification(
            type=notif_type,
            target_user_id=target_user_id,
            message=message,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def get_unresolved(self) -> List[AdminNotification]:
        return self.db.query(AdminNotification).filter(
            AdminNotification.is_resolved == False
        ).order_by(AdminNotification.created_at.desc()).all()

    def resolve(self, notif_id: int):
        notif = self.db.query(AdminNotification).filter(
            AdminNotification.id == notif_id
        ).first()
        if notif:
            notif.is_resolved = True
            self.db.commit()


class AdRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_due_ad(self) -> Optional[AdCampaign]:
        from datetime import timedelta
        return self.db.query(AdCampaign).filter(
            AdCampaign.is_active == True,
            or_(
                AdCampaign.last_shown_at == None,
                AdCampaign.last_shown_at < datetime.utcnow() - timedelta(days=AdCampaign.frequency_days)
            )
        ).order_by(AdCampaign.last_shown_at.asc()).first()

    def mark_shown(self, ad_id: int):
        ad = self.db.query(AdCampaign).filter(AdCampaign.id == ad_id).first()
        if ad:
            ad.last_shown_at = datetime.utcnow()
            self.db.commit()
