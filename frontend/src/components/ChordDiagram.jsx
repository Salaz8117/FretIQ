import { useState } from 'react'

/**
 * ChordDiagram - Visual chord diagram for guitar, ukulele, banjo, etc.
 * 
 * Props:
 * - chord: ChordDiagram object from API
 * - size: 'small' | 'medium' | 'large'
 * - showFingers: boolean - whether to show finger numbers
 */
function ChordDiagram({ chord, size = 'medium', showFingers = true }) {
  const [showDetails, setShowDetails] = useState(false)

  // String names for different instruments (high to low)
  const stringNames = {
    guitar: ['E', 'B', 'G', 'D', 'A', 'E'],
    ukulele: ['A', 'E', 'C', 'G'],
    banjo: ['D', 'B', 'G', 'D', 'G'], // 5-string banjo
    mandolin: ['E', 'A', 'D', 'G'], // doubled strings
    bass: ['G', 'D', 'A', 'E'],
    violin: ['E', 'A', 'D', 'G'],
    cello: ['A', 'D', 'G', 'C'],
  }

  const strings = stringNames[chord.instrument] || stringNames.guitar
  const numStrings = strings.length
  const frets = chord.frets || []
  const fingers = chord.fingers || []

  // Determine fret range to display
  const playedFrets = frets.filter(f => f !== null && f !== undefined && f > 0)
  const maxFret = playedFrets.length > 0 ? Math.max(...playedFrets) : 3
  const startFret = chord.base_fret > 0 ? chord.base_fret : (playedFrets.length > 0 ? Math.min(...playedFrets) : 1)
  const displayFrets = Math.max(4, maxFret - startFret + 2)

  // Size configurations
  const sizes = {
    small: { width: 120, height: 160, dotRadius: 6, fontSize: 10, nutHeight: 8 },
    medium: { width: 160, height: 200, dotRadius: 8, fontSize: 12, nutHeight: 10 },
    large: { width: 200, height: 250, dotRadius: 10, fontSize: 14, nutHeight: 12 },
  }
  const s = sizes[size]

  const stringSpacing = (s.width - 20) / (numStrings - 1)
  const fretSpacing = (s.height - s.nutHeight - 20) / displayFrets

  const getDotPosition = (stringIndex, fretNumber) => {
    if (fretNumber === null || fretNumber === undefined) return null
    if (fretNumber === 0) return null // Open string handled separately
    if (fretNumber < startFret || fretNumber > startFret + displayFrets - 1) return null
    
    const x = 10 + stringIndex * stringSpacing
    const fretIndex = fretNumber - startFret + 0.5 // Center in fret
    const y = s.nutHeight + 10 + fretIndex * fretSpacing
    return { x, y }
  }

  const getOpenStringPosition = (stringIndex) => {
    const x = 10 + stringIndex * stringSpacing
    const y = s.nutHeight + 5
    return { x, y }
  }

  const getMutedStringPosition = (stringIndex) => {
    const x = 10 + stringIndex * stringSpacing
    const y = s.nutHeight + 5
    return { x, y }
  }

  const getFingerNumber = (stringIndex) => {
    if (showFingers && fingers[stringIndex] && fingers[stringIndex] > 0) {
      return fingers[stringIndex]
    }
    return null
  }

  return (
    <div className="chord-diagram" onClick={() => setShowDetails(!showDetails)}>
      <div className="relative">
        <svg 
          width={s.width} 
          height={s.height} 
          viewBox={`0 0 ${s.width} ${s.height}`}
          role="img"
          aria-label={`${chord.name} chord diagram for ${chord.instrument}`}
        >
          {/* Nut (thick line at top for open position) */}
          {chord.base_fret === 0 && startFret === 1 && (
            <line
              x1={10}
              y1={s.nutHeight}
              x2={s.width - 10}
              y2={s.nutHeight}
              stroke="currentColor"
              strokeWidth={3}
              strokeLinecap="round"
            />
          )}

          {/* Barre chord indicator */}
          {chord.is_barre && chord.base_fret > 0 && (
            <rect
              x={10}
              y={s.nutHeight + (chord.base_fret - 1) * fretSpacing + 10 - fretSpacing / 2}
              width={s.width - 20}
              height={fretSpacing}
              fill="currentColor"
              opacity={0.15}
              rx={2}
            />
          )}

          {/* Fret lines */}
          {[...Array(displayFrets)].map((_, i) => (
            <line
              key={i}
              x1={10}
              y1={s.nutHeight + 10 + i * fretSpacing}
              x2={s.width - 10}
              y2={s.nutHeight + 10 + i * fretSpacing}
              stroke="currentColor"
              strokeWidth={i === 0 && chord.base_fret === 0 ? 2 : 1}
              strokeDasharray={i === 0 && chord.base_fret === 0 ? '0' : '4 2'}
              strokeLinecap="round"
              opacity={i === 0 && chord.base_fret === 0 ? 1 : 0.5}
            />
          ))}

          {/* Strings (vertical lines) */}
          {strings.map((_, stringIndex) => (
            <line
              key={stringIndex}
              x1={10 + stringIndex * stringSpacing}
              y1={s.nutHeight}
              x2={10 + stringIndex * stringSpacing}
              y2={s.height - 10}
              stroke="currentColor"
              strokeWidth={1}
              strokeLinecap="round"
              opacity={0.6}
            />
          ))}

          {/* Fret number label (for non-open position) */}
          {startFret > 1 && (
            <text
              x={s.width - 15}
              y={s.nutHeight + 10 + fretSpacing / 2}
              fontSize={s.fontSize}
              fill="currentColor"
              textAnchor="end"
              dominantBaseline="middle"
              opacity={0.7}
            >
              {startFret}fr
            </text>
          )}

          {/* String labels at top */}
          {strings.map((name, stringIndex) => (
            <text
              key={stringIndex}
              x={10 + stringIndex * stringSpacing}
              y={s.nutHeight - 2}
              fontSize={s.fontSize - 2}
              fill="currentColor"
              textAnchor="middle"
              dominantBaseline="baseline"
              opacity={0.7}
            >
              {name}
            </text>
          ))}

          {/* Open strings (circles above nut) */}
          {frets.map((fret, stringIndex) => {
            if (fret === 0) {
              const pos = getOpenStringPosition(stringIndex)
              return (
                <circle
                  key={`open-${stringIndex}`}
                  cx={pos.x}
                  cy={pos.y}
                  r={s.dotRadius * 0.7}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  strokeLinecap="round"
                />
              )
            }
            if (fret === null || fret === undefined) {
              const pos = getMutedStringPosition(stringIndex)
              return (
                <g key={`muted-${stringIndex}`}>
                  <line
                    x1={pos.x - s.dotRadius}
                    y1={pos.y - s.dotRadius}
                    x2={pos.x + s.dotRadius}
                    y2={pos.y + s.dotRadius}
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                  />
                  <line
                    x1={pos.x + s.dotRadius}
                    y1={pos.y - s.dotRadius}
                    x2={pos.x - s.dotRadius}
                    y2={pos.y + s.dotRadius}
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                  />
                </g>
              )
            }
            return null
          })}

          {/* Fretted notes */}
          {frets.map((fret, stringIndex) => {
            if (fret !== null && fret !== undefined && fret > 0) {
              const pos = getDotPosition(stringIndex, fret)
              if (!pos) return null
              
              const fingerNum = getFingerNumber(stringIndex)
              
              return (
                <g key={`fretted-${stringIndex}`}>
                  {/* Dot */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={s.dotRadius}
                    fill="currentColor"
                    opacity={0.9}
                  />
                  {/* Finger number */}
                  {fingerNum && (
                    <text
                      x={pos.x}
                      y={pos.y}
                      fontSize={s.fontSize - 1}
                      fill="white"
                      textAnchor="middle"
                      dominantBaseline="central"
                      fontWeight="bold"
                      pointerEvents="none"
                    >
                      {fingerNum}
                    </text>
                  )}
                </g>
              )
            }
            return null
          })}

          {/* Barre number indicator */}
          {chord.is_barre && chord.base_fret > 0 && (
            <text
              x={5}
              y={s.nutHeight + (chord.base_fret - 0.5) * fretSpacing + 10}
              fontSize={s.fontSize}
              fill="currentColor"
              textAnchor="end"
              dominantBaseline="middle"
              fontWeight="bold"
            >
              {chord.base_fret}fr
            </text>
          )}
        </svg>

        {/* Chord name */}
        <div className="chord-name mt-2 font-semibold text-center">
          {chord.name}
          {chord.alternative_names.length > 0 && (
            <span className="text-xs text-muted ml-1">
              ({chord.alternative_names.join(', ')})
            </span>
          )}
        </div>
      </div>

      {/* Details tooltip */}
      {showDetails && (
        <div className="absolute z-10 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-bg-card border border-border rounded-lg shadow-lg text-xs text-center whitespace-nowrap animate-fade-in">
          <div className="font-medium">{chord.name} ({chord.instrument})</div>
          <div className="text-muted mt-1">
            Frets: {frets.map(f => f === null ? 'x' : f === 0 ? '0' : f).join(' ')}
          </div>
          {showFingers && fingers.some(f => f) && (
            <div className="text-muted">
              Fingers: {fingers.map(f => f || '').join(' ')}
            </div>
          )}
          {chord.is_barre && <div className="text-primary text-xs">Barre chord at fret {chord.base_fret}</div>}
        </div>
      )}
    </div>
  )
}

export default ChordDiagram