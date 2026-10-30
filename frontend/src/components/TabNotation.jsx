import React, { useState } from 'react'
import { Copy, Check, Maximize, Minimize, ChevronDown, ChevronUp } from 'lucide-react'

/**
 * TabNotation - Displays guitar/ukulele/banjo tab notation
 * 
 * Props:
 * - tab: TabNotation object from API
 * - compact: boolean - show compact version
 */
function TabNotation({ tab, compact = false }) {
  const [isExpanded, setIsExpanded] = useState(!compact)
  const [copied, setCopied] = useState(false)
  const [fontSize, setFontSize] = useState(14)
  const [showLegend, setShowLegend] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(tab.lines.join('\n'))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const formatTabLines = () => {
    return tab.lines.map(line => {
      // Highlight string labels and fret numbers
      return line
    })
  }

  const getTuningLabel = () => {
    const tunings = {
      'E,A,D,G,B,E': 'Standard (EADGBE)',
      'D,A,D,G,B,E': 'Drop D',
      'D,G,D,G,B,D': 'Open G',
      'D,A,D,F#,A,D': 'Open D',
      'C,G,D,G,B,D': 'Open C',
      'G,C,E,A': 'Ukulele (GCEA)',
      'A,D,F#,B': 'Ukulele (ADF#B)',
      'G,D,G,B,D': 'Banjo (Open G)',
      'G,C,G,C,E': 'Banjo (Double C)',
    }
    return tunings[tab.tuning.join(',')] || tab.tuning.join(', ')
  }

  if (compact) {
    return (
      <div className="tab-notation" style={{ fontSize: `${fontSize}px` }}>
        <pre>{tab.lines.join('\n')}</pre>
      </div>
    )
  }

  return (
    <div className="card bg-bg p-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-secondary">
            {getTuningLabel()}
          </span>
          {tab.tuning.length !== 6 && (
            <span className="badge badge-outline badge-xs">
              {tab.tuning.length}-string
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFontSize(Math.max(10, fontSize - 1))}
            className="btn btn-ghost btn-icon btn-sm p-1"
            aria-label="Decrease font size"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
          <span className="text-xs text-secondary w-10 text-center">{fontSize}px</span>
          <button
            onClick={() => setFontSize(Math.min(20, fontSize + 1))}
            className="btn btn-ghost btn-icon btn-sm p-1"
            aria-label="Increase font size"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
          
          <button
            onClick={copyToClipboard}
            className="btn btn-ghost btn-icon btn-sm p-1"
            aria-label={copied ? 'Copied!' : 'Copy tab'}
            title={copied ? 'Copied!' : 'Copy tab'}
          >
            {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          </button>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="btn btn-ghost btn-icon btn-sm p-1"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            aria-expanded={isExpanded}
          >
            {isExpanded ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </button>
          
          {Object.keys(tab.legend || {}).length > 0 && (
            <button
              onClick={() => setShowLegend(!showLegend)}
              className="btn btn-ghost btn-icon btn-sm p-1"
              aria-label={showLegend ? 'Hide legend' : 'Show legend'}
              aria-expanded={showLegend}
            >
              <ChevronDown className={`w-4 h-4 ${showLegend ? 'rotate-180' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Legend */}
      {showLegend && Object.keys(tab.legend || {}).length > 0 && (
        <div className="mb-3 p-3 bg-bg-card rounded border border-border animate-slide-up">
          <div className="font-semibold mb-2">Legend</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
            {Object.entries(tab.legend).map(([symbol, meaning]) => (
              <div key={symbol} className="flex items-center gap-2">
                <code className="font-mono text-primary bg-bg px-1 rounded">{symbol}</code>
                <span className="text-secondary">{meaning}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab content */}
      <div 
        className={`tab-notation ${!isExpanded ? 'max-h-32 overflow-hidden' : ''}`}
        style={{ fontSize: `${fontSize}px` }}
        role="region"
        aria-label="Tablature"
      >
        <pre className="font-mono" style={{ lineHeight: 1.8 }}>
          {tab.lines.map((line, i) => (
            <React.Fragment key={i}>
              {line}
              {i < tab.lines.length - 1 && '\n'}
            </React.Fragment>
          ))}
        </pre>
        
        {!isExpanded && tab.lines.length > 8 && (
          <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-bg to-transparent pointer-events-none" />
        )}
      </div>

      {tab.lines.length > 8 && !isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="btn btn-outline btn-sm mt-2 w-full"
        >
          Show all {tab.lines.length} lines
        </button>
      )}
    </div>
  )
}

export default TabNotation