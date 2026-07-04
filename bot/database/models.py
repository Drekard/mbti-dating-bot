from datetime import datetime
import json
from sqlalchemy import (
    Boolean, Column, BigInteger, Integer, String, Text,
    DateTime, ForeignKey, CheckConstraint, UniqueConstraint,
    Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from bot.config import DATABASE_URL

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(DateTime, nullable=True)
    referred_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)
    daily_views = Column(Integer, default=0)
    last_view_reset = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    profile = relationship("Profile", back_populates="user", uselist=False)
    sent_likes = relationship("Like", foreign_keys="Like.from_user_id", back_populates="from_user")
    received_likes = relationship("Like", foreign_keys="Like.to_user_id", back_populates="to_user")
    matches_as_user1 = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1")
    matches_as_user2 = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2")
    reviews_given = relationship("Review", foreign_keys="Review.from_user_id", back_populates="from_user")
    reviews_received = relationship("Review", foreign_keys="Review.to_user_id", back_populates="to_user")
    complaints_given = relationship("Complaint", foreign_keys="Complaint.from_user_id", back_populates="from_user")
    complaints_received = relationship("Complaint", foreign_keys="Complaint.to_user_id", back_populates="to_user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    name = Column(String(255), nullable=True, default="")
    gender = Column(String(10), nullable=True, default="")
    age = Column(Integer, nullable=True)
    mbti_type = Column(String(4), nullable=True, default="")
    visibility_mode = Column(String(20), nullable=True, default="public")
    communication_form = Column(String(50), nullable=True, default="")
    description = Column(Text, nullable=True, default="")
    looking_for = Column(Text, nullable=True, default="")
    is_visible = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)
    is_rejected = Column(Boolean, default=False)
    photo_file_ids = Column(Text, nullable=True, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

    __table_args__ = (
        Index("idx_profiles_mbti", "mbti_type"),
        Index("idx_profiles_approved", "is_approved", "is_visible"),
    )

    def get_photo_ids(self):
        return json.loads(self.photo_file_ids or "[]")

    def field_display(self, field_name):
        val = getattr(self, field_name, None)
        if field_name == "photo_file_ids":
            photos = self.get_photo_ids()
            return f"{len(photos)} фото" if photos else "[nil]"
        if field_name == "visibility_mode":
            return "Публично" if val == "public" else "Анонимно" if val == "anonymous" else "[nil]"
        if not val or (isinstance(val, str) and not val.strip()):
            return "[nil]"
        if field_name == "age":
            return str(val)
        return str(val)


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_likes")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_likes")

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_like_pair"),
        Index("idx_likes_from", "from_user_id"),
        Index("idx_likes_to", "to_user_id"),
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    user2_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_match_pair"),
        CheckConstraint("user1_id < user2_id", name="ck_user_order"),
        Index("idx_matches_user1", "user1_id"),
        Index("idx_matches_user2", "user2_id"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="reviews_given")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="reviews_received")

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_review_pair"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
    )


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="complaints_given")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="complaints_received")

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_complaint_pair"),
    )


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    referred_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    bonus_granted = Column(Boolean, default=False)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")

    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id", name="uq_referral_pair"),
    )


class AdminNotification(Base):
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    target_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    message = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    photo_file_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    frequency_days = Column(Integer, default=7)
    last_shown_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
