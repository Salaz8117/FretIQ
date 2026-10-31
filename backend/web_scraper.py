"""
Music Chords App - Web Scraper Module
Searches popular chord websites for song data.
"""
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any, Set
from urllib.parse import quote_plus, urljoin
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup

from config import get_settings
from models import (
    Instrument, ContentType, DifficultyLevel, SourceType,
    ChordDiagram, StrummingPattern, TabNotation, PianoNotes, SongResult
)

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ScrapedChord:
    """Represents a scraped chord."""
    name: str
    instrument: Instrument
    frets: List[Optional[int]]
    fingers: List[Optional[int]]


class BaseScraper(ABC):
    """Base class for chord website scrapers."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        pass
    
    @abstractmethod
    async def search(self, song_name: str, artist: Optional[str]) -> List[str]:
        """Search for song URLs. Returns list of result URLs."""
        pass
    
    @abstractmethod
    async def scrape_song(self, url: str) -> Optional[SongResult]:
        """Scrape a single song page."""
        pass
    
    async def close(self):
        await self.client.aclose()


class UltimateGuitarScraper(BaseScraper):
    """Scraper for Ultimate-Guitar.com"""
    
    @property
    def name(self) -> str:
        return "ultimate_guitar"
    
    @property
    def base_url(self) -> str:
        return "https://www.ultimate-guitar.com"
    
    async def search(self, song_name: str, artist: Optional[str]) -> List[str]:
        query = f"{song_name} {artist or ''}".strip()
        search_url = f"{self.base_url}/search.php?search_type=title&value={quote_plus(query)}"
        
        try:
            response = await self.client.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find song links in search results
            urls = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/tab/" in href and "ultimate-guitar.com" in href:
                    urls.append(href if href.startswith("http") else urljoin(self.base_url, href))
            
            return list(set(urls))[:10]
        except Exception as e:
            logger.error(f"UG search error: {e}")
            return []
    
    async def scrape_song(self, url: str) -> Optional[SongResult]:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract song metadata
            title_elem = soup.find("h1", class_=re.compile(r".*title.*"))
            artist_elem = soup.find("a", class_=re.compile(r".*artist.*"))
            
            song_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
            artist = artist_elem.get_text(strip=True) if artist_elem else None
            
            # Find chord data in the page (UG stores it in a script tag)
            chords_data = self._extract_chords_data(soup)
            
            if not chords_data:
                return None
            
            return self._parse_ug_data(song_name, artist, chords_data, url)
            
        except Exception as e:
            logger.error(f"UG scrape error for {url}: {e}")
            return None
    
    def _extract_chords_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract chord data from UG's JavaScript."""
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "UGAPP.store.page" in script.string:
                # Extract the JSON data
                match = re.search(r'UGAPP\.store\.page\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        import json
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue
        return None
    
    def _parse_ug_data(
        self,
        song_name: str,
        artist: Optional[str],
        data: Dict,
        url: str
    ) -> SongResult:
        """Parse UG data into SongResult."""
        # Simplified parsing - UG data structure is complex
        chords = {}
        tab_content = data.get("data", {}).get("tab_view", {}).get("wiki_tab", {}).get("content", "")
        
        if tab_content:
            parsed_chords = self._parse_chord_text(tab_content, Instrument.GUITAR)
            if parsed_chords:
                chords[Instrument.GUITAR] = parsed_chords
        
        return SongResult(
            song_name=song_name,
            artist=artist,
            source=SourceType.WEB_SCRAPED,
            source_url=url,
            chords=chords,
            confidence=0.7
        )
    
    def _parse_chord_text(self, text: str, instrument: Instrument) -> List[ChordDiagram]:
        """Parse chord names from text and generate diagrams."""
        # Common chord patterns
        chord_pattern = r'\b([A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|add[9]|[679]|maj7|m7|7|6|9|11|13)?)\b'
        chords_found = re.findall(chord_pattern, text)
        
        unique_chords = list(dict.fromkeys(chords_found))  # Preserve order, remove duplicates
        
        diagrams = []
        for chord_name in unique_chords[:20]:  # Limit to 20 chords
            diagram = self._get_chord_diagram(chord_name, instrument)
            if diagram:
                diagrams.append(diagram)
        
        return diagrams
    
    def _get_chord_diagram(self, chord_name: str, instrument: Instrument) -> Optional[ChordDiagram]:
        """Get standard chord diagram for common chords."""
        # Simplified chord dictionary for guitar
        guitar_chords = {
            "C": ([None, 3, 2, 0, 1, 0], [None, 3, 2, None, 1, None]),
            "G": ([3, 2, 0, 0, 0, 3], [2, 1, None, None, None, 3]),
            "D": ([None, None, 0, 2, 3, 2], [None, None, None, 1, 3, 2]),
            "A": ([None, 0, 2, 2, 2, 0], [None, None, 1, 2, 3, None]),
            "E": ([0, 2, 2, 1, 0, 0], [None, 2, 3, 1, None, None]),
            "Am": ([None, 0, 2, 2, 1, 0], [None, None, 2, 3, 1, None]),
            "Em": ([0, 2, 2, 0, 0, 0], [None, 2, 3, None, None, None]),
            "F": ([1, 3, 3, 2, 1, 1], [1, 3, 4, 2, 1, 1]),  # Barre
        }
        
        if instrument == Instrument.GUITAR and chord_name in guitar_chords:
            frets, fingers = guitar_chords[chord_name]
            return ChordDiagram(
                name=chord_name,
                instrument=instrument,
                frets=frets,
                fingers=fingers,
                is_barre=chord_name == "F"
            )
        
        # For other instruments, return basic structure
        return ChordDiagram(
            name=chord_name,
            instrument=instrument,
            frets=[],
            fingers=[]
        )


class ChordifyScraper(BaseScraper):
    """Scraper for Chordify.net"""
    
    @property
    def name(self) -> str:
        return "chordify"
    
    @property
    def base_url(self) -> str:
        return "https://chordify.net"
    
    async def search(self, song_name: str, artist: Optional[str]) -> List[str]:
        query = f"{song_name} {artist or ''}".strip()
        search_url = f"{self.base_url}/search?q={quote_plus(query)}"
        
        try:
            response = await self.client.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            urls = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/chords/" in href:
                    urls.append(href if href.startswith("http") else urljoin(self.base_url, href))
            
            return list(set(urls))[:10]
        except Exception as e:
            logger.error(f"Chordify search error: {e}")
            return []
    
    async def scrape_song(self, url: str) -> Optional[SongResult]:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chordify uses JSON-LD or data attributes
            title_elem = soup.find("h1")
            song_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            return SongResult(
                song_name=song_name,
                source=SourceType.WEB_SCRAPED,
                source_url=url,
                confidence=0.6
            )
        except Exception as e:
            logger.error(f"Chordify scrape error: {e}")
            return None


class SongsterrScraper(BaseScraper):
    """Scraper for Songsterr.com (tabs)"""
    
    @property
    def name(self) -> str:
        return "songsterr"
    
    @property
    def base_url(self) -> str:
        return "https://www.songsterr.com"
    
    async def search(self, song_name: str, artist: Optional[str]) -> List[str]:
        query = f"{song_name} {artist or ''}".strip()
        search_url = f"{self.base_url}/a/wa/bestMatchForQueryString?s={quote_plus(query)}"
        
        try:
            response = await self.client.get(search_url)
            response.raise_for_status()
            data = response.json()
            
            urls = []
            for item in data.get("results", [])[:10]:
                if "id" in item:
                    urls.append(f"{self.base_url}/a/wsa/song?id={item['id']}")
            
            return urls
        except Exception as e:
            logger.error(f"Songsterr search error: {e}")
            return []
    
    async def scrape_song(self, url: str) -> Optional[SongResult]:
        # Songsterr requires more complex handling (AJAX)
        return None


class EChordsScraper(BaseScraper):
    """Scraper for E-Chords.com"""
    
    @property
    def name(self) -> str:
        return "e_chords"
    
    @property
    def base_url(self) -> str:
        return "https://www.e-chords.com"
    
    async def search(self, song_name: str, artist: Optional[str]) -> List[str]:
        query = f"{song_name} {artist or ''}".strip()
        search_url = f"{self.base_url}/search?q={quote_plus(query)}"
        
        try:
            response = await self.client.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            urls = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/chords/" in href and "/tab/" not in href:
                    urls.append(href if href.startswith("http") else urljoin(self.base_url, href))
            
            return list(set(urls))[:10]
        except Exception as e:
            logger.error(f"E-Chords search error: {e}")
            return []
    
    async def scrape_song(self, url: str) -> Optional[SongResult]:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            title_elem = soup.find("h1")
            song_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Find chord content
            content_div = soup.find("div", class_="song-lyrics") or soup.find("pre")
            chords_text = content_div.get_text() if content_div else ""
            
            chords = {}
            if chords_text:
                parsed = self._parse_chord_text(chords_text, Instrument.GUITAR)
                if parsed:
                    chords[Instrument.GUITAR] = parsed
            
            return SongResult(
                song_name=song_name,
                source=SourceType.WEB_SCRAPED,
                source_url=url,
                chords=chords,
                confidence=0.65
            )
        except Exception as e:
            logger.error(f"E-Chords scrape error: {e}")
            return None
    
    def _parse_chord_text(self, text: str, instrument: Instrument) -> List[ChordDiagram]:
        chord_pattern = r'\b([A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|add[9]|[679]|maj7|m7|7|6|9|11|13)?)\b'
        chords_found = re.findall(chord_pattern, text)
        unique_chords = list(dict.fromkeys(chords_found))
        
        diagrams = []
        for chord_name in unique_chords[:20]:
            diagram = self._get_chord_diagram(chord_name, instrument)
            if diagram:
                diagrams.append(diagram)
        return diagrams
    
    def _get_chord_diagram(self, chord_name: str, instrument: Instrument) -> Optional[ChordDiagram]:
        # Same as UG
        guitar_chords = {
            "C": ([None, 3, 2, 0, 1, 0], [None, 3, 2, None, 1, None]),
            "G": ([3, 2, 0, 0, 0, 3], [2, 1, None, None, None, 3]),
            "D": ([None, None, 0, 2, 3, 2], [None, None, None, 1, 3, 2]),
            "A": ([None, 0, 2, 2, 2, 0], [None, None, 1, 2, 3, None]),
            "E": ([0, 2, 2, 1, 0, 0], [None, 2, 3, 1, None, None]),
            "Am": ([None, 0, 2, 2, 1, 0], [None, None, 2, 3, 1, None]),
            "Em": ([0, 2, 2, 0, 0, 0], [None, 2, 3, None, None, None]),
            "F": ([1, 3, 3, 2, 1, 1], [1, 3, 4, 2, 1, 1]),
        }
        
        if instrument == Instrument.GUITAR and chord_name in guitar_chords:
            frets, fingers = guitar_chords[chord_name]
            return ChordDiagram(
                name=chord_name,
                instrument=instrument,
                frets=frets,
                fingers=fingers,
                is_barre=chord_name == "F"
            )
        return ChordDiagram(name=chord_name, instrument=instrument, frets=[], fingers=[])


class UkuleleTabsScraper(BaseScraper):
    """Scraper for Ukulele-Tabs.com"""
    
    @property
    def name(self) -> str:
        return "ukulele_tabs"
    
    @property
    def base_url(self) -> str:
        return "https://www.ukulele-tabs.com"
    
    async def search(self, song_name: str, artist: Optional[str]) -> List[str]:
        query = f"{song_name} {artist or ''}".strip()
        search_url = f"{self.base_url}/search.php?search={quote_plus(query)}"
        
        try:
            response = await self.client.get(search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            urls = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/uke-songs/" in href:
                    urls.append(href if href.startswith("http") else urljoin(self.base_url, href))
            
            return list(set(urls))[:10]
        except Exception as e:
            logger.error(f"Ukulele-Tabs search error: {e}")
            return []
    
    async def scrape_song(self, url: str) -> Optional[SongResult]:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            title_elem = soup.find("h1")
            song_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            content = soup.find("pre") or soup.find("div", class_="song-content")
            chords_text = content.get_text() if content else ""
            
            chords = {}
            if chords_text:
                parsed = self._parse_chord_text(chords_text, Instrument.UKULELE)
                if parsed:
                    chords[Instrument.UKULELE] = parsed
            
            return SongResult(
                song_name=song_name,
                source=SourceType.WEB_SCRAPED,
                source_url=url,
                chords=chords,
                confidence=0.65
            )
        except Exception as e:
            logger.error(f"Ukulele-Tabs scrape error: {e}")
            return None
    
    def _parse_chord_text(self, text: str, instrument: Instrument) -> List[ChordDiagram]:
        chord_pattern = r'\b([A-G][#b]?(?:m|maj|min|dim|aug|sus[24]?|add[9]|[679]|maj7|m7|7|6|9|11|13)?)\b'
        chords_found = re.findall(chord_pattern, text)
        unique_chords = list(dict.fromkeys(chords_found))
        
        diagrams = []
        ukulele_chords = {
            "C": ([0, 0, 0, 3], [None, None, None, 1]),
            "G": ([0, 2, 3, 2], [None, 1, 3, 2]),
            "F": ([2, 0, 1, 0], [2, None, 1, None]),
            "Am": ([2, 0, 0, 0], [2, None, None, None]),
            "D": ([2, 2, 2, 0], [1, 1, 1, None]),
            "Em": ([0, 4, 3, 2], [None, 3, 2, 1]),
        }
        
        for chord_name in unique_chords[:20]:
            if instrument == Instrument.UKULELE and chord_name in ukulele_chords:
                frets, fingers = ukulele_chords[chord_name]
                diagrams.append(ChordDiagram(
                    name=chord_name,
                    instrument=instrument,
                    frets=frets,
                    fingers=fingers
                ))
            else:
                diagrams.append(ChordDiagram(name=chord_name, instrument=instrument, frets=[], fingers=[]))
        return diagrams


# Scraper registry
SCRAPERS = [
    UltimateGuitarScraper(),
    ChordifyScraper(),
    EChordsScraper(),
    UkuleleTabsScraper(),
]


async def search_all_sources(
    song_name: str,
    artist: Optional[str],
    instruments: List[Instrument]
) -> List[SongResult]:
    """Search all available scrapers and return combined results."""
    all_results = []
    
    for scraper in SCRAPERS:
        try:
            urls = await scraper.search(song_name, artist)
            
            for url in urls[:3]:  # Limit per source
                result = await scraper.scrape_song(url)
                if result and result.chords:
                    # Filter to requested instruments
                    filtered_chords = {
                        k: v for k, v in result.chords.items() 
                        if k in instruments
                    }
                    if filtered_chords:
                        result.chords = filtered_chords
                        all_results.append(result)
                        
        except Exception as e:
            logger.error(f"Error with {scraper.name}: {e}")
        finally:
            await scraper.close()
    
    return all_results


async def search_web_fallback(
    song_name: str,
    artist: Optional[str],
    instruments: List[Instrument]
) -> List[SongResult]:
    """Fallback web search using search engines."""
    # This would integrate with SerpAPI, Bing, or similar
    # For now, return empty - requires API keys
    return []