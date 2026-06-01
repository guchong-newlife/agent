import base64
import json
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import func, text
from ..database.session import SessionLocal, engine
from .model import TrackingEvent, TrackingSession

tracking_router = APIRouter(prefix="/api/tracking")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@tracking_router.get("/admin")
async def tracking_admin_page():
    return FileResponse(os.path.join(STATIC_DIR, "tracking_admin.html"))


def _save_event(data: dict) -> bool:
    db = SessionLocal()
    try:
        existing = db.query(TrackingEvent).filter(
            TrackingEvent.event_id == data.get("event_id", "")
        ).first()
        if existing:
            return False

        payload = json.dumps(data, ensure_ascii=False)
        ts_str = data.get("timestamp", "")
        ts = datetime.now()
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00").replace("+00:00", ""))
            except Exception:
                pass

        record = TrackingEvent(
            event_id=data.get("event_id", ""),
            track_name=data.get("trackName", "unknown"),
            fingerprint_id=data.get("fingerprint_id", ""),
            session_id=data.get("session_id", ""),
            page_url=data.get("page_url", ""),
            page_title=data.get("page_title", ""),
            timestamp=ts,
            payload=payload,
        )
        db.add(record)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


@tracking_router.api_route("/event", methods=["POST", "GET"])
async def receive_event(request: Request, d: str = Query("", alias="d")):
    # POST: sendBeacon with Blob body
    # GET: Image beacon with ?d=<url_encoded_json>
    data = None

    if request.method == "POST":
        body = await request.body()
        if body:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return {"error": "invalid json"}
    else:
        if d:
            try:
                d += "=" * (4 - len(d) % 4) if len(d) % 4 else ""
                decoded = base64.urlsafe_b64decode(d).decode("utf-8")
                data = json.loads(decoded)
            except Exception:
                return {"error": "invalid base64 data param"}

    if not data:
        return {"error": "no data"}

    saved = _save_event(data)
    return {"saved": 1 if saved else 0, "duplicate": not saved}


@tracking_router.api_route("/session", methods=["POST", "GET"])
async def upsert_session(request: Request, d: str = Query("", alias="d")):
    data = None
    if request.method == "POST":
        body = await request.body()
        if body:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return {"error": "invalid json"}
    else:
        if d:
            try:
                d += "=" * (4 - len(d) % 4) if len(d) % 4 else ""
                decoded = base64.urlsafe_b64decode(d).decode("utf-8")
                data = json.loads(decoded)
            except Exception:
                return {"error": "invalid base64 data"}

    if not data:
        return {"error": "no data"}

    session_id = data.get("session_id", "")
    if not session_id:
        return {"error": "session_id required"}

    db = SessionLocal()
    try:
        sess = db.query(TrackingSession).filter(
            TrackingSession.session_id == session_id
        ).first()

        if sess:
            if data.get("event_count"):
                sess.event_count = data["event_count"]
            if data.get("ended_at"):
                try:
                    sess.ended_at = datetime.fromisoformat(
                        data["ended_at"].replace("Z", "+00:00").replace("+00:00", "")
                    )
                except Exception:
                    pass
        else:
            browser = data.get("browser", {})
            screen = data.get("screen", {})
            ts_str = data.get("timestamp", "")
            started_at = datetime.now()
            if ts_str:
                try:
                    started_at = datetime.fromisoformat(ts_str.replace("Z", "+00:00").replace("+00:00", ""))
                except Exception:
                    pass

            sess = TrackingSession(
                session_id=session_id,
                fingerprint_id=data.get("fingerprint_id", ""),
                first_page_url=data.get("page_url", ""),
                referrer=data.get("referrer", ""),
                user_agent=browser.get("user_agent", ""),
                browser_info=json.dumps(browser, ensure_ascii=False) if browser else "",
                screen_info=json.dumps(screen, ensure_ascii=False) if screen else "",
                started_at=started_at,
                event_count=data.get("event_count", 1),
            )
            db.add(sess)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return {"success": True}


@tracking_router.get("/stats")
async def tracking_stats(days_back: int = Query(7, ge=1, le=90)):
    cutoff = datetime.now() - timedelta(days=days_back)

    with engine.connect() as conn:
        total_events = conn.execute(
            text("SELECT COUNT(*) FROM tracking_events WHERE created_at >= :cutoff"),
            {"cutoff": cutoff},
        ).scalar()

        by_track = conn.execute(
            text(
                "SELECT track_name, COUNT(*) AS cnt FROM tracking_events "
                "WHERE created_at >= :cutoff GROUP BY track_name ORDER BY cnt DESC"
            ),
            {"cutoff": cutoff},
        ).fetchall()

        total_sessions = conn.execute(
            text("SELECT COUNT(*) FROM tracking_sessions WHERE started_at >= :cutoff"),
            {"cutoff": cutoff},
        ).scalar()

        unique_fingerprints = conn.execute(
            text(
                "SELECT COUNT(DISTINCT fingerprint_id) FROM tracking_events "
                "WHERE created_at >= :cutoff"
            ),
            {"cutoff": cutoff},
        ).scalar()

        top_pages = conn.execute(
            text(
                "SELECT page_url, COUNT(*) AS cnt FROM tracking_events "
                "WHERE created_at >= :cutoff AND page_url IS NOT NULL "
                "GROUP BY page_url ORDER BY cnt DESC LIMIT 10"
            ),
            {"cutoff": cutoff},
        ).fetchall()

    return {
        "days_back": days_back,
        "total_events": total_events,
        "total_sessions": total_sessions,
        "unique_visitors": unique_fingerprints,
        "by_track_name": [{"name": r[0], "count": r[1]} for r in by_track],
        "top_pages": [{"url": r[0], "views": r[1]} for r in top_pages],
    }


# ── management API ─────────────────────────────────────────────

@tracking_router.get("/admin/events")
async def admin_list_events(
    track_name: str = Query(""),
    fingerprint_id: str = Query(""),
    session_id: str = Query(""),
    days_back: int = Query(1, ge=1, le=90),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    db = SessionLocal()
    try:
        q = db.query(TrackingEvent)
        cutoff = datetime.now() - timedelta(days=days_back)
        q = q.filter(TrackingEvent.created_at >= cutoff)
        if track_name:
            q = q.filter(TrackingEvent.track_name == track_name)
        if fingerprint_id:
            q = q.filter(TrackingEvent.fingerprint_id == fingerprint_id)
        if session_id:
            q = q.filter(TrackingEvent.session_id == session_id)

        total = q.count()
        rows = (
            q.order_by(TrackingEvent.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        events = []
        for r in rows:
            events.append({
                "id": r.id,
                "event_id": r.event_id,
                "track_name": r.track_name,
                "fingerprint_id": r.fingerprint_id,
                "session_id": r.session_id,
                "page_url": r.page_url,
                "page_title": r.page_title,
                "timestamp": str(r.timestamp),
                "created_at": str(r.created_at),
                "payload": json.loads(r.payload) if r.payload else {},
            })

        return {
            "events": events, "total": total,
            "page": page, "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    finally:
        db.close()


@tracking_router.get("/admin/event/{event_id}")
async def admin_event_detail(event_id: str):
    db = SessionLocal()
    try:
        r = db.query(TrackingEvent).filter(TrackingEvent.event_id == event_id).first()
        if not r:
            return {"error": "not found"}

        sess = db.query(TrackingSession).filter(
            TrackingSession.session_id == r.session_id
        ).first()

        return {
            "event_id": r.event_id,
            "track_name": r.track_name,
            "fingerprint_id": r.fingerprint_id,
            "session_id": r.session_id,
            "page_url": r.page_url,
            "page_title": r.page_title,
            "timestamp": str(r.timestamp),
            "created_at": str(r.created_at),
            "payload": json.loads(r.payload) if r.payload else {},
            "session": {
                "session_id": sess.session_id,
                "fingerprint_id": sess.fingerprint_id,
                "first_page_url": sess.first_page_url,
                "referrer": sess.referrer,
                "user_agent": sess.user_agent,
                "browser_info": json.loads(sess.browser_info) if sess.browser_info else {},
                "screen_info": json.loads(sess.screen_info) if sess.screen_info else {},
                "started_at": str(sess.started_at),
                "ended_at": str(sess.ended_at) if sess.ended_at else None,
                "event_count": sess.event_count,
            } if sess else None,
        }
    finally:
        db.close()


@tracking_router.get("/admin/sessions")
async def admin_list_sessions(
    days_back: int = Query(1, ge=1, le=90),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days_back)
        q = db.query(TrackingSession).filter(TrackingSession.started_at >= cutoff)
        total = q.count()
        rows = (
            q.order_by(TrackingSession.started_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        sessions = []
        for s in rows:
            event_count = db.query(TrackingEvent).filter(
                TrackingEvent.session_id == s.session_id
            ).count()
            sessions.append({
                "session_id": s.session_id,
                "fingerprint_id": s.fingerprint_id,
                "first_page_url": s.first_page_url,
                "referrer": s.referrer,
                "user_agent": s.user_agent,
                "started_at": str(s.started_at),
                "ended_at": str(s.ended_at) if s.ended_at else None,
                "event_count": event_count,
            })

        return {
            "sessions": sessions, "total": total,
            "page": page, "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    finally:
        db.close()
