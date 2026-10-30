import { useState, useMemo } from 'react'
import ResultCard from './ResultCard'

function ResultsDisplay({ results }) {
  const [expandedIds, setExpandedIds] = useState(new Set())

  // Group results by instrument for summary
  const instrumentSummary = useMemo(() => {
    const summary = {}
    results.forEach(result => {
      Object.keys(result.chords).forEach(inst => {
        summary[inst] = (summary[inst] || 0) + result.chords[inst].length
      })
      Object.keys(result.strumming_patterns).forEach(inst => {
        summary[`${inst}_strumming`] = (summary[`${inst}_strumming`] || 0) + result.strumming_patterns[inst].length
      })
      Object.keys(result.tabs).forEach(inst => {
        summary[`${inst}_tabs`] = (summary[`${inst}_tabs`] || 0) + result.tabs[inst].length
      })
      if (result.piano_notes) {
        summary.piano = (summary.piano || 0) + 1
      }
    })
    return summary
  }, [results])

  const toggleExpand = (id) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  return (
    <div className="space-y-6" role="region" aria-label="Search results">
      {/* Results summary */}
      <div className="card">
        <div className="card-body">
          <h3 className="font-semibold mb-4">Results Overview</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(instrumentSummary).map(([key, count]) => {
              const [instrument, type] = key.includes('_') ? key.split('_') : [key, 'chords']
              const displayType = type === 'chords' ? 'Chords' : type === 'strumming' ? 'Strumming' : type === 'tabs' ? 'Tabs' : 'Notes'
              return (
                <span key={key} className="badge badge-primary">
                  {instrument.charAt(0).toUpperCase() + instrument.slice(1)}: {count} {displayType}
                </span>
              )
            })}
          </div>
        </div>
      </div>

      {/* Result cards */}
      <div className="space-y-4" role="list" aria-label="Song results">
        {results.map((result, index) => (
          <ResultCard
            key={`${result.song_name}-${result.artist}-${index}`}
            result={result}
            index={index + 1}
            isExpanded={expandedIds.has(`${result.song_name}-${result.artist}-${index}`)}
            onToggleExpand={() => toggleExpand(`${result.song_name}-${result.artist}-${index}`)}
          />
        ))}
      </div>

      {results.length > 5 && (
        <div className="text-center">
          <p className="text-secondary">
            Showing top {results.length} results. Refine your search for more specific results.
          </p>
        </div>
      )}
    </div>
  )
}

export default ResultsDisplay