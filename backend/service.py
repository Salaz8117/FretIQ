"""
FretIQ App - Main Service
Orchestrates AI providers and web scrapers for chord search.
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import get_settings, INSTRUMENTS, INSTRUMENT_FORMATS
from models import (
    SearchRequest, SearchResponse, SongResult, Instrument,
    ContentType, DifficultyLevel, SourceType
)
from ai_providers import get_available_providers_async, AIProvider
from web_scraper import search_all_sources, SCRAPERS
from cache import get_cached_search, cache_search_result

logger = logging.getLogger(__name__)
settings = get_settings()


class ChordSearchService:
    """Main service for searching chords across multiple sources."""
    
    def __init__(self):
        self.ai_providers: List[AIProvider] = []
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service and discover available providers."""
        if self._initialized:
            return
        
        self.ai_providers = await get_available_providers_async()
        logger.info(f"Initialized with {len(self.ai_providers)} AI providers: {[p.name for p in self.ai_providers]}")
        self._initialized = True
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search for chords across all available sources."""
        start_time = time.time()
        
        # Ensure initialized
        await self.initialize()
        
        # Check cache first
        request_dict = request.model_dump()
        cached = await get_cached_search(request_dict)
        if cached:
            logger.info(f"Cache hit for: {request.song_name}")
            cached.search_time_ms = (time.time() - start_time) * 1000
            return cached
        
        all_results: List[SongResult] = []
        sources_used = []
        errors = []
        
        # Determine content types per instrument
        content_types = request.content_types or self._get_default_content_types(request.instruments)
        
        # Search AI providers
        if request.use_ai and self.ai_providers:
            ai_results, ai_errors = await self._search_ai_providers(
                request, content_types
            )
            all_results.extend(ai_results)
            errors.extend(ai_errors)
            if ai_results:
                sources_used.append("ai")
        
        # Search web scrapers
        if request.use_web:
            web_results, web_errors = await self._search_web_sources(
                request, content_types
            )
            all_results.extend(web_results)
            errors.extend(web_errors)
            if web_results:
                sources_used.append("web")
        
        # Deduplicate and rank results
        final_results = self._deduplicate_and_rank(all_results, request)
        
        # Limit results
        final_results = final_results[:request.max_results]
        
        response = SearchResponse(
            query=request,
            results=final_results,
            total_found=len(all_results),
            search_time_ms=(time.time() - start_time) * 1000,
            sources_used=sources_used,
            errors=errors
        )
        
        # Cache the result
        await cache_search_result(request_dict, response)
        
        return response
    
    def _get_default_content_types(self, instruments: List[Instrument]) -> List[ContentType]:
        """Get default content types for instruments."""
        content_types = set()
        for instrument in instruments:
            formats = INSTRUMENT_FORMATS.get(instrument.value, [])
            for fmt in formats:
                try:
                    content_types.add(ContentType(fmt))
                except ValueError:
                    pass
        return list(content_types)
    
    async def _search_ai_providers(
        self,
        request: SearchRequest,
        content_types: List[ContentType]
    ) -> tuple[List[SongResult], List[str]]:
        """Search all available AI providers."""
        results = []
        errors = []
        
        # Run providers in parallel
        tasks = []
        for provider in self.ai_providers:
            task = self._safe_ai_search(provider, request, content_types)
            tasks.append(task)
        
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(provider_results):
            provider = self.ai_providers[i]
            if isinstance(result, Exception):
                error_msg = f"{provider.name}: {str(result)}"
                logger.error(error_msg)
                errors.append(error_msg)
            elif result:
                results.append(result)
                logger.info(f"AI provider {provider.name} returned result for {request.song_name}")
        
        return results, errors
    
    async def _safe_ai_search(
        self,
        provider: AIProvider,
        request: SearchRequest,
        content_types: List[ContentType]
    ) -> Optional[SongResult]:
        """Safely search a single AI provider."""
        try:
            return await provider.generate_chords(
                song_name=request.song_name,
                artist=request.artist,
                instruments=request.instruments,
                content_types=content_types,
                difficulty=request.difficulty
            )
        except Exception as e:
            logger.error(f"AI provider {provider.name} error: {e}")
            raise
    
    async def _search_web_sources(
        self,
        request: SearchRequest,
        content_types: List[ContentType]
    ) -> tuple[List[SongResult], List[str]]:
        """Search web scrapers."""
        results = []
        errors = []
        
        try:
            web_results = await search_all_sources(
                song_name=request.song_name,
                artist=request.artist,
                instruments=request.instruments
            )
            results.extend(web_results)
        except Exception as e:
            error_msg = f"Web search: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return results, errors
    
    def _deduplicate_and_rank(
        self,
        results: List[SongResult],
        request: SearchRequest
    ) -> List[SongResult]:
        """Deduplicate and rank results by quality."""
        if not results:
            return []
        
        # Group by source and song similarity
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a fingerprint for deduplication
            fingerprint = (
                result.song_name.lower().strip(),
                (result.artist or "").lower().strip(),
                result.source.value
            )
            
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_results.append(result)
        
        # Rank by confidence and source priority
        source_priority = {
            SourceType.VERIFIED: 100,
            SourceType.AI_GENERATED: 80,
            SourceType.WEB_SCRAPED: 60,
            SourceType.USER_SUBMITTED: 40,
        }
        
        def rank_score(r: SongResult) -> float:
            base = r.confidence * 100
            source_bonus = source_priority.get(r.source, 0)
            # Bonus for having more instruments covered
            instrument_bonus = len(r.chords) * 10
            # Bonus for verified content
            verified_bonus = 20 if r.is_verified else 0
            return base + source_bonus + instrument_bonus + verified_bonus
        
        unique_results.sort(key=rank_score, reverse=True)
        return unique_results


# Global service instance
_service_instance: Optional[ChordSearchService] = None


def get_service() -> ChordSearchService:
    """Get or create global service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChordSearchService()
    return _service_instance