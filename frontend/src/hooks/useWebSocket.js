import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

export const useWebSocket = (workspaceId, onMessageReceived, onPresenceUpdate, onTypingIndicator) => {
  const { token } = useAuth()
  const [status, setStatus] = useState('closed')
  const socketRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectDelayRef = useRef(1000) // Initial 1s reconnect delay
  const connectRef = useRef(null)
  
  // Track callbacks in refs to avoid triggering effect changes
  const callbacksRef = useRef({ onMessageReceived, onPresenceUpdate, onTypingIndicator })
  useEffect(() => {
    callbacksRef.current = { onMessageReceived, onPresenceUpdate, onTypingIndicator }
  }, [onMessageReceived, onPresenceUpdate, onTypingIndicator])

  const connect = useCallback(() => {
    if (!workspaceId || !token) return

    if (socketRef.current) {
      // Close cleanly with code 1000 so the onclose handler doesn't trigger a reconnect loop
      socketRef.current.close(1000, "Closing old connection before reconnect")
    }

    setStatus('connecting')
    const wsUrl = `${WS_URL}/${workspaceId}?token=${token}`
    const socket = new WebSocket(wsUrl)
    socketRef.current = socket

    socket.onopen = () => {
      console.log('WebSocket connected')
      setStatus('open')
      reconnectDelayRef.current = 1000 // Reset reconnect delay
    }

    socket.onmessage = (event) => {
      try {
        const data = json_parse(event.data)
        if (!data) return
        console.log('WS message received:', data)

        const { onMessageReceived, onPresenceUpdate, onTypingIndicator } = callbacksRef.current

        if (data.type === 'message' || data.type === 'agent_message') {
          if (onMessageReceived) onMessageReceived(data.message)
        } else if (data.type === 'presence') {
          if (onPresenceUpdate) onPresenceUpdate(data.online_user_ids)
        } else if (data.type === 'typing' || data.type === 'agent_typing') {
          if (onTypingIndicator) onTypingIndicator(data)
        } else if (data.type === 'error') {
          console.error('WebSocket server error:', data.detail)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message', err)
      }
    }

    socket.onclose = (event) => {
      console.log(`WebSocket closed (code: ${event.code})`)
      setStatus('closed')
      
      // Attempt reconnection with exponential backoff if not closed cleanly
      if (event.code !== 1000 && event.code !== 1001) {
        scheduleReconnect()
      }
    }

    socket.onerror = (error) => {
      console.error('WebSocket encountered error:', error)
    }
  }, [workspaceId, token])

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return
    
    console.log(`Scheduling reconnect in ${reconnectDelayRef.current}ms...`)
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = null
      // Increase delay exponentially up to 30s
      reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 1.5, 30000)
      connect()
    }, reconnectDelayRef.current)
  }, [connect])

  useEffect(() => {
    console.log("useWebSocket useEffect triggered: workspaceId=" + workspaceId + ", token=" + (token ? token.slice(-10) : "null") + ", connectChanged=" + (connectRef.current !== connect))
    connectRef.current = connect
    connect()

    return () => {
      console.log("useWebSocket useEffect cleanup running")
      if (socketRef.current) {
        socketRef.current.close(1000, "Component unmounted")
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [workspaceId, token, connect])

  const sendMessage = useCallback((channelId, content) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'message',
        channel_id: channelId,
        content: content
      }))
    } else {
      console.warn('Cannot send message: WebSocket is not open')
    }
  }, [])

  const sendTyping = useCallback((channelId, isTyping = true) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'typing',
        channel_id: channelId,
        is_typing: isTyping
      }))
    }
  }, [])

  return { status, sendMessage, sendTyping }
}

function json_parse(str) {
  try {
    return JSON.parse(str)
  } catch (e) {
    return null
  }
}
