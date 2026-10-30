import React, { useState, useEffect, useRef } from 'react'
import { Copy, Check, Play, Pause, Volume2, VolumeX } from 'lucide-react'

/**
 * StrummingPattern - Displays strumming pattern with visual notation
 * 
 * Props:
 * - pattern: StrummingPattern object from API
 * - compact: boolean - show compact version
 */
function StrummingPattern({ pattern, compact = false }) {
  const [copied, setCopied] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [volume, setVolume] = useState(0.5)
  const [bpm, setBpm] = useState(pattern.bpm || 120)
  const audioContextRef = useRef(null)
  const intervalRef = useRef(null)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(pattern.pattern)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const parsePattern = (patternStr) => {
    // Parse pattern like "D DU UDU" into array of strokes
    return patternStr.split('').filter(c => c !== ' ').map(c => {
      switch (c.toUpperCase()) {
        case 'D': return { type: 'down', symbol: '↓', label: 'Down' }
        case 'U': return { type: 'up', symbol: '↑', label: 'Up' }
        case 'X': return { type: 'mute', symbol: '✕', label: 'Muted' }
        case '-': case ' ': return { type: 'rest', symbol: '·', label: 'Rest' }
        default: return { type: 'unknown', symbol: c, label: c }
      }
    })
  }

  const strokes = parsePattern(pattern.pattern)

  const playPattern = () => {
    if (isPlaying) {
      stopPattern()
      return
    }

    // Initialize audio context
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
    }

    const ctx = audioContextRef.current
    if (ctx.state === 'suspended') {
      ctx.resume()
    }

    setIsPlaying(true)
    const beatDuration = 60000 / bpm / 4 // 16th note duration in ms
    let beatIndex = 0

    const playStroke = (stroke, index) => {
      if (!isPlaying) return

      // Create oscillator for audio feedback
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      
      osc.connect(gain)
      gain.connect(ctx.destination)
      
      // Different frequencies for down/up strokes
      if (stroke.type === 'down') {
        osc.frequency.value = 180
        osc.type = 'triangle'
      } else if (stroke.type === 'up') {
        osc.frequency.value = 220
        osc.type = 'sine'
      } else if (stroke.type === 'mute') {
        osc.frequency.value = 100
        osc.type = 'square'
      } else {
        // Rest - no sound
        return
      }
      
      gain.gain.value = volume * 0.1
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1)
      
      osc.start()
      osc.stop(ctx.currentTime + 0.1)
    }

    const nextBeat = () => {
      if (!isPlaying) return
      
      const stroke = strokes[beatIndex % strokes.length]
      playStroke(stroke, beatIndex)
      beatIndex++
      
      intervalRef.current = setTimeout(nextBeat, beatDuration)
    }

    nextBeat()
  }

  const stopPattern = () => {
    setIsPlaying(false)
    if (intervalRef.current) {
      clearTimeout(intervalRef.current)
      intervalRef.current = null
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPattern()
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const difficultyColors = {
    beginner: 'text-success',
    intermediate: 'text-warning',
    advanced: 'text-danger',
  }

  if (compact) {
    return (
      <div className="strumming-pattern" title={`${pattern.name}: ${pattern.pattern}`}>
        <span className="font-medium">{pattern.name}</span>
        <span className="ml-2 font-mono">{pattern.pattern}</span>
      </div>
    )
  }

  return (
    <div className="card bg-bg p-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{pattern.name}</span>
          <span className={`badge badge-outline ${difficultyColors[pattern.difficulty] || ''}`}>
            {pattern.difficulty.charAt(0).toUpperCase() + pattern.difficulty.slice(1)}
          </span>
          {pattern.time_signature !== '4/4' && (
            <span className="badge badge-outline">{pattern.time_signature}</span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* BPM Control */}
          <div className="flex items-center gap-1 text-sm">
            <span className="text-secondary">BPM:</span>
            <input
              type="number"
              min="40"
              max="200"
              value={bpm}
              onChange={(e) => setBpm(parseInt(e.target.value) || 120)}
              className="w-16 px-2 py-1 text-center border border-border rounded bg-bg-card text-sm"
            />
          </div>

          {/* Volume Control */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setVolume(v => v === 0 ? 0.5 : 0)}
              className="btn btn-ghost btn-icon btn-sm p-1"
              aria-label={volume === 0 ? 'Unmute' : 'Mute'}
            >
              {volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="w-20"
              aria-label="Volume"
            />
          </div>

          {/* Play/Stop */}
          <button
            onClick={playPattern}
            disabled={strokes.every(s => s.type === 'rest')}
            className="btn btn-primary btn-sm gap-1"
            aria-label={isPlaying ? 'Stop playback' : 'Play pattern'}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? 'Stop' : 'Play'}
          </button>

          {/* Copy */}
          <button
            onClick={copyToClipboard}
            className="btn btn-ghost btn-icon btn-sm p-1"
            aria-label={copied ? 'Copied!' : 'Copy pattern'}
            title={copied ? 'Copied!' : 'Copy pattern'}
          >
            {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Pattern display */}
      <div className="space-y-2">
        {/* Visual pattern */}
        <div className="strumming-pattern p-3" style={{ fontSize: '1.25rem' }}>
          {strokes.map((stroke, i) => (
            <span
              key={i}
              className={`strumming-symbol ${stroke.type} transition-colors ${
                isPlaying && i === (Math.floor(Date.now() / (60000 / bpm / 4)) % strokes.length)
                  ? 'text-primary animate-pulse'
                  : ''
              }`}
              title={`${stroke.label}${stroke.type !== 'rest' ? ' stroke' : ''}`}
            >
              {stroke.symbol}
            </span>
          ))}
        </div>

        {/* Text representation */}
        <div className="flex items-center gap-2 text-sm text-secondary flex-wrap">
          <span className="font-mono bg-bg-card px-2 py-1 rounded border border-border">
            {pattern.pattern}
          </span>
          {pattern.description && (
            <span className="text-muted">{pattern.description}</span>
          )}
        </div>

        {/* Beat counting helper */}
        <div className="text-xs text-muted flex flex-wrap gap-1">
          {strokes.map((stroke, i) => (
            <span key={i} className={`w-6 text-center ${stroke.type !== 'rest' ? 'font-semibold' : ''}`}>
              {i + 1}
            </span>
          ))}
          <span className="ml-2">← 16th notes</span>
        </div>
      </div>
    </div>
  )
}

export default StrummingPattern