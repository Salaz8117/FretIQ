import { useState, useCallback } from 'react'
import { Search, Guitar, Piano, Music, X, Settings, Sparkles, Globe, Brain } from 'lucide-react'

const INSTRUMENTS = [
  { id: 'guitar', label: 'Guitar', icon: Guitar },
  { id: 'ukulele', label: 'Ukulele', icon: Music },
  { id: 'piano', label: 'Piano', icon: Piano },
  { id: 'banjo', label: 'Banjo', icon: Music },
  { id: 'mandolin', label: 'Mandolin', icon: Music },
  { id: 'bass', label: 'Bass', icon: Music },
  { id: 'violin', label: 'Violin', icon: Music },
  { id: 'cello', label: 'Cello', icon: Music },
]

const CONTENT_TYPES = [
  { id: 'chords', label: 'Chords' },
  { id: 'tabs', label: 'Tabs' },
  { id: 'strumming', label: 'Strumming' },
  { id: 'fingerpicking', label: 'Fingerpicking' },
  { id: 'notes', label: 'Notes' },
  { id: 'sheet_music', label: 'Sheet Music' },
  { id: 'rolls', label: 'Rolls' },
]

const DIFFICULTIES = [
  { id: 'beginner', label: 'Beginner' },
  { id: 'intermediate', label: 'Intermediate' },
  { id: 'advanced', label: 'Advanced' },
]

function SearchForm({ onSearch, onClear }) {
  const [songName, setSongName] = useState('')
  const [artist, setArtist] = useState('')
  const [selectedInstruments, setSelectedInstruments] = useState(['guitar'])
  const [selectedContentTypes, setSelectedContentTypes] = useState([])
  const [selectedDifficulty, setSelectedDifficulty] = useState('')
  const [useAI, setUseAI] = useState(true)
  const [useWeb, setUseWeb] = useState(true)
  const [maxResults, setMaxResults] = useState(5)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = useCallback((e) => {
    e.preventDefault()
    if (!songName.trim()) return

    onSearch({
      song_name: songName.trim(),
      artist: artist.trim() || null,
      instruments: selectedInstruments,
      content_types: selectedContentTypes.length > 0 ? selectedContentTypes : null,
      difficulty: selectedDifficulty || null,
      use_ai: useAI,
      use_web: useWeb,
      max_results: maxResults,
    })
  }, [songName, artist, selectedInstruments, selectedContentTypes, selectedDifficulty, useAI, useWeb, maxResults, onSearch])

  const handleClear = useCallback(() => {
    setSongName('')
    setArtist('')
    setSelectedInstruments(['guitar'])
    setSelectedContentTypes([])
    setSelectedDifficulty('')
    setUseAI(true)
    setUseWeb(true)
    setMaxResults(5)
    onClear()
  }, [onClear])

  const toggleInstrument = (instrument) => {
    setSelectedInstruments(prev =>
      prev.includes(instrument)
        ? prev.filter(i => i !== instrument)
        : [...prev, instrument]
    )
  }

  const toggleContentType = (type) => {
    setSelectedContentTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      {/* Main search fields */}
      <div className="card overflow-hidden">
        <div className="card-body space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="sm:col-span-3">
              <label htmlFor="song-name" className="block text-sm font-medium mb-1">
                Song Name <span className="text-danger">*</span>
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" aria-hidden="true" />
                <input
                  id="song-name"
                  type="text"
                  value={songName}
                  onChange={(e) => setSongName(e.target.value)}
                  placeholder="e.g., Wonderwall, Hotel California, Let It Be..."
                      className="pl-10 pr-4 py-3 text-lg"
                  required
                  autoFocus
                  aria-describedby="song-name-hint"
                />
              </div>
              <p id="song-name-hint" className="text-xs text-muted mt-1">Enter the song title (required)</p>
            </div>

            <div>
              <label htmlFor="artist" className="block text-sm font-medium mb-1">
                Artist
              </label>
              <div className="relative">
                <Music className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" aria-hidden="true" />
                <input
                  id="artist"
                  type="text"
                  value={artist}
                  onChange={(e) => setArtist(e.target.value)}
                  placeholder="e.g., Oasis, Adele, The Beatles"
                  className="pl-10 pr-4 py-3"
                />
              </div>
              <p className="text-xs text-muted mt-1">Optional but improves accuracy</p>
            </div>
          </div>

          {/* Instruments */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Instruments <span className="text-danger">*</span>
            </label>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Select instruments">
              {INSTRUMENTS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => toggleInstrument(id)}
                  className={`btn ${selectedInstruments.includes(id) ? 'btn-primary' : 'btn-outline'} btn-sm`}
                  aria-pressed={selectedInstruments.includes(id)}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  {label}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted mt-1">
              Select one or more instruments
            </p>
          </div>
        </div>
      </div>

      {/* Advanced options */}
      <div className="card overflow-hidden">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between p-4 hover:bg-bg-hover transition-colors"
          aria-expanded={showAdvanced}
        >
          <span className="flex items-center gap-2 font-medium">
            <Settings className="w-5 h-5" aria-hidden="true" />
            Advanced Options
          </span>
          <span className="text-muted">{showAdvanced ? 'Hide' : 'Show'}</span>
        </button>

        {showAdvanced && (
          <div className="card-body space-y-6 animate-slide-up">
            {/* Content Types */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Content Types
              </label>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Select content types">
                {CONTENT_TYPES.map(({ id, label }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => toggleContentType(id)}
                    className={`btn ${selectedContentTypes.includes(id) ? 'btn-primary' : 'btn-outline'} btn-sm`}
                    aria-pressed={selectedContentTypes.includes(id)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted mt-1">Leave empty for all available types</p>
            </div>

            {/* Difficulty */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="difficulty" className="block text-sm font-medium mb-1">
                  Difficulty Level
                </label>
                <select
                  id="difficulty"
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full"
                >
                  <option value="">Any Difficulty</option>
                  {DIFFICULTIES.map(d => (
                    <option key={d.id} value={d.id}>{d.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="max-results" className="block text-sm font-medium mb-1">
                  Max Results
                </label>
                <input
                  id="max-results"
                  type="number"
                  min="1"
                  max="20"
                  value={maxResults}
                  onChange={(e) => setMaxResults(parseInt(e.target.value) || 5)}
                  className="w-full"
                />
              </div>
            </div>

            {/* Search Sources */}
            <div>
              <label className="block text-sm font-medium mb-2">Search Sources</label>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useAI}
                    onChange={(e) => setUseAI(e.target.checked)}
                    className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="flex items-center gap-1">
                    <Brain className="w-4 h-4" aria-hidden="true" />
                    AI Generation (GPT-4, Claude, Gemini, Local)
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useWeb}
                    onChange={(e) => setUseWeb(e.target.checked)}
                    className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="flex items-center gap-1">
                    <Globe className="w-4 h-4" aria-hidden="true" />
                    Web Search (Ultimate Guitar, Chordify, etc.)
                  </span>
                </label>
              </div>
              <p className="text-xs text-muted mt-1">At least one source must be enabled</p>
            </div>

            <div className="flex justify-end pt-4 border-t border-border">
              <button
                type="button"
                onClick={handleClear}
                className="btn btn-outline btn-sm"
              >
                <X className="w-4 h-4" aria-hidden="true" />
                Clear Form
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Submit button */}
      <button
        type="submit"
        disabled={!songName.trim()}
        className="btn btn-primary btn-lg w-full sm:w-auto py-4 px-8 gap-3"
      >
        <Search className="w-5 h-5" aria-hidden="true" />
        <span>Find Chords</span>
        <Sparkles className="w-5 h-5 animate-pulse" aria-hidden="true" />
      </button>
    </form>
  )
}

export default SearchForm