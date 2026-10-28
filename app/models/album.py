import uuid
import datetime
from sqlalchemy import Column, String, Boolean, Date, DateTime, Text, Integer, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class PlanType(str, enum.Enum):
    basic = "basic"
    premium = "premium"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class Album(Base):
    __tablename__ = "albums"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name1 = Column(String(100), nullable=False)
    name2 = Column(String(100), nullable=False)
    owner_email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=True)
    plan = Column(SAEnum(PlanType), default=PlanType.basic)
    is_active = Column(Boolean, default=False)
    stripe_customer_id = Column(String(255), nullable=True)
    phrase = Column(Text, nullable=True)
    spotify_url = Column(String(500), nullable=True)
    theme = Column(String(50), default="romantic")
    cover_photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    memories = relationship("Memory", back_populates="album", cascade="all, delete-orphan")
    places = relationship("Place", back_populates="album", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="album", cascade="all, delete-orphan")
    page_views = relationship("PageView", back_populates="album", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="album", cascade="all, delete-orphan")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = Column(String, ForeignKey("albums.id"), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    memory_date = Column(Date, nullable=True)
    location_name = Column(String(200), nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    album = relationship("Album", back_populates="memories")


class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = Column(String, ForeignKey("albums.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    album = relationship("Album", back_populates="places")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = Column(String, ForeignKey("albums.id"), nullable=False)
    stripe_payment_id = Column(String(255), nullable=True)
    amount_cents = Column(Integer, default=0)
    plan = Column(SAEnum(PlanType), default=PlanType.basic)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.pending)
    created_at = Column(DateTime, default=func.now())

    album = relationship("Album", back_populates="payments")


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = Column(String, ForeignKey("albums.id"), nullable=False)
    device = Column(String(20), default="desktop")
    referrer = Column(String(500), nullable=True)
    viewed_at = Column(DateTime, default=func.now())

    album = relationship("Album", back_populates="page_views")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = Column(String, ForeignKey("albums.id"), nullable=False)
    title = Column(String(200), nullable=False)
    event_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    is_special = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    album = relationship("Album", back_populates="timeline_events")
