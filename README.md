# FretIQ 🎸

> Find chords, tabs, strumming patterns & notes for any song on guitar, ukulele, piano, banjo + more. Powered by AI + web scrapers. PWA + User Auth.

## Features

- **Multi-instrument support**: Guitar, Ukulele, Piano, Banjo, Mandolin, Bass, Violin, Cello
- **Multiple content types**: Chords, Tabs, Strumming Patterns, Fingerpicking, Notes, Sheet Music, Rolls
- **AI-powered generation**: Uses GPT-4o-mini via OpenRouter (primary), with fallback to Anthropic, DeepSeek, NVIDIA, Grok, Kimi
- **Web scraping**: Searches Ultimate Guitar, Chordify, E-Chords, Ukulele-Tabs
- **Interactive UI**: Visual chord diagrams, playable strumming patterns, interactive piano keyboard, tab viewer
- **Caching**: In-memory LRU cache with TTL for fast repeated searches
- **Difficulty levels**: Beginner, Intermediate, Advanced
- **Dark/Light mode**: Automatic system preference detection
- **Responsive design**: Works on desktop and mobile
- **PWA support**: Install as native app on mobile/desktop
- **User accounts**: JWT authentication, search history, favorites

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for at least one AI provider (OpenRouter recommended)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run server
python main.py
# Or with uvicorn directly:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Opens at http://localhost:3000
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# AI Provider API Keys (at least one required)
OPENROUTER_API_KEY=sk-or-...       # Primary (GPT-4o-mini)
ANTHROPIC_API_KEY=sk-ant-...       # Fallback
DEEPSEEK_API_KEY=sk-...            # Fallback
NVIDIA_API_KEY=nvapi-...           # Fallback
GROK_API_KEY=sk-...                # Fallback
KIMI_API_KEY=sk-...                # Fallback

# Search API Keys (optional)
TAVILY_API_KEY=tvly-...

# Local AI Gateway (optional)
FREE_LLMAPI_URL=http://localhost:3001/v1
FREE_LLMAPI_KEY=local

# App Settings
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# JWT Secret (change in production!)
JWT_SECRET_KEY=your-secret-key
```

## API Endpoints

### Search Chords

```http
POST /api/auth/search
Content-Type: application/json

{
  "song_name": "Wonderwall",
  "artist": "Oasis",
  "instruments": ["guitar", "ukulele"],
  "content_types": ["chords", "strumming"],
  "difficulty": "beginner",
  "use_ai": true,
  "use_web": true,
  "max_results": 5
}
```

### GET Search (for easy testing)

```http
GET /search?song_name=Wonderwall&artist=Oasis&instruments=guitar,ukulele
```

### List Instruments

```http
GET /instruments
```

### Health Check

```http
GET /health
```

### Authentication

```http
POST /api/auth/register
POST /api/auth/login
GET /api/me
```

## Architecture

```
fretiq/
├── backend/                 # FastAPI Python backend
│   ├── main.py             # FastAPI app & routes
│   ├── config.py           # Configuration & settings
│   ├── models/
│   │   ├── core.py         # Pydantic data models
│   │   └── user.py         # Auth models
│   ├── ai_providers.py     # AI provider implementations
│   ├── web_scraper.py      # Web scraper implementations
│   ├── service.py          # Main search orchestration
│   ├── cache.py            # LRU cache with TTL
│   ├── auth.py             # JWT authentication
│   ├── db.py               # SQLite + aiosqlite
│   └── requirements.txt    # Python dependencies
│
└── frontend/               # React + Vite frontend
    ├── src/
    │   ├── components/     # React components
    │   ├── hooks/          # Custom React hooks
    │   ├── App.jsx         # Main app component
    │   ├── main.jsx        # Entry point
    │   └── index.css       # Global styles
    ├── package.json
    ├── vite.config.js      # PWA config
    └── index.html
```

## Supported Instruments & Content Types

| Instrument | Chords | Tabs | Strumming | Fingerpicking | Notes | Sheet Music | Rolls |
|------------|--------|------|-----------|---------------|-------|-------------|-------|
| Guitar     | ✓      | ✓    | ✓         | ✓             |       |             |       |
| Ukulele    | ✓      | ✓    | ✓         |               |       |             |       |
| Piano      | ✓      |      |           |               | ✓     | ✓           |       |
| Banjo      | ✓      | ✓    |           |               |       |             | ✓     |
| Mandolin   | ✓      | ✓    |           |               |       |             |       |
| Bass       |        | ✓    |           |               | ✓     |             |       |
| Violin     |        |      |           |               | ✓     | ✓           |       |
| Cello      |        |      |           |               | ✓     | ✓           |       |

## AI Providers

| Provider | Model | Cost | Status |
|----------|-------|------|--------|
| OpenRouter | GPT-4o-mini | Pay-per-token | ✅ Primary |
| Anthropic | Claude 3.5 Sonnet | Pay-per-token | ⚠️ Needs credits |
| DeepSeek | DeepSeek Chat | Pay-per-token | ⚠️ Needs balance |
| NVIDIA | Nemotron 3 Ultra | Pay-per-token | ⚠️ Endpoint issues |
| Grok | Grok Beta | Pay-per-token | ⚠️ Key format |
| Kimi | Moonshot v1 8k | Pay-per-token | ⚠️ Auth issues |

## Web Sources

- **Ultimate Guitar** - Chords, tabs, strumming patterns
- **Chordify** - Chord detection from audio
- **E-Chords** - Chords and lyrics
- **Ukulele-Tabs** - Ukulele-specific chords/tabs

## Development

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Building Frontend for Production

```bash
cd frontend
npm run build
# Output in dist/
```

### Docker Deployment

```bash
# From project root
docker-compose up --build
```

## Mobile Apps

### PWA (Progressive Web App)

The app is a fully functional PWA. To install:

1. Open `https://your-domain.com` in Chrome/Edge/Safari
2. Click "Install" in address bar or menu
3. App installs like native app with offline support

### Native Android/iOS (Capacitor)

```bash
cd frontend
npm install @capacitor/core @capacitor/cli
npm install @capacitor/android @capacitor/ios

npx cap init com.fretiq.app FretIQ
npx cap add android
npx cap add ios
npm run build
npx cap sync

# Android
npx cap open android
# Build APK/AAB in Android Studio

# iOS
npx cap open ios
# Build in Xcode
```

**Note**: Native builds require Android Studio (Android) and Xcode (iOS) which must be run on respective platforms.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - feel free to use for personal or commercial projects.

## Acknowledgments

- Ultimate Guitar, Chordify, E-Chords, Ukulele-Tabs for chord data
- OpenAI, Anthropic, Google for AI models
- Lucide React for icons
- The music community for inspiration

---

Built as part of the AI Mastery Journey project 🎸