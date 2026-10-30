import { useState, useCallback, useRef } from 'react'
import axios from 'axios'

const API_BASE = '/api'

export function useSearch() {
  const [results, setResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortControllerRef = useRef(null)

  const search = useCallback(async (params) => {
    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE}/search`, params, {
        signal: abortControllerRef.current.signal
      })
      setResults(response.data)
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Search error:', err)
        setError(err.response?.data?.error || 'Search failed. Please try again.')
        setResults(null)
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearResults = useCallback(() => {
    setResults(null)
    setError(null)
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }, [])

  return {
    results,
    isLoading,
    error,
    search,
    clearResults
  }
}

// Hook for fetching instruments list
export function useInstruments() {
  const [instruments, setInstruments] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchInstruments = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${API_BASE}/instruments`)
      setInstruments(response.data)
    } catch (err) {
      console.error('Failed to fetch instruments:', err)
      setError('Failed to load instruments')
    } finally {
      setIsLoading(false)
    }
  }, [])

  return { instruments, isLoading, error, fetchInstruments }
}

// Hook for health check
export function useHealthCheck() {
  const [health, setHealth] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const checkHealth = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await axios.get(`${API_BASE}/health`)
      setHealth(response.data)
    } catch (err) {
      console.error('Health check failed:', err)
      setHealth({ status: 'error', ai_providers: [] })
    } finally {
      setIsLoading(false)
    }
  }, [])

  return { health, isLoading, checkHealth }
}

// Hook for submitting feedback
export function useFeedback() {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const submitFeedback = useCallback(async (feedback) => {
    setIsSubmitting(true)
    try {
      await axios.post(`${API_BASE}/feedback`, feedback)
      return { success: true }
    } catch (err) {
      console.error('Feedback submission failed:', err)
      return { success: false, error: 'Failed to submit feedback' }
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  return { submitFeedback, isSubmitting }
}