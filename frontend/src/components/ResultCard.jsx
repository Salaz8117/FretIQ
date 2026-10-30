import { useState } from 'react'
import { 
  Guitar, Piano, Music, 
  ChevronDown, ExternalLink, CheckCircle, 
  Sparkles, Globe, Star, Copy, Heart
} from 'lucide-react'
import ChordDiagram from './ChordDiagram'
import TabNotation from './TabNotation'
import StrummingPattern from './StrummingPattern'
import PianoNotes from './PianoNotes'

function InstrumentIcon({ instrument, className = "w-4 h-4", ...props }) {
  const icons = {
    guitar: Guitar,
    piano: Piano,
    ukulele: Music,
    banjo: Music,
    mandolin: Music,
    bass: Music,
    violin: Music,
    cello: Music,
  }
  
  const Icon = icons[instrument] || Music
  return <Icon className={className} {...props} />
}

const SOURCE_ICONS = {
  ai_generated: Sparkles,
  web_scraped: Globe,
  verified: CheckCircle,
  user_submitted: Star,
}

function ResultCard({ result, index, isExpanded, onToggleExpand }) {
  const [copied, setCopied] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)
  const [rating, setRating] = useState(0)

  const SourceIcon = SOURCE_ICONS[result.source] || Sparkles
  const confidencePercent = Math.round(result.confidence * 100)

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const generateTextSummary = () => {
    let text = `${result.song_name}${result.artist ? ` - ${result.artist}` : ''}\n\n`
    
    if (result.key) text += `Key: ${result.key}\n`
    if (result.tempo) text += `Tempo: ${result.tempo} BPM\n`
    if (result.capo) text += `Capo: ${result.capo}\n`
    text += `\n`

    Object.entries(result.chords).forEach(([instrument, chords]) => {
      if (chords.length > 0) {
        text += `${instrument.toUpperCase()} CHORDS:\n`
        text += chords.map(c => c.name).join(', ') + '\n\n'
      }
    })

    Object.entries(result.strumming_patterns).forEach(([instrument, patterns]) => {
      if (patterns.length > 0) {
        text += `${instrument.toUpperCase()} STRUMMING:\n`
        patterns.forEach(p => {
          text += `${p.name}: ${p.pattern}\n`
        })
        text += '\n'
      }
    })

    if (result.piano_notes) {
      text += `PIANO CHORDS:\n${result.piano_notes.chords.join(', ')}\n\n`
      if (result.piano_notes.melody_notes.length > 0) {
        text += `MELODY: ${result.piano_notes.melody_notes.join(' ')}\n\n`
      }
    }

    return text
  }

  const handleFeedback = async (ratingValue) => {
    setRating(ratingValue)
    // In a real app, this would call the feedback API
    console.log('Feedback:', { resultId: `${result.song_name}-${result.artist}`, rating: ratingValue })
    setShowFeedback(false)
    alert('Thank you for your feedback!')
  }

  return (
    <article 
      className="card overflow-hidden animate-slide-up" 
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="card-header flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="text-3xl font-bold text-primary-light text-muted">
            {index}.
          </span>
          <div>
            <h3 className="text-xl font-bold flex items-center gap-2">
              {result.song_name}
              {result.artist && (
                <span className="text-secondary font-normal text-lg">— {result.artist}</span>
              )}
            </h3>
            <div className="flex items-center gap-3 mt-1 text-sm">
              <span className="flex items-center gap-1 text-secondary">
                <SourceIcon className="w-4 h-4" aria-hidden="true" />
                {result.source.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
              <span className="flex items-center gap-1 text-secondary">
                <span className={`w-2 h-2 rounded-full ${
                  confidencePercent >= 80 ? 'bg-success' : 
                  confidencePercent >= 60 ? 'bg-warning' : 'bg-danger'
                }`} aria-hidden="true" />
                {confidencePercent}% confidence
              </span>
              {result.is_verified && (
                <span className="flex items-center gap-1 text-success">
                  <CheckCircle className="w-4 h-4" />
                  Verified
                </span>
              )}
              {result.key && (
                <span className="badge badge-outline">
                  Key: {result.key}
                </span>
              )}
              {result.tempo && (
                <span className="badge badge-outline">
                  {result.tempo} BPM
                </span>
              )}
              {result.capo && (
                <span className="badge badge-outline">
                  Capo {result.capo}
                </span>
              )}
              {result.difficulty !== 'beginner' && (
                <span className="badge badge-primary">
                  {result.difficulty.charAt(0).toUpperCase() + result.difficulty.slice(1)}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {result.source_url && (
            <a
              href={result.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost btn-sm"
              title="View source"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
          <button
            onClick={() => copyToClipboard(generateTextSummary())}
            className="btn btn-ghost btn-sm"
            title={copied ? 'Copied!' : 'Copy all as text'}
          >
            {copied ? <CheckCircle className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={onToggleExpand}
            className="btn btn-ghost btn-sm"
            aria-expanded={isExpanded}
            aria-controls={`result-content-${index}`}
          >
            <ChevronDown className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Expandable content */}
      <div 
        id={`result-content-${index}`}
        className={`${isExpanded ? '' : 'hidden'} animate-slide-up`}
        role="region"
        aria-label={`${result.song_name} details`}
      >
        <div className="card-body space-y-6">
          {/* Chords section */}
          {Object.keys(result.chords).length > 0 && (
            <section aria-labelledby="chords-heading">
              <h4 id="chords-heading" className="font-semibold flex items-center gap-2 mb-4">
                <Music className="w-5 h-5 text-primary" />
                Chords
              </h4>
              <div className="space-y-4">
                {Object.entries(result.chords).map(([instrument, chords]) => (
                  <div key={instrument} className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-secondary">
                      {InstrumentIcon({ instrument, className: "w-4 h-4", "aria-hidden": "true" })}
                      {instrument.charAt(0).toUpperCase() + instrument.slice(1)}
                      <span className="badge badge-outline">{chords.length} chords</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {chords.map((chord, i) => (
                        <ChordDiagram key={`${instrument}-${i}`} chord={chord} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Strumming patterns */}
          {Object.keys(result.strumming_patterns).length > 0 && (
            <section aria-labelledby="strumming-heading">
              <h4 id="strumming-heading" className="font-semibold flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-secondary" />
                Strumming Patterns
              </h4>
              <div className="space-y-4">
                {Object.entries(result.strumming_patterns).map(([instrument, patterns]) => (
                  <div key={instrument} className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-secondary">
                      {InstrumentIcon({ instrument, className: "w-4 h-4", "aria-hidden": "true" })}
                      {instrument.charAt(0).toUpperCase() + instrument.slice(1)}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {patterns.map((pattern, i) => (
                        <StrummingPattern key={`${instrument}-${i}`} pattern={pattern} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Tabs */}
          {Object.keys(result.tabs).length > 0 && (
            <section aria-labelledby="tabs-heading">
              <h4 id="tabs-heading" className="font-semibold flex items-center gap-2 mb-4">
                <Music className="w-5 h-5 text-accent" />
                Tabs
              </h4>
              <div className="space-y-4">
                {Object.entries(result.tabs).map(([instrument, tabs]) => (
                  <div key={instrument} className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-secondary">
                      {InstrumentIcon({ instrument, className: "w-4 h-4", "aria-hidden": "true" })}
                      {instrument.charAt(0).toUpperCase() + instrument.slice(1)}
                    </div>
                    {tabs.map((tab, i) => (
                      <TabNotation key={`${instrument}-${i}`} tab={tab} />
                    ))}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Piano notes */}
          {result.piano_notes && (
            <section aria-labelledby="piano-heading">
              <h4 id="piano-heading" className="font-semibold flex items-center gap-2 mb-4">
                <Piano className="w-5 h-5 text-primary" />
                Piano
              </h4>
              <PianoNotes notes={result.piano_notes} />
            </section>
          )}

          {/* Feedback */}
          <div className="pt-4 border-t border-border">
            <p className="text-sm text-secondary mb-3">Was this result helpful?</p>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  type="button"
                  onClick={() => handleFeedback(star)}
                  className={`p-1 rounded transition-colors ${
                    rating >= star ? 'text-warning' : 'text-muted hover:text-warning'
                  }`}
                  aria-label={`Rate ${star} star${star > 1 ? 's' : ''}`}
                >
                  <Star className={`w-5 h-5 ${rating >= star ? 'fill-current' : ''}`} />
                </button>
              ))}
              <button
                onClick={() => setShowFeedback(!showFeedback)}
                className="btn btn-ghost btn-sm ml-2"
              >
                {showFeedback ? 'Cancel' : 'Leave detailed feedback'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}

export default ResultCard