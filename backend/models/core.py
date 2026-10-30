"""
FretIQ App - Data Models
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Instrument(str, Enum):
    GUITAR = "guitar"
    UKULELE = "ukulele"
    PIANO = "piano"
    BANJO = "banjo"
    MANDOLIN = "mandolin"
    BASS = "bass"
    VIOLIN = "violin"
    CELLO = "cello"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContentType(str, Enum):
    CHORDS = "chords"
    TABS = "tabs"
    STRUMMING = "strumming"
    FINGERPICKING = "fingerpicking"
    NOTES = "notes"
    SHEET_MUSIC = "sheet_music"
    ROLLS = "rolls"


class SourceType(str, Enum):
    AI_GENERATED = "ai_generated"
    WEB_SCRAPED = "web_scraped"
    USER_SUBMITTED = "user_submitted"
    VERIFIED = "verified"


class SearchRequest(BaseModel):
    """Request model for searching song chords."""
    song_name: str = Field(..., min_length=1, max_length=200, description="Name of the song")
    artist: Optional[str] = Field(default=None, max_length=200, description="Artist name")
    instruments: List[Instrument] = Field(default=[Instrument.GUITAR], description="Instruments to search for")
    content_types: Optional[List[ContentType]] = Field(default=None, description="Types of content to retrieve")
    difficulty: Optional[DifficultyLevel] = Field(default=None, description="Preferred difficulty level")
    use_ai: bool = Field(default=True, description="Use AI generation")
    use_web: bool = Field(default=True, description="Search web sources")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum results per instrument")


class ChordDiagram(BaseModel):
    """Chord diagram/fingering representation."""
    name: str
    instrument: Instrument
    frets: List[Optional[int]] = Field(default=[], description="Fret numbers for each string (None = muted)")
    fingers: List[Optional[int]] = Field(default=[], description="Finger numbers (1=index, 2=middle, 3=ring, 4=pinky)")
    base_fret: int = Field(default=0, description="Starting fret for barre chords")
    is_barre: bool = Field(default=False)
    alternative_names: List[str] = Field(default=[])


class StrummingPattern(BaseModel):
    """Strumming pattern representation."""
    name: str
    pattern: str = Field(..., description="Pattern string (e.g., 'D DU UDU')")
    bpm: Optional[int] = Field(default=None, description="Beats per minute")
    time_signature: str = Field(default="4/4")
    description: Optional[str] = None
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)


class TabNotation(BaseModel):
    """Guitar/Ukulele/Banjo tab notation."""
    instrument: Instrument
    tuning: List[str] = Field(default=["E", "A", "D", "G", "B", "E"], description="String tuning")
    lines: List[str] = Field(..., description="Tab lines")
    legend: Dict[str, str] = Field(default={}, description="Symbol legend")


class PianoNotes(BaseModel):
    """Piano notes/chords representation."""
    chords: List[str] = Field(default=[], description="Chord symbols (e.g., 'Cmaj7', 'Am')")
    melody_notes: List[str] = Field(default=[], description="Melody note sequence")
    left_hand: List[str] = Field(default=[], description="Left hand accompaniment")
    right_hand: List[str] = Field(default=[], description="Right hand melody")
    key_signature: Optional[str] = None
    time_signature: str = Field(default="4/4")


class SongResult(BaseModel):
    """Complete song result with all instrument data."""
    song_name: str
    artist: Optional[str] = None
    source: SourceType
    source_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    
    # Instrument-specific content
    chords: Dict[Instrument, List[ChordDiagram]] = Field(default={})
    strumming_patterns: Dict[Instrument, List[StrummingPattern]] = Field(default={})
    tabs: Dict[Instrument, List[TabNotation]] = Field(default={})
    piano_notes: Optional[PianoNotes] = None
    
    # Metadata
    key: Optional[str] = None
    tempo: Optional[int] = None
    time_signature: str = Field(default="4/4")
    genre: Optional[str] = None
    year: Optional[int] = None
    capo: Optional[int] = None
    
    # Difficulty and verification
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    is_verified: bool = Field(default=False)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: SearchRequest
    results: List[SongResult] = Field(default=[])
    total_found: int = 0
    search_time_ms: float = 0.0
    sources_used: List[str] = Field(default=[])
    errors: List[str] = Field(default=[])


class UserFeedback(BaseModel):
    """User feedback on a result."""
    result_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class CacheEntry(BaseModel):
    """Cache entry for search results."""
    key: str
    value: SearchResponse
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    hit_count: int = 0