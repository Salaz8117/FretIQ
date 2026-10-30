import React, { useState, useMemo } from 'react'
import { Copy, Check, Piano, Music, Volume2, VolumeX, Play, Pause } from 'lucide-react'

/**
 * PianoNotes - Displays piano chords and melody notes
 * 
 * Props:
 * - notes: PianoNotes object from API
 * - compact: boolean - show compact version
 */
function PianoNotes({ notes, compact = false }) {
  const [copied, setCopied] = useState(false)
  const [showKeyboard, setShowKeyboard] = useState(true)
  const [playbackNote, setPlaybackNote] = useState(null)

  // Piano key layout (white keys with black key positions)
  const WHITE_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
  const BLACK_KEYS = ['C#', 'D#', '', 'F#', 'G#', 'A#', '']
  const OCTAVES = [3, 4, 5, 6] // C3 to B6

  // Generate all notes in range
  const allNotes = []
  OCTAVES.forEach(octave => {
    WHITE_KEYS.forEach((whiteKey, i) => {
      const noteName = `${whiteKey}${octave}`
      allNotes.push({ note: noteName, isWhite: true, index: allNotes.length })
      if (BLACK_KEYS[i]) {
        allNotes.push({ note: `${BLACK_KEYS[i]}${octave}`, isWhite: false, index: allNotes.length })
      }
    })
  })

  // Parse chord symbols to notes
  const chordToNotes = (chordSymbol) => {
    // Simplified chord parsing - in reality this would be more complex
    const rootMatch = chordSymbol.match(/^([A-G][#b]?)/)
    if (!rootMatch) return []
    
    const root = rootMatch[1]
    const quality = chordSymbol.slice(root.length)
    
    // Note to semitone mapping
    const noteToSemitone = {
      'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
      'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
      'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }
    
    const rootSemitone = noteToSemitone[root]
    if (rootSemitone === undefined) return []
    
    // Chord quality intervals (simplified)
    const intervals = {
      '': [0, 4, 7],           // Major
      'm': [0, 3, 7],          // Minor
      'maj': [0, 4, 7],        // Major
      'maj7': [0, 4, 7, 11],   // Major 7
      'm7': [0, 3, 7, 10],     // Minor 7
      '7': [0, 4, 7, 10],      // Dominant 7
      'dim': [0, 3, 6],        // Diminished
      'aug': [0, 4, 8],        // Augmented
      'sus2': [0, 2, 7],       // Sus2
      'sus4': [0, 5, 7],       // Sus4
      '6': [0, 4, 7, 9],       // Major 6
      'm6': [0, 3, 7, 9],      // Minor 6
      '9': [0, 4, 7, 10, 14],  // Dominant 9
      'maj9': [0, 4, 7, 11, 14], // Major 9
      'm9': [0, 3, 7, 10, 14], // Minor 9
    }
    
    const chordIntervals = intervals[quality] || intervals['']
    return chordIntervals.map(interval => (rootSemitone + interval) % 12)
  }

  // Get active notes from chords
  const activeChordNotes = React.useMemo(() => {
    const active = new Set()
    notes.chords.forEach(chord => {
      chordToNotes(chord).forEach(semitone => active.add(semitone))
    })
    return active
  }, [notes.chords])

  // Get active melody notes
  const activeMelodyNotes = React.useMemo(() => {
    const active = new Set()
    notes.melody_notes.forEach(note => {
      const match = note.match(/^([A-G][#b]?)(\d+)$/)
      if (match) {
        const [, noteName, octave] = match
        const noteToSemitone = {
          'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
          'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
          'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        const semitone = noteToSemitone[noteName]
        if (semitone !== undefined) {
          active.add(semitone + (parseInt(octave) + 1) * 12) // MIDI note number
        }
      }
    })
    return active
  }, [notes.melody_notes])

  const isNoteActive = (noteName) => {
    const match = noteName.match(/^([A-G][#b]?)(\d+)$/)
    if (!match) return false
    const [, noteNameOnly, octave] = match
    const noteToSemitone = {
      'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
      'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
      'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }
    const semitone = noteToSemitone[noteNameOnly]
    if (semitone === undefined) return false
    const midiNote = semitone + (parseInt(octave) + 1) * 12
    
    return activeChordNotes.has(semitone) || activeMelodyNotes.has(midiNote)
  }

  const getNoteType = (noteName) => {
    const match = noteName.match(/^([A-G][#b]?)(\d+)$/)
    if (!match) return 'none'
    const [, noteNameOnly, octave] = match
    const noteToSemitone = {
      'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
      'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
      'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }
    const semitone = noteToSemitone[noteNameOnly]
    if (semitone === undefined) return 'none'
    const midiNote = semitone + (parseInt(octave) + 1) * 12
    
    const inChord = activeChordNotes.has(semitone)
    const inMelody = activeMelodyNotes.has(midiNote)
    
    if (inChord && inMelody) return 'both'
    if (inChord) return 'chord'
    if (inMelody) return 'melody'
    return 'none'
  }

  const copyToClipboard = async () => {
    const text = `Chords: ${notes.chords.join(', ')}\nMelody: ${notes.melody_notes.join(' ')}\nLeft Hand: ${notes.left_hand.join(', ')}\nRight Hand: ${notes.right_hand.join(', ')}`
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {notes.chords.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-secondary">Chords:</span>
            {notes.chords.map((chord, i) => (
              <span key={i} className="badge badge-primary">{chord}</span>
            ))}
          </div>
        )}
        {notes.melody_notes.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-secondary">Melody:</span>
            <span className="font-mono text-sm">{notes.melody_notes.join(' ')}</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h4 className="font-semibold flex items-center gap-2">
            <Piano className="w-5 h-5 text-primary" />
            Piano
          </h4>
          {notes.key_signature && (
            <span className="badge badge-primary">Key: {notes.key_signature}</span>
          )}
          <span className="badge badge-outline">{notes.time_signature}</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={copyToClipboard}
            className="btn btn-ghost btn-icon btn-sm p-1"
            aria-label={copied ? 'Copied!' : 'Copy notes'}
            title={copied ? 'Copied!' : 'Copy all notes'}
          >
            {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setShowKeyboard(!showKeyboard)}
            className="btn btn-ghost btn-sm gap-1"
          >
            <Piano className="w-4 h-4" />
            {showKeyboard ? 'Hide' : 'Show'} Keyboard
          </button>
        </div>
      </div>

      {/* Chords section */}
      {notes.chords.length > 0 && (
        <section className="space-y-2">
          <h5 className="font-medium text-secondary flex items-center gap-2">
            <Music className="w-4 h-4" />
            Chords
          </h5>
          <div className="flex flex-wrap gap-2">
            {notes.chords.map((chord, i) => (
              <span key={i} className="badge badge-primary text-base px-3 py-1">{chord}</span>
            ))}
          </div>
        </section>
      )}

      {/* Melody section */}
      {notes.melody_notes.length > 0 && (
        <section className="space-y-2">
          <h5 className="font-medium text-secondary flex items-center gap-2">
            <Music className="w-4 h-4" />
            Melody
          </h5>
          <div className="font-mono text-sm text-primary bg-bg-card p-3 rounded border border-border flex flex-wrap gap-1">
            {notes.melody_notes.map((note, i) => (
              <span key={i} className="px-1">{note}</span>
            ))}
          </div>
        </section>
      )}

      {/* Left/Right hand */}
      {(notes.left_hand.length > 0 || notes.right_hand.length > 0) && (
        <section className="space-y-2">
          <h5 className="font-medium text-secondary">Hand Parts</h5>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {notes.left_hand.length > 0 && (
              <div className="bg-bg-card p-3 rounded border border-border">
                <div className="text-xs text-muted mb-1">Left Hand</div>
                <div className="font-mono text-sm flex flex-wrap gap-1">
                  {notes.left_hand.map((note, i) => (
                    <span key={i} className="px-1">{note}</span>
                  ))}
                </div>
              </div>
            )}
            {notes.right_hand.length > 0 && (
              <div className="bg-bg-card p-3 rounded border border-border">
                <div className="text-xs text-muted mb-1">Right Hand</div>
                <div className="font-mono text-sm flex flex-wrap gap-1">
                  {notes.right_hand.map((note, i) => (
                    <span key={i} className="px-1">{note}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Interactive Keyboard */}
      {showKeyboard && (
        <section className="space-y-2">
          <h5 className="font-medium text-secondary">Interactive Keyboard</h5>
          <div className="relative bg-bg-card p-4 rounded border border-border">
            <div className="flex gap-0.5 overflow-x-auto pb-2" style={{ minWidth: '100%' }}>
              {allNotes.map((noteData, i) => {
                const isActive = isNoteActive(noteData.note)
                const noteType = getNoteType(noteData.note)
                
                return (
                  <div
                    key={i}
                    className={`piano-key ${noteData.isWhite ? 'white' : 'black'} ${isActive ? 'active' : ''} ${noteType === 'melody' ? 'melody' : ''} ${noteType === 'chord' ? 'chord' : ''} ${noteType === 'both' ? 'both' : ''}`}
                    style={{
                      width: noteData.isWhite ? '40px' : '24px',
                      height: noteData.isWhite ? '140px' : '90px',
                      zIndex: noteData.isWhite ? 1 : 2,
                      marginLeft: noteData.isWhite ? 0 : '-12px',
                    }}
                    title={`${noteData.note} ${noteType !== 'none' ? `(${noteType})` : ''}`}
                    onClick={() => {
                      // Play note sound
                      setPlaybackNote(noteData.note)
                      setTimeout(() => setPlaybackNote(null), 300)
                    }}
                  >
                    {noteData.isWhite && (
                      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-muted">
                        {noteData.note}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            
            {/* Legend */}
            <div className="flex flex-wrap gap-4 mt-3 pt-3 border-t border-border">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 rounded border border-border bg-white" />
                <span>White Key</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 rounded bg-gray-800" />
                <span>Black Key</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 rounded border border-primary bg-primary/20" />
                <span>Chord Tone</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 rounded border border-secondary bg-secondary/20" />
                <span>Melody Note</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 rounded border border-primary bg-gradient-to-r from-primary/20 to-secondary/20" />
                <span>Both</span>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

export default PianoNotes