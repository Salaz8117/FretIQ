"""
FretIQ App - Backend Tests
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from models import (
    SearchRequest, SearchResponse, SongResult, Instrument,
    ContentType, DifficultyLevel, SourceType,
    ChordDiagram, StrummingPattern, TabNotation, PianoNotes
)
from config import INSTRUMENTS, INSTRUMENT_FORMATS, DIFFICULTY_LEVELS
from service import ChordSearchService
from cache import LRUCache, CacheStats
from ai_providers import OpenAIProvider, AnthropicProvider, GoogleProvider, LocalAIProvider
from web_scraper import UltimateGuitarScraper, EChordsScraper, UkuleleTabsScraper


class TestModels:
    """Test data models."""
    
    def test_search_request_creation(self):
        request = SearchRequest(
            song_name="Wonderwall",
            artist="Oasis",
            instruments=[Instrument.GUITAR, Instrument.UKULELE],
            content_types=[ContentType.CHORDS, ContentType.STRUMMING],
            difficulty=DifficultyLevel.BEGINNER,
            use_ai=True,
            use_web=True,
            max_results=5
        )
        assert request.song_name == "Wonderwall"
        assert request.artist == "Oasis"
        assert len(request.instruments) == 2
        assert request.max_results == 5
    
    def test_chord_diagram_creation(self):
        chord = ChordDiagram(
            name="C",
            instrument=Instrument.GUITAR,
            frets=[None, 3, 2, 0, 1, 0],
            fingers=[None, 3, 2, None, 1, None],
            base_fret=0,
            is_barre=False
        )
        assert chord.name == "C"
        assert chord.instrument == Instrument.GUITAR
        assert len(chord.frets) == 6
    
    def test_strumming_pattern_creation(self):
        pattern = StrummingPattern(
            name="Main Pattern",
            pattern="D DU UDU",
            bpm=120,
            time_signature="4/4",
            difficulty=DifficultyLevel.BEGINNER
        )
        assert pattern.pattern == "D DU UDU"
        assert pattern.bpm == 120
    
    def test_song_result_creation(self):
        result = SongResult(
            song_name="Wonderwall",
            artist="Oasis",
            source=SourceType.AI_GENERATED,
            confidence=0.85,
            key="G major",
            tempo=120,
            difficulty=DifficultyLevel.BEGINNER
        )
        assert result.song_name == "Wonderwall"
        assert result.confidence == 0.85
        assert result.source == SourceType.AI_GENERATED


class TestConfig:
    """Test configuration."""
    
    def test_instruments_list(self):
        assert "guitar" in INSTRUMENTS
        assert "ukulele" in INSTRUMENTS
        assert "piano" in INSTRUMENTS
        assert "banjo" in INSTRUMENTS
        assert len(INSTRUMENTS) == 8
    
    def test_instrument_formats(self):
        assert "chords" in INSTRUMENT_FORMATS["guitar"]
        assert "tabs" in INSTRUMENT_FORMATS["guitar"]
        assert "strumming" in INSTRUMENT_FORMATS["guitar"]
        assert "chords" in INSTRUMENT_FORMATS["ukulele"]
        assert "notes" in INSTRUMENT_FORMATS["piano"]
        assert "sheet_music" in INSTRUMENT_FORMATS["piano"]
    
    def test_difficulty_levels(self):
        assert DIFFICULTY_LEVELS == ["beginner", "intermediate", "advanced"]


class TestCache:
    """Test cache functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        cache = LRUCache(max_size=10, default_ttl=60)
        
        request_dict = {"song_name": "Test", "artist": "Artist"}
        response = SearchResponse(
            query=SearchRequest(song_name="Test", artist="Artist"),
            results=[],
            total_found=0,
            search_time_ms=100,
            sources_used=[],
            errors=[]
        )
        
        await cache.set("test_key", response)
        retrieved = await cache.get("test_key")
        
        assert retrieved is not None
        assert retrieved.total_found == 0
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        cache = LRUCache(max_size=10, default_ttl=0)  # Immediate expiration
        
        response = SearchResponse(
            query=SearchRequest(song_name="Test"),
            results=[],
            total_found=0,
            search_time_ms=100,
            sources_used=[],
            errors=[]
        )
        
        await cache.set("test_key", response, ttl=0)
        # Wait a bit for expiration
        await asyncio.sleep(0.1)
        retrieved = await cache.get("test_key")
        
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        cache = LRUCache(max_size=2, default_ttl=60)
        
        response1 = SearchResponse(query=SearchRequest(song_name="1"), results=[], total_found=0, search_time_ms=100, sources_used=[], errors=[])
        response2 = SearchResponse(query=SearchRequest(song_name="2"), results=[], total_found=0, search_time_ms=100, sources_used=[], errors=[])
        response3 = SearchResponse(query=SearchRequest(song_name="3"), results=[], total_found=0, search_time_ms=100, sources_used=[], errors=[])
        
        await cache.set("key1", response1)
        await cache.set("key2", response2)
        await cache.set("key3", response3)  # Should evict key1
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is not None
        assert await cache.get("key3") is not None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        cache = LRUCache(max_size=10, default_ttl=60)
        
        response = SearchResponse(query=SearchRequest(song_name="Test"), results=[], total_found=0, search_time_ms=100, sources_used=[], errors=[])
        
        await cache.set("key1", response)
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        
        stats = await cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5


class TestAIProviders:
    """Test AI providers (mocked)."""
    
    @pytest.mark.asyncio
    async def test_openai_provider_unavailable_without_key(self):
        provider = OpenAIProvider()
        provider.api_key = None
        assert await provider.is_available() is False
    
    @pytest.mark.asyncio
    async def test_anthropic_provider_unavailable_without_key(self):
        provider = AnthropicProvider()
        provider.api_key = None
        assert await provider.is_available() is False
    
    @pytest.mark.asyncio
    async def test_google_provider_unavailable_without_key(self):
        provider = GoogleProvider()
        provider.api_key = None
        assert await provider.is_available() is False


class TestWebScrapers:
    """Test web scrapers (mocked)."""
    
    @pytest.mark.asyncio
    async def test_ultimate_guitar_scraper_init(self):
        scraper = UltimateGuitarScraper()
        assert scraper.name == "ultimate_guitar"
        assert scraper.base_url == "https://www.ultimate-guitar.com"
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_e_chords_scraper_init(self):
        scraper = EChordsScraper()
        assert scraper.name == "e_chords"
        assert scraper.base_url == "https://www.e-chords.com"
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_ukulele_tabs_scraper_init(self):
        scraper = UkuleleTabsScraper()
        assert scraper.name == "ukulele_tabs"
        assert scraper.base_url == "https://www.ukulele-tabs.com"
        await scraper.close()


class TestService:
    """Test main service."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        service = ChordSearchService()
        # Don't actually initialize - just test instantiation
        assert service.ai_providers == []
        assert service._initialized is False
    
    @pytest.mark.asyncio
    async def test_get_default_content_types(self):
        service = ChordSearchService()
        content_types = service._get_default_content_types([Instrument.GUITAR, Instrument.PIANO])
        
        assert ContentType.CHORDS in content_types
        assert ContentType.TABS in content_types
        assert ContentType.STRUMMING in content_types
        assert ContentType.NOTES in content_types


class TestIntegration:
    """Integration tests (require API keys)."""
    
    @pytest.mark.skip(reason="Requires API keys")
    @pytest.mark.asyncio
    async def test_full_search_flow(self):
        """Test complete search flow with real APIs."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])