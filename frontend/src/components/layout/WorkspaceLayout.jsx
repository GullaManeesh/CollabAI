import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, Outlet, useNavigate } from 'react-router-dom'
import { useWorkspace } from '../../context/WorkspaceContext'
import { useAuth } from '../../context/AuthContext'
import { useWebSocket } from '../../hooks/useWebSocket'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

const WorkspaceLayout = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { token, loading: authLoading } = useAuth()
  const { workspace, activeWorkspaceId, selectWorkspace } = useWorkspace()
  
  // States updated via WebSocket events
  const [onlineUserIds, setOnlineUserIds] = useState([])
  const [typingUsers, setTypingUsers] = useState({}) // { user_id: { channel_id, user_name } }
  const [wsMessages, setWsMessages] = useState([])
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  
  // Ref to clear typing timeouts
  const typingTimeoutsRef = useRef({})

  // Redirect to login if token missing (checked after auth loading finishes)
  useEffect(() => {
    if (!authLoading && !token) {
      navigate('/login')
    }
  }, [token, authLoading, navigate])

  // Select active workspace when path id changes
  useEffect(() => {
    if (id && id !== activeWorkspaceId) {
      selectWorkspace(id)
    }
  }, [id, activeWorkspaceId, selectWorkspace])

  // Callback when a chat message is broadcast
  const handleMessageReceived = useCallback((message) => {
    setWsMessages((prev) => [...prev, message])
    
    // Clear typing status for this sender immediately since they sent the message
    const senderKey = message.sender_type === 'agent'
      ? `agent:${message.sender_id}`
      : message.sender_id
    if (senderKey) {
      setTypingUsers((prev) => {
        const next = { ...prev }
        delete next[senderKey]
        return next
      })
    }
  }, [])

  // Callback for online presence updates
  const handlePresenceUpdate = useCallback((onlineIds) => {
    setOnlineUserIds(onlineIds)
  }, [])

  // Callback for typing indicator broadcast
  const handleTypingIndicator = useCallback((data) => {
    const { user_id, user_name, agent, channel_id, type, is_typing = true } = data
    
    const targetKey = type === 'agent_typing' ? `agent:${agent}` : user_id
    const targetName = type === 'agent_typing' ? `${agent.toUpperCase()} Agent` : user_name
    if (!targetKey || !targetName) return

    if (!is_typing) {
      if (typingTimeoutsRef.current[targetKey]) {
        clearTimeout(typingTimeoutsRef.current[targetKey])
        delete typingTimeoutsRef.current[targetKey]
      }
      setTypingUsers((prev) => {
        const next = { ...prev }
        delete next[targetKey]
        return next
      })
      return
    }

    setTypingUsers((prev) => ({
      ...prev,
      [targetKey]: { channel_id: channel_id, user_name: targetName }
    }))

    // Clear indicator after 3 seconds of inactivity
    if (typingTimeoutsRef.current[targetKey]) {
      clearTimeout(typingTimeoutsRef.current[targetKey])
    }

    typingTimeoutsRef.current[targetKey] = setTimeout(() => {
      setTypingUsers((prev) => {
        const next = { ...prev }
        delete next[targetKey]
        return next
      })
      delete typingTimeoutsRef.current[targetKey]
    }, 3000)
  }, [])

  // Instantiate live socket connection at layout level
  const { status: wsStatus, sendMessage, sendTyping } = useWebSocket(
    id,
    handleMessageReceived,
    handlePresenceUpdate,
    handleTypingIndicator
  )

  // Clean up typing timeouts on unmount
  useEffect(() => {
    return () => {
      Object.values(typingTimeoutsRef.current).forEach(clearTimeout)
    }
  }, [])

  if (authLoading || !workspace) {
    return (
      <div className="h-screen w-screen bg-slate-50 flex items-center justify-center flex-col space-y-3 font-sans">
        <div className="w-9 h-9 border-3 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
        <div className="text-slate-500 text-xs font-medium tracking-wide">Synchronizing workspace...</div>
      </div>
    )
  }

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-ink text-paper">
      {/* Sidebar - Pinned LEFT */}
      <Sidebar isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0 h-dvh overflow-hidden">
        {/* TopBar - Header */}
        <TopBar wsStatus={wsStatus} onlineCount={onlineUserIds.length || 1} onMenuClick={() => setMobileNavOpen(true)} />

        {/* Dynamic page container */}
        <main className="flex-grow min-h-0 relative">
          <Outlet context={{ 
            wsStatus, 
            sendMessage, 
            sendTyping, 
            onlineUserIds, 
            typingUsers, 
            wsMessages,
            setWsMessages
          }} />
        </main>
      </div>
    </div>
  )
}

export default WorkspaceLayout
