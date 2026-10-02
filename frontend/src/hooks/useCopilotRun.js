import { useState, useEffect, useRef, useCallback } from 'react'
import client from '../api/client'

export const useCopilotRun = (runId, onCompleted, onFailed) => {
  const [run, setRun] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const pollIntervalRef = useRef(null)
  const startTimeRef = useRef(null)

  const pollStatus = useCallback(async () => {
    if (!runId) return

    try {
      const response = await client.get(`/copilot/runs/${runId}`)
      const currentRun = response.data
      setRun(currentRun)

      // Check if finished
      if (currentRun.status === 'done') {
        stopPolling()
        if (onCompleted) onCompleted(currentRun)
      } else if (currentRun.status === 'failed') {
        stopPolling()
        if (onFailed) onFailed(currentRun.error || 'Copilot run failed')
      } else {
        // Check timeout (120 seconds limit)
        const elapsed = (Date.now() - startTimeRef.current) / 1000
        if (elapsed > 120) {
          stopPolling()
          setError('Copilot execution timed out after 2 minutes.')
          if (onFailed) onFailed('Timeout')
        }
      }
    } catch (err) {
      console.error('Error polling copilot run:', err)
      // We don't stop polling on single fetch error in case of intermittent network drops
    }
  }, [runId, onCompleted, onFailed])

  const startPolling = useCallback(() => {
    stopPolling() // Clear existing
    if (!runId) return

    setLoading(true)
    setError(null)
    startTimeRef.current = Date.now()
    
    // First immediate check
    pollStatus()
    
    // Start interval
    pollIntervalRef.current = setInterval(pollStatus, 1500)
  }, [runId, pollStatus])

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    if (runId) {
      startPolling()
    } else {
      setRun(null)
      stopPolling()
    }

    return () => stopPolling()
  }, [runId, startPolling, stopPolling])

  return { run, loading, error, refresh: pollStatus }
}
