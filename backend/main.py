"""
FretIQ App - FastAPI Application
Main entry point and API routes.
"""
import logging
import json
from contextlib import asynccontextmanager
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import get_settings
from models.core import (
    SearchRequest, SearchResponse, SongResult, Instrument,
    ContentType, DifficultyLevel, SourceType, UserFeedback,
    ChordDiagram, StrummingPattern, TabNotation, PianoNotes
)
from models.user import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    FavoriteCreate, FavoriteResponse, FeedbackCreate, FeedbackResponse,
    SearchHistoryItem, UserProfile
)
from service import get_service, ChordSearchService
from cache import get_cache
from db import init_db, close_pool, execute_query, execute_one, execute_insert, execute_update
from auth import (
    hash_password, verify_password, create_token_response,
    get_current_user_id, require_user_id, get_user_id_from_token
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    service = get_service()
    await service.initialize()
    logger.info("FretIQ App started")
    
    yield
    
    # Shutdown
    await close_pool()
    logger.info("FretIQ App shutting down")


app = FastAPI(
    title="Music Chords API",
    description="Find chords, notes, tabs, and strumming patterns for any song across multiple instruments",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_search_service() -> ChordSearchService:
    return get_service()


# Request/Response models for API
class SearchRequestAPI(BaseModel):
    song_name: str
    artist: Optional[str] = None
    instruments: List[str] = ["guitar"]
    content_types: Optional[List[str]] = None
    difficulty: Optional[str] = None
    use_ai: bool = True
    use_web: bool = True
    max_results: int = 5


class SongResultAPI(BaseModel):
    song_name: str
    artist: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    confidence: float
    chords: Dict[str, List[Dict]] = {}
    strumming_patterns: Dict[str, List[Dict]] = {}
    tabs: Dict[str, List[Dict]] = {}
    piano_notes: Optional[Dict] = None
    key: Optional[str] = None
    tempo: Optional[int] = None
    time_signature: str = "4/4"
    genre: Optional[str] = None
    year: Optional[int] = None
    capo: Optional[int] = None
    difficulty: str = "beginner"
    is_verified: bool = False


class SearchResponseAPI(BaseModel):
    query: SearchRequestAPI
    results: List[SongResultAPI]
    total_found: int
    search_time_ms: float
    sources_used: List[str]
    errors: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    ai_providers: List[str]
    cache_stats: Dict


class FeedbackRequest(BaseModel):
    result_id: str
    rating: int
    comment: Optional[str] = None
    corrections: Optional[Dict] = None


def convert_instrument(inst: str) -> Instrument:
    """Convert string to Instrument enum."""
    try:
        return Instrument(inst.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid instrument: {inst}")


def convert_content_type(ct: str) -> ContentType:
    """Convert string to ContentType enum."""
    try:
        return ContentType(ct.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {ct}")


def convert_difficulty(d: str) -> DifficultyLevel:
    """Convert string to DifficultyLevel enum."""
    try:
        return DifficultyLevel(d.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty: {d}")


def song_result_to_api(result: SongResult) -> SongResultAPI:
    """Convert internal SongResult to API model."""
    return SongResultAPI(
        song_name=result.song_name,
        artist=result.artist,
        source=result.source.value,
        source_url=result.source_url,
        confidence=result.confidence,
        chords={
            inst.value: [
                {
                    "name": c.name,
                    "frets": c.frets,
                    "fingers": c.fingers,
                    "base_fret": c.base_fret,
                    "is_barre": c.is_barre,
                    "alternative_names": c.alternative_names
                }
                for c in chords
            ]
            for inst, chords in result.chords.items()
        },
        strumming_patterns={
            inst.value: [
                {
                    "name": p.name,
                    "pattern": p.pattern,
                    "bpm": p.bpm,
                    "time_signature": p.time_signature,
                    "description": p.description,
                    "difficulty": p.difficulty.value
                }
                for p in patterns
            ]
            for inst, patterns in result.strumming_patterns.items()
        },
        tabs={
            inst.value: [
                {
                    "instrument": t.instrument.value,
                    "tuning": t.tuning,
                    "lines": t.lines,
                    "legend": t.legend
                }
                for t in tabs
            ]
            for inst, tabs in result.tabs.items()
        },
        piano_notes={
            "chords": result.piano_notes.chords,
            "melody_notes": result.piano_notes.melody_notes,
            "left_hand": result.piano_notes.left_hand,
            "right_hand": result.piano_notes.right_hand,
            "key_signature": result.piano_notes.key_signature,
            "time_signature": result.piano_notes.time_signature
        } if result.piano_notes else None,
        key=result.key,
        tempo=result.tempo,
        time_signature=result.time_signature,
        genre=result.genre,
        year=result.year,
        capo=result.capo,
        difficulty=result.difficulty.value,
        is_verified=result.is_verified
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    service = get_service()
    await service.initialize()
    cache = get_cache()
    stats = await cache.get_stats()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ai_providers=[p.name for p in service.ai_providers],
        cache_stats={
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_rate": stats.hit_rate,
            "total_entries": stats.total_entries,
            "evictions": stats.evictions
        }
    )


@app.post("/search", response_model=SearchResponseAPI)
async def search_chords(
    request: SearchRequestAPI,
    service: ChordSearchService = Depends(get_search_service)
):
    """Search for chords, tabs, and patterns for a song."""
    # Validate and convert instruments
    try:
        instruments = [convert_instrument(i) for i in request.instruments]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid instruments: {e}")
    
    # Validate content types
    content_types = None
    if request.content_types:
        try:
            content_types = [convert_content_type(ct) for ct in request.content_types]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid content types: {e}")
    
    # Validate difficulty
    difficulty = None
    if request.difficulty:
        try:
            difficulty = convert_difficulty(request.difficulty)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid difficulty: {e}")
    
    # Build internal request
    search_request = SearchRequest(
        song_name=request.song_name,
        artist=request.artist,
        instruments=instruments,
        content_types=content_types,
        difficulty=difficulty,
        use_ai=request.use_ai,
        use_web=request.use_web,
        max_results=request.max_results
    )
    
    # Perform search
    try:
        response = await service.search(search_request)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    # Record search history if user is authenticated
    user_id = await get_current_user_id(None)
    if user_id:
        await execute_insert(
            """INSERT INTO search_history (user_id, song_name, artist, instruments, result_count)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, request.song_name, request.artist,
             json.dumps([i.value for i in instruments]), len(response.results))
        )
    
    # Convert to API response
    api_results = [song_result_to_api(r) for r in response.results]
    api_query = SearchRequestAPI(
        song_name=response.query.song_name,
        artist=response.query.artist,
        instruments=[i.value for i in response.query.instruments],
        content_types=[ct.value for ct in response.query.content_types] if response.query.content_types else None,
        difficulty=response.query.difficulty.value if response.query.difficulty else None,
        use_ai=response.query.use_ai,
        use_web=response.query.use_web,
        max_results=response.query.max_results
    )
    
    return SearchResponseAPI(
        query=api_query,
        results=api_results,
        total_found=response.total_found,
        search_time_ms=response.search_time_ms,
        sources_used=response.sources_used,
        errors=response.errors
    )


@app.get("/search")
async def search_chords_get(
    song_name: str = Query(..., description="Song name"),
    artist: Optional[str] = Query(None, description="Artist name"),
    instruments: str = Query("guitar", description="Comma-separated instruments"),
    content_types: Optional[str] = Query(None, description="Comma-separated content types"),
    difficulty: Optional[str] = Query(None, description="Difficulty level"),
    use_ai: bool = Query(True, description="Use AI generation"),
    use_web: bool = Query(True, description="Search web sources"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum results"),
    service: ChordSearchService = Depends(get_search_service)
):
    """Search for chords via GET (for easy testing)."""
    request = SearchRequestAPI(
        song_name=song_name,
        artist=artist,
        instruments=[i.strip() for i in instruments.split(",")],
        content_types=[ct.strip() for ct in content_types.split(",")] if content_types else None,
        difficulty=difficulty,
        use_ai=use_ai,
        use_web=use_web,
        max_results=max_results
    )
    return await search_chords(request, service)


@app.get("/instruments")
async def list_instruments():
    """List supported instruments and their content types."""
    from config import INSTRUMENTS, INSTRUMENT_FORMATS
    
    return {
        "instruments": [
            {
                "name": inst,
                "content_types": INSTRUMENT_FORMATS.get(inst, [])
            }
            for inst in INSTRUMENTS
        ],
        "content_types": [ct.value for ct in ContentType],
        "difficulties": [d.value for d in DifficultyLevel]
    }


# ============================================================================
# CACHE ROUTES
# ============================================================================

@app.delete("/cache")
async def clear_cache():
    """Clear the search cache."""
    cache = get_cache()
    await cache.clear()
    return {"status": "cleared", "message": "Cache cleared successfully"}


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    cache = get_cache()
    stats = await cache.get_stats()
    return {
        "hits": stats.hits,
        "misses": stats.misses,
        "hit_rate": stats.hit_rate,
        "total_entries": stats.total_entries,
        "evictions": stats.evictions
    }


# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    """Register a new user."""
    # Check if email exists
    existing = await execute_one("SELECT id FROM users WHERE email = ?", (user_data.email,))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing = await execute_one("SELECT id FROM users WHERE username = ?", (user_data.username,))
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    password_hash = hash_password(user_data.password)
    user_id = await execute_insert(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        (user_data.email, user_data.username, password_hash)
    )
    
    return create_token_response(user_id, user_data.email, user_data.username)


@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """Login user."""
    print(f"DEBUG: Login attempt for email: {user_data.email}")
    user = await execute_one("SELECT id, email, username, password_hash FROM users WHERE email = ?", (user_data.email,))
    print(f"DEBUG: User found: {user is not None}")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"DEBUG: Verifying password...")
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"DEBUG: Creating token...")
    return create_token_response(user["id"], user["email"], user["username"])


@app.get("/api/me")
async def get_current_user(user_id: int = Depends(require_user_id)):
    """Get current user profile."""
    user = await execute_one("SELECT id, email, username, created_at FROM users WHERE id = ?", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================================
# SEARCH HISTORY ROUTES
# ============================================================================

@app.get("/api/history", response_model=List[SearchHistoryItem])
async def get_search_history(
    limit: int = Query(50, ge=1, le=100),
    user_id: int = Depends(require_user_id)
):
    """Get user's search history."""
    rows = await execute_query(
        """SELECT id, song_name, artist, instruments, result_count, created_at 
           FROM search_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    )
    # Parse instruments JSON
    for row in rows:
        row["instruments"] = json.loads(row["instruments"])
    return rows


# ============================================================================
# FAVORITES ROUTES
# ============================================================================

@app.post("/api/favorites", response_model=FavoriteResponse)
async def add_favorite(
    favorite: FavoriteCreate,
    user_id: int = Depends(require_user_id)
):
    """Add a song to favorites."""
    try:
        fav_id = await execute_insert(
            """INSERT INTO favorites (user_id, song_name, artist, result_data) 
               VALUES (?, ?, ?, ?)""",
            (user_id, favorite.song_name, favorite.artist, json.dumps(favorite.result_data))
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Already in favorites")
    
    fav = await execute_one("SELECT * FROM favorites WHERE id = ?", (fav_id,))
    fav["result_data"] = json.loads(fav["result_data"])
    return fav


@app.get("/api/favorites", response_model=List[FavoriteResponse])
async def get_favorites(user_id: int = Depends(require_user_id)):
    """Get user's favorites."""
    rows = await execute_query("SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    for row in rows:
        row["result_data"] = json.loads(row["result_data"])
    return rows


@app.delete("/api/favorites/{favorite_id}")
async def remove_favorite(favorite_id: int, user_id: int = Depends(require_user_id)):
    """Remove a favorite."""
    await execute_update("DELETE FROM favorites WHERE id = ? AND user_id = ?", (favorite_id, user_id))
    return {"status": "removed"}


# ============================================================================
# FEEDBACK ROUTES (persisted)
# ============================================================================

@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Submit feedback on a search result (persisted)."""
    fb_id = await execute_insert(
        """INSERT INTO feedback (user_id, result_id, song_name, artist, rating, comment, corrections)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, feedback.result_id, feedback.song_name, feedback.artist,
         feedback.rating, feedback.comment, json.dumps(feedback.corrections) if feedback.corrections else None)
    )
    
    fb = await execute_one("SELECT * FROM feedback WHERE id = ?", (fb_id,))
    if fb and fb["corrections"]:
        fb["corrections"] = json.loads(fb["corrections"])
    return fb


@app.get("/api/feedback/stats")
async def feedback_stats(user_id: int = Depends(require_user_id)):
    """Get feedback statistics for current user."""
    total = await execute_one("SELECT COUNT(*) as count FROM feedback WHERE user_id = ?", (user_id,))
    avg_rating = await execute_one("SELECT AVG(rating) as avg FROM feedback WHERE user_id = ?", (user_id,))
    return {
        "total_feedback": total["count"] if total else 0,
        "average_rating": round(avg_rating["avg"], 2) if avg_rating and avg_rating["avg"] else 0
    }


# ============================================================================
# USER PROFILE / STATS
# ============================================================================

@app.get("/api/profile", response_model=UserProfile)
async def get_profile(user_id: int = Depends(require_user_id)):
    """Get user profile with stats."""
    user = await execute_one("SELECT id, email, username, created_at FROM users WHERE id = ?", (user_id,))
    
    search_count = await execute_one("SELECT COUNT(*) as count FROM search_history WHERE user_id = ?", (user_id,))
    favorites_count = await execute_one("SELECT COUNT(*) as count FROM favorites WHERE user_id = ?", (user_id,))
    feedback_count = await execute_one("SELECT COUNT(*) as count FROM feedback WHERE user_id = ?", (user_id,))
    
    return UserProfile(
        user=user,
        stats={
            "search_count": search_count["count"] if search_count else 0,
            "favorites_count": favorites_count["count"] if favorites_count else 0,
            "feedback_count": feedback_count["count"] if feedback_count else 0
        }
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )