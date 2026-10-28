from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
from app.routers.main_routers import (
    albums_router,
    memories_router,
    places_router,
    timeline_router,
    payments_router,
    analytics_router,
    admin_router,
)

# Import all models so create_all finds them
import app.models.album  # noqa: F401


def create_tables():
    Base.metadata.create_all(bind=engine)


app = FastAPI(title="Nossa História API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


# Auth routes
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.album import Album
from app.schemas.album import AlbumCreate, AlbumLogin


@app.post("/auth/register", status_code=201)
def register(data: AlbumCreate, db: Session = Depends(get_db)):
    existing = db.query(Album).filter(Album.slug == data.slug).first()
    if existing:
        raise HTTPException(409, "Slug já utilizado. Escolha outro.")
    album = Album(
        slug=data.slug,
        name1=data.name1,
        name2=data.name2,
        owner_email=data.owner_email,
        hashed_password=hash_password(data.password),
        start_date=data.start_date,
    )
    db.add(album)
    db.flush()
    token = create_access_token({"sub": album.id})
    return {
        "token": token,
        "album_id": album.id,
        "slug": album.slug,
        "plan": album.plan,
        "is_active": album.is_active,
    }


@app.post("/auth/login")
def login(data: AlbumLogin, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.slug == data.slug).first()
    if not album or not verify_password(data.password, album.hashed_password):
        raise HTTPException(401, "Slug ou senha incorretos.")
    token = create_access_token({"sub": album.id})
    return {
        "token": token,
        "album_id": album.id,
        "slug": album.slug,
        "name1": album.name1,
        "name2": album.name2,
        "plan": album.plan,
        "is_active": album.is_active,
        "start_date": str(album.start_date) if album.start_date else None,
        "phrase": album.phrase,
        "spotify_url": album.spotify_url,
        "theme": album.theme,
        "cover_photo_url": album.cover_photo_url,
    }


# Include routers
app.include_router(albums_router, prefix="/albums", tags=["albums"])
app.include_router(memories_router, prefix="/memories", tags=["memories"])
app.include_router(places_router, prefix="/places", tags=["places"])
app.include_router(timeline_router, prefix="/timeline", tags=["timeline"])
app.include_router(payments_router, prefix="/payments", tags=["payments"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
