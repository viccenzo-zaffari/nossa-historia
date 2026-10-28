from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
import stripe

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_album
from app.models.album import Album, Place, Payment, PaymentStatus, PageView, PlanType, Memory, TimelineEvent
from app.schemas.album import AlbumPublic, AlbumPrivate, AlbumUpdate, PlaceOut, PlaceCreate

stripe.api_key = settings.STRIPE_SECRET_KEY

albums_router = APIRouter()

@albums_router.get("/{slug}", response_model=AlbumPublic)
def get_album(slug: str, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.slug == slug).first()
    if not album or not album.is_active:
        raise HTTPException(404, "Álbum não encontrado.")
    return album

@albums_router.get("/{slug}/memories")
def get_album_memories_public(slug: str, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.slug == slug).first()
    if not album or not album.is_active:
        raise HTTPException(404, "Álbum não encontrado.")
    memories = db.query(Memory).filter(Memory.album_id == album.id).order_by(Memory.display_order).all()
    return [{"id": m.id, "title": m.title, "description": m.description, "memory_date": str(m.memory_date) if m.memory_date else None, "location_name": m.location_name, "photo_url": m.photo_url, "display_order": m.display_order} for m in memories]

@albums_router.get("/{slug}/places")
def get_album_places_public(slug: str, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.slug == slug).first()
    if not album or not album.is_active:
        raise HTTPException(404, "Álbum não encontrado.")
    places = db.query(Place).filter(Place.album_id == album.id).order_by(Place.display_order).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "latitude": p.latitude, "longitude": p.longitude} for p in places]

@albums_router.get("/{slug}/timeline")
def get_album_timeline_public(slug: str, db: Session = Depends(get_db)):
    album = db.query(Album).filter(Album.slug == slug).first()
    if not album or not album.is_active:
        raise HTTPException(404, "Álbum não encontrado.")
    events = db.query(TimelineEvent).filter(TimelineEvent.album_id == album.id).order_by(TimelineEvent.event_date.desc()).all()
    return [{"id": e.id, "title": e.title, "event_date": str(e.event_date), "description": e.description, "is_special": e.is_special} for e in events]

@albums_router.get("/me/profile", response_model=AlbumPrivate)
def get_my_album(current: Album = Depends(get_current_album)):
    return current

@albums_router.patch("/me/profile", response_model=AlbumPrivate)
def update_album(data: AlbumUpdate, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current, field, value)
    db.flush()
    return current

memories_router = APIRouter()

@memories_router.get("/")
def list_memories(db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    memories = db.query(Memory).filter(Memory.album_id == current.id).order_by(Memory.display_order).all()
    return [{"id": m.id, "title": m.title, "description": m.description, "memory_date": str(m.memory_date) if m.memory_date else None, "location_name": m.location_name, "photo_url": m.photo_url, "display_order": m.display_order} for m in memories]

@memories_router.post("/", status_code=201)
def create_memory(data: dict, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    memory_date = None
    if data.get("memory_date"):
        try:
            memory_date = date.fromisoformat(data["memory_date"])
        except ValueError:
            pass
    memory = Memory(
        album_id=current.id,
        title=data.get("title", "Memória"),
        photo_url=data.get("photo_url"),
        location_name=data.get("location_name"),
        description=data.get("description"),
        memory_date=memory_date,
        display_order=data.get("display_order", 0)
    )
    db.add(memory)
    db.flush()
    return {"id": memory.id, "title": memory.title, "photo_url": memory.photo_url, "memory_date": str(memory.memory_date) if memory.memory_date else None, "location_name": memory.location_name, "description": memory.description, "album_id": memory.album_id}

@memories_router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: str, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    memory = db.query(Memory).filter(Memory.id == memory_id, Memory.album_id == current.id).first()
    if not memory:
        raise HTTPException(404, "Memória não encontrada.")
    db.delete(memory)

places_router = APIRouter()

@places_router.get("/", response_model=list[PlaceOut])
def list_places(db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    return db.query(Place).filter(Place.album_id == current.id).order_by(Place.display_order).all()

@places_router.post("/", response_model=PlaceOut, status_code=201)
def create_place(data: PlaceCreate, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    place = Place(album_id=current.id, **data.model_dump())
    db.add(place)
    db.flush()
    return place

@places_router.delete("/{place_id}", status_code=204)
def delete_place(place_id: str, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    place = db.query(Place).filter(Place.id == place_id, Place.album_id == current.id).first()
    if not place:
        raise HTTPException(404, "Lugar não encontrado.")
    db.delete(place)

# ── TIMELINE ROUTER ──
timeline_router = APIRouter()

@timeline_router.get("/")
def list_timeline(db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    events = db.query(TimelineEvent).filter(TimelineEvent.album_id == current.id).order_by(TimelineEvent.event_date.desc()).all()
    return [{"id": e.id, "title": e.title, "event_date": str(e.event_date), "description": e.description, "is_special": e.is_special} for e in events]

@timeline_router.post("/", status_code=201)
def create_timeline_event(data: dict, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    event_date = None
    if data.get("event_date"):
        try:
            event_date = date.fromisoformat(data["event_date"])
        except ValueError:
            raise HTTPException(400, "Data inválida.")
    if not event_date:
        raise HTTPException(400, "Data obrigatória.")
    event = TimelineEvent(
        album_id=current.id,
        title=data.get("title", "Evento"),
        event_date=event_date,
        description=data.get("description"),
        is_special=data.get("is_special", False)
    )
    db.add(event)
    db.flush()
    return {"id": event.id, "title": event.title, "event_date": str(event.event_date), "description": event.description, "is_special": event.is_special}

@timeline_router.delete("/{event_id}", status_code=204)
def delete_timeline_event(event_id: str, db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id, TimelineEvent.album_id == current.id).first()
    if not event:
        raise HTTPException(404, "Evento não encontrado.")
    db.delete(event)

payments_router = APIRouter()

@payments_router.post("/checkout")
def create_checkout(plan: str = "basic", db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    price_id = settings.STRIPE_PRICE_PREMIUM if plan == "premium" else settings.STRIPE_PRICE_BASIC
    mode = "subscription" if plan == "premium" else "payment"
    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=current.owner_email,
            metadata={"album_id": current.id, "plan": plan},
            success_url=f"{settings.FRONTEND_URL}/nossa_historia_dashboard.html?payment=success",
            cancel_url=f"{settings.FRONTEND_URL}/nossa_historia_criar.html?payment=cancelled",
        )
    except stripe.StripeError as e:
        raise HTTPException(400, str(e))
    return {"checkout_url": session.url, "session_id": session.id}

@payments_router.post("/webhook", status_code=200)
def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    import asyncio
    body = asyncio.get_event_loop().run_until_complete(request.body())
    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(400, "Webhook inválido.")
    data = event["data"]["object"]
    if event["type"] == "checkout.session.completed":
        album_id = data.get("metadata", {}).get("album_id")
        plan = data.get("metadata", {}).get("plan", "basic")
        if album_id:
            album = db.query(Album).filter(Album.id == album_id).first()
            if album:
                album.is_active = True
                album.plan = PlanType.premium if plan == "premium" else PlanType.basic
                album.stripe_customer_id = data.get("customer")
                payment = Payment(album_id=album_id, stripe_payment_id=data.get("payment_intent") or data.get("id"), amount_cents=data.get("amount_total", 0), plan=album.plan, status=PaymentStatus.completed)
                db.add(payment)
    elif event["type"] in ("customer.subscription.deleted", "invoice.payment_failed"):
        customer_id = data.get("customer")
        album = db.query(Album).filter(Album.stripe_customer_id == customer_id).first()
        if album:
            album.plan = PlanType.basic
    return {"received": True}

analytics_router = APIRouter()

@analytics_router.post("/{album_id}/view", status_code=204)
def register_view(album_id: str, request: Request, db: Session = Depends(get_db)):
    ua = request.headers.get("user-agent", "").lower()
    device = "mobile" if any(x in ua for x in ["iphone", "android", "mobile"]) else "tablet" if "ipad" in ua else "desktop"
    view = PageView(album_id=album_id, device=device, referrer=request.headers.get("referer"))
    db.add(view)

@analytics_router.get("/me/summary")
def get_analytics(db: Session = Depends(get_db), current: Album = Depends(get_current_album)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    total = db.query(PageView).filter(PageView.album_id == current.id).count()
    this_week = db.query(PageView).filter(PageView.album_id == current.id, PageView.viewed_at >= week_ago).count()
    prev_week = db.query(PageView).filter(PageView.album_id == current.id, PageView.viewed_at >= two_weeks_ago, PageView.viewed_at < week_ago).count()
    today = db.query(PageView).filter(PageView.album_id == current.id, PageView.viewed_at >= today_start).count()

    # Dispositivos
    mobile = db.query(PageView).filter(PageView.album_id == current.id, PageView.device == "mobile").count()
    desktop = db.query(PageView).filter(PageView.album_id == current.id, PageView.device == "desktop").count()
    tablet = db.query(PageView).filter(PageView.album_id == current.id, PageView.device == "tablet").count()

    # Variação semana a semana
    if prev_week > 0:
        week_change_pct = round(((this_week - prev_week) / prev_week) * 100)
    elif this_week > 0:
        week_change_pct = 100
    else:
        week_change_pct = 0

    # Últimos 7 dias por dia
    daily_views = []
    days_pt = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.query(PageView).filter(
            PageView.album_id == current.id,
            PageView.viewed_at >= day_start,
            PageView.viewed_at < day_end
        ).count()
        daily_views.append({"day": days_pt[day_start.weekday() + 1 if day_start.weekday() < 6 else 0], "v": count})

    return {
        "total_views": total,
        "week_views": this_week,
        "prev_week_views": prev_week,
        "week_change_pct": week_change_pct,
        "today_views": today,
        "mobile_views": mobile,
        "desktop_views": desktop,
        "tablet_views": tablet,
        "daily_views": daily_views
    }

# ── ADMIN ROUTER ──
admin_router = APIRouter()

ADMIN_TOKEN = "nossahistoria-admin-2026"  # trocar por env var na produção

def check_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(401, "Não autorizado.")

@admin_router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _: None = Depends(check_admin)):
    total_albums = db.query(Album).count()
    active_albums = db.query(Album).filter(Album.is_active == True).count()
    premium_albums = db.query(Album).filter(Album.plan == PlanType.premium).count()
    total_revenue_cents = db.query(func.sum(Payment.amount_cents)).filter(Payment.status == PaymentStatus.completed).scalar() or 0
    total_views = db.query(PageView).count()
    recent_payments = db.query(Payment, Album).join(Album, Payment.album_id == Album.id).filter(
        Payment.status == PaymentStatus.completed
    ).order_by(Payment.created_at.desc()).limit(10).all()

    payments_data = [{
        "album": f"{p.Album.name1} & {p.Album.name2}",
        "email": p.Album.owner_email,
        "amount": p.Payment.amount_cents / 100,
        "plan": p.Payment.plan,
        "date": str(p.Payment.created_at)[:10] if p.Payment.created_at else ""
    } for p in recent_payments]

    return {
        "total_albums": total_albums,
        "active_albums": active_albums,
        "premium_albums": premium_albums,
        "basic_albums": active_albums - premium_albums,
        "total_revenue_brl": total_revenue_cents / 100,
        "total_views": total_views,
        "recent_payments": payments_data
    }

@admin_router.get("/albums")
def admin_albums(db: Session = Depends(get_db), _: None = Depends(check_admin)):
    albums = db.query(Album).order_by(Album.created_at.desc()).all()
    return [{
        "id": a.id,
        "slug": a.slug,
        "name1": a.name1,
        "name2": a.name2,
        "email": a.owner_email,
        "plan": a.plan,
        "is_active": a.is_active,
        "created_at": str(a.created_at)[:10] if a.created_at else "",
        "start_date": str(a.start_date) if a.start_date else ""
    } for a in albums]
