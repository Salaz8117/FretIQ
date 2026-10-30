import { useState, useEffect } from 'react'
import { Search, Music, Guitar, Piano, Settings, Sparkles, Zap, Globe, Brain } from 'lucide-react'
import SearchForm from './components/SearchForm'
import ResultsDisplay from './components/ResultsDisplay'
import Header from './components/Header'
import Footer from './components/Footer'
import AuthModal from './components/AuthModal'
import { AuthProvider } from './hooks/useAuth'
import { useSearch } from './hooks/useSearch'

function App() {
  const [activeTab, setActiveTab] = useState('results')
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const { results, isLoading, error, search, clearResults } = useSearch()

  // Listen for auth modal open events
  useEffect(() => {
    const handleAuthOpen = (e) => {
      setAuthMode(e.detail === 'register' ? 'register' : 'login')
      setShowAuthModal(true)
    }
    window.addEventListener('auth:open', handleAuthOpen)
    return () => window.removeEventListener('auth:open', handleAuthOpen)
  }, [])

  return (
    <AuthProvider>
      <div className="flex flex-col min-h-screen">
        <Header />
        
        <main className="flex-1 container py-8 px-4">
          {/* Search Section */}
          <section className="mb-8 animate-slide-up" aria-labelledby="search-heading">
            <div className="max-w-3xl mx-auto">
              <SearchForm onSearch={search} onClear={clearResults} />
              
              {/* Quick stats */}
              {(results?.total_found || 0) > 0 && (
                <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm text-secondary">
                  <span className="flex items-center gap-1">
                    <Music className="w-4 h-4" />
                    Found <strong>{results.total_found}</strong> result{results.total_found !== 1 ? 's' : ''}
                  </span>
                  <span className="flex items-center gap-1">
                    <Zap className="w-4 h-4" />
                    {results.search_time_ms.toFixed(0)}ms
                  </span>
                  {results.sources_used.length > 0 && (
                    <span className="flex items-center gap-1">
                      <Globe className="w-4 h-4" />
                      Sources: {results.sources_used.map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(', ')}
                    </span>
                  )}
                </div>
              )}
              
              {error && (
                <div className="mt-4 p-4 bg-danger/10 border border-danger/20 rounded-lg text-danger text-sm animate-fade-in" role="alert">
                  <p>{error}</p>
                  {results?.errors.length && (
                    <details className="mt-2">
                      <summary className="cursor-pointer font-medium">Error details</summary>
                      <ul className="mt-1 list-disc list-inside space-y-1">
                        {results.errors.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* Results Section */}
          <section aria-labelledby="results-heading" className="animate-fade-in">
            <div className="max-w-5xl mx-auto">
              {isLoading ? (
                <LoadingState />
              ) : results?.results.length ? (
                <ResultsDisplay results={results.results} />
              ) : !isLoading && !error ? (
                <EmptyState onSearchExample={search} />
              ) : null}
            </div>
          </section>
        </main>

        <Footer />
        
        {/* Auth Modal */}
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authMode}
        />
      </div>
    </AuthProvider>
  )
}

function LoadingState() {
  return (
    <div className="text-center py-16" role="status" aria-live="polite">
      <div className="flex justify-center gap-3 mb-4">
        <div className="spinner" />
        <div className="spinner" style={{ animationDelay: '0.1s' }} />
        <div className="spinner" style={{ animationDelay: '0.2s' }} />
      </div>
      <p className="text-secondary text-lg">Searching for chords across all sources...</p>
      <p className="text-muted text-sm mt-2">Checking AI models, Ultimate Guitar, Chordify, and more</p>
    </div>
  )
}

function EmptyState({ onSearchExample }) {
  const examples = [
    { song: 'Wonderwall', artist: 'Oasis' },
    { song: 'Someone Like You', artist: 'Adele' },
    { song: 'Hotel California', artist: 'Eagles' },
    { song: 'Let It Be', artist: 'The Beatles' },
    { song: 'Sweet Home Alabama', artist: 'Lynyrd Skynyrd' },
  ]

  return (
    <div className="text-center py-16 animate-fade-in">
      <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary-light text-primary mb-6">
        <Music className="w-10 h-10" />
      </div>
      <h2 className="text-2xl font-bold mb-2">Ready to find your chords?</h2>
      <p className="text-secondary mb-8 max-w-md mx-auto">
        Enter any song and artist above, and we'll search AI models and popular chord websites 
        to find chords, tabs, strumming patterns, and notes for guitar, ukulele, piano, banjo, and more!
      </p>
      
      <div className="flex flex-wrap justify-center gap-2 mb-8">
        {examples.map((ex, i) => (
          <button
            key={i}
            onClick={() => onSearchExample({ song_name: ex.song, artist: ex.artist })}
            className="btn btn-outline btn-sm"
          >
            {ex.song} — {ex.artist}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-3xl mx-auto text-left">
        <FeatureCard icon={<Guitar />} title="Guitar" desc="Chords, tabs, strumming, fingerpicking" />
        <FeatureCard icon={<Music />} title="Ukulele" desc="Chords, tabs, island strums" />
        <FeatureCard icon={<Piano />} title="Piano" desc="Chords, melody notes, sheet music" />
        <FeatureCard icon={<Music />} title="Banjo" desc="Chords, tabs, roll patterns" />
      </div>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-3 mb-2">
        <Icon className="w-6 h-6 text-primary" />
        <h3 className="font-semibold">{title}</h3>
      </div>
      <p className="text-sm text-secondary">{desc}</p>
    </div>
  )
}

export default App