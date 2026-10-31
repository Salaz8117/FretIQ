"""
FretIQ App - AI Provider Module
Handles AI-based chord generation using multiple providers.
"""
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from abc import ABC, abstractmethod
import logging

import httpx
from pydantic import BaseModel

from config import get_settings, INSTRUMENTS, INSTRUMENT_FORMATS
from models import (
    Instrument, ContentType, DifficultyLevel, SourceType,
    ChordDiagram, StrummingPattern, TabNotation, PianoNotes, SongResult
)

logger = logging.getLogger(__name__)
settings = get_settings()


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        """Generate chords for a song."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider for chord generation."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"
    
    @property
    def name(self) -> str:
        return "openai"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    def _build_prompt(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> str:
        """Build the prompt for chord generation."""
        artist_str = f" by {artist}" if artist else ""
        instruments_str = ", ".join([i.value for i in instruments])
        content_str = ", ".join([c.value for c in content_types])
        difficulty_str = difficulty.value if difficulty else "beginner"
        
        return f"""You are an expert music transcriber. Generate accurate musical notation for "{song_name}"{artist_str}.

Requirements:
- Instruments: {instruments_str}
- Content types: {content_str}
- Difficulty: {difficulty_str}

Return ONLY valid JSON matching this exact structure:
{{
  "song_name": "{song_name}",
  "artist": "{artist or ''}",
  "key": "C major",
  "tempo": 120,
  "time_signature": "4/4",
  "genre": "pop",
  "capo": 0,
  "difficulty": "{difficulty_str}",
  "chords": {{
    "guitar": [
      {{"name": "C", "frets": [null, 3, 2, 0, 1, 0], "fingers": [null, 3, 2, null, 1, null], "base_fret": 0, "is_barre": false}},
      {{"name": "G", "frets": [3, 2, 0, 0, 0, 3], "fingers": [2, 1, null, null, null, 3], "base_fret": 0, "is_barre": false}}
    ],
    "ukulele": [
      {{"name": "C", "frets": [0, 0, 0, 3], "fingers": [null, null, null, 1], "base_fret": 0, "is_barre": false}}
    ],
    "piano": {{"chords": ["C", "Am", "F", "G"], "melody_notes": ["C5", "E5", "G5", "C6"]}},
    "banjo": [
      {{"name": "G", "frets": [0, 0, 0, 0, 0], "fingers": [null, null, null, null, null], "base_fret": 0, "is_barre": false}}
    ]
  }},
  "strumming_patterns": {{
    "guitar": [
      {{"name": "Main Pattern", "pattern": "D DU UDU", "bpm": 120, "time_signature": "4/4", "difficulty": "beginner"}}
    ],
    "ukulele": [
      {{"name": "Island Strum", "pattern": "D DU UDU", "bpm": 120, "time_signature": "4/4", "difficulty": "beginner"}}
    ]
  }},
  "tabs": {{
    "guitar": [
      {{"instrument": "guitar", "tuning": ["E", "A", "D", "G", "B", "E"], "lines": ["e|--0--|", "B|--1--|", "G|--0--|", "D|--2--|", "A|--3--|", "E|-----|"]}}
    ]
  }}
}}

Rules:
1. Use null for muted strings, not 0
2. Fret numbers are integers, finger numbers 1-4
3. For piano, provide chord symbols and melody notes in scientific pitch notation
4. Strumming patterns: D=down, U=up, space=rest
5. Tabs: standard ASCII tab format with string labels
6. Be accurate - only include chords/patterns that actually exist in the song
7. If unsure about specific content, omit it rather than guess"""
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        prompt = self._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return self._parse_result(result_data, SourceType.AI_GENERATED)
    
    def _parse_result(self, data: Dict[str, Any], source: SourceType) -> SongResult:
        """Parse AI response into SongResult."""
        chords = {}
        for inst_str, chord_data in data.get("chords", {}).items():
            try:
                instrument = Instrument(inst_str)
                # Handle piano specially (dict with chords/melody_notes)
                if instrument == Instrument.PIANO and isinstance(chord_data, dict):
                    continue  # Will be handled in piano_notes section
                # For other instruments, expect a list
                if isinstance(chord_data, list):
                    chords[instrument] = [
                        ChordDiagram(
                            name=c["name"],
                            instrument=instrument,
                            frets=c.get("frets", []),
                            fingers=c.get("fingers", []),
                            base_fret=c.get("base_fret", 0),
                            is_barre=c.get("is_barre", False)
                        )
                        for c in chord_data
                    ]
            except (ValueError, TypeError):
                continue
        
        strumming_patterns = {}
        for inst_str, patterns in data.get("strumming_patterns", {}).items():
            try:
                instrument = Instrument(inst_str)
                strumming_patterns[instrument] = [
                    StrummingPattern(
                        name=p["name"],
                        pattern=p["pattern"],
                        bpm=p.get("bpm"),
                        time_signature=p.get("time_signature", "4/4"),
                        difficulty=DifficultyLevel(p.get("difficulty", "beginner"))
                    )
                    for p in patterns
                ]
            except ValueError:
                continue
        
        tabs = {}
        for inst_str, tab_list in data.get("tabs", {}).items():
            try:
                instrument = Instrument(inst_str)
                tabs[instrument] = [
                    TabNotation(
                        instrument=instrument,
                        tuning=t.get("tuning", ["E", "A", "D", "G", "B", "E"]),
                        lines=t["lines"]
                    )
                    for t in tab_list
                ]
            except ValueError:
                continue
        
        piano_notes = None
        if "piano" in data.get("chords", {}) and isinstance(data["chords"]["piano"], dict):
            p = data["chords"]["piano"]
            piano_notes = PianoNotes(
                chords=p.get("chords", []),
                melody_notes=p.get("melody_notes", []),
                left_hand=p.get("left_hand", []),
                right_hand=p.get("right_hand", []),
                key_signature=p.get("key_signature"),
                time_signature=p.get("time_signature", "4/4")
            )
        
        return SongResult(
            song_name=data.get("song_name", ""),
            artist=data.get("artist"),
            source=source,
            key=data.get("key"),
            tempo=data.get("tempo"),
            time_signature=data.get("time_signature", "4/4"),
            genre=data.get("genre"),
            capo=data.get("capo"),
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            chords=chords,
            strumming_patterns=strumming_patterns,
            tabs=tabs,
            piano_notes=piano_notes,
            confidence=0.85
        )


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider for chord generation."""

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-5-sonnet-20241022"
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": "You are an expert music transcriber. Output only valid JSON.",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["content"][0]["text"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    async def is_available(self) -> bool:
        return self.api_key is not None


class GoogleProvider(AIProvider):
    """Google Gemini provider for chord generation."""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-flash"
    
    @property
    def name(self) -> str:
        return "google"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 4000,
                        "responseMimeType": "application/json"
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


class LocalAIProvider(AIProvider):
    """Local AI gateway provider (FreeLLMAPI/OmniRoute)."""
    
    def __init__(self):
        self.base_url = settings.free_llmapi_url or "http://localhost:3001/v1"
        self.api_key = settings.free_llmapi_key or "local"
        self.model = "dolphin-local"
    
    @property
    def name(self) -> str:
        return "local"
    
    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/models")
                return response.status_code == 200
        except Exception:
            return False
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


class OpenRouterProvider(AIProvider):
    """OpenRouter provider - access to 100+ models via OpenAI-compatible API."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-4o-mini"
    
    @property
    def name(self) -> str:
        return "openrouter"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://fretiq.app",
                    "X-Title": "FretIQ"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


class DeepSeekProvider(AIProvider):
    """DeepSeek provider - OpenAI-compatible API."""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
    
    @property
    def name(self) -> str:
        return "deepseek"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


class NVIDIAProvider(AIProvider):
    """NVIDIA Nemotron provider - OpenAI-compatible API."""

    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "nvidia/nemotron-3-ultra-550b-a55b"
    
    @property
    def name(self) -> str:
        return "nvidia"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("NVIDIA API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


class GrokProvider(AIProvider):
    """Grok (xAI) provider - OpenAI-compatible API."""
    
    def __init__(self):
        self.api_key = settings.grok_api_key
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-beta"
    
    @property
    def name(self) -> str:
        return "grok"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("Grok API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


class KimiProvider(AIProvider):
    """Kimi (Moonshot AI) provider - OpenAI-compatible API."""
    
    def __init__(self):
        self.api_key = settings.kimi_api_key
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = "moonshot-v1-8k"
    
    @property
    def name(self) -> str:
        return "kimi"
    
    async def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate_chords(
        self,
        song_name: str,
        artist: Optional[str],
        instruments: List[Instrument],
        content_types: List[ContentType],
        difficulty: Optional[DifficultyLevel]
    ) -> SongResult:
        if not self.api_key:
            raise ValueError("Kimi API key not configured")
        
        openai_provider = OpenAIProvider()
        prompt = openai_provider._build_prompt(song_name, artist, instruments, content_types, difficulty)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert music transcriber. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            result_data = json.loads(content)
            
            return openai_provider._parse_result(result_data, SourceType.AI_GENERATED)


# Provider registry
def get_available_providers() -> List[AIProvider]:
    """Get list of available AI providers."""
    providers = [
        OpenAIProvider(),
        AnthropicProvider(),
        GoogleProvider(),
        LocalAIProvider(),
        OpenRouterProvider(),
        DeepSeekProvider(),
        NVIDIAProvider(),
        GrokProvider(),
        KimiProvider(),
    ]
    return [p for p in providers if asyncio.run(p.is_available())]


async def get_available_providers_async() -> List[AIProvider]:
    """Get list of available AI providers (async version)."""
    providers = [
        OpenAIProvider(),
        AnthropicProvider(),
        GoogleProvider(),
        LocalAIProvider(),
        OpenRouterProvider(),
        DeepSeekProvider(),
        NVIDIAProvider(),
        GrokProvider(),
        KimiProvider(),
    ]
    available = []
    for p in providers:
        if await p.is_available():
            available.append(p)
    return available