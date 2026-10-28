from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from app.models.album import PlanType


class AlbumCreate(BaseModel):
    slug: str
    name1: str
    name2: str
    owner_email: EmailStr
    password: str
    start_date: Optional[date] = None


class AlbumLogin(BaseModel):
    slug: str
    password: str


class AlbumUpdate(BaseModel):
    name1: Optional[str] = None
    name2: Optional[str] = None
    start_date: Optional[date] = None
    phrase: Optional[str] = None
    spotify_url: Optional[str] = None
    theme: Optional[str] = None
    cover_photo_url: Optional[str] = None


class AlbumPublic(BaseModel):
    id: str
    slug: str
    name1: str
    name2: str
    start_date: Optional[date] = None
    phrase: Optional[str] = None
    spotify_url: Optional[str] = None
    theme: Optional[str] = None
    cover_photo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class AlbumPrivate(AlbumPublic):
    owner_email: str
    plan: PlanType
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PlaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_order: int = 0


class PlaceOut(PlaceCreate):
    id: str
    album_id: str

    model_config = {"from_attributes": True}
