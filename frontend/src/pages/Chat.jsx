import React, { useEffect, useState, useRef, useCallback } from 'react'
import { useOutletContext, useParams } from 'react-router-dom'
import { Send, Sparkles, User, Paperclip, ChevronRight, FileText, Bot, ArrowDown, AtSign, Zap, BookOpen, Calendar, HelpCircle, Layers } from 'lucide-react'
import client from '../api/client'
import { useWorkspace } from '../context/WorkspaceContext'
import { useAuth } from '../context/AuthContext'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { motion, AnimatePresence } from 'framer-motion'

const mergeIncomingMessages = (currentMessages, incomingMessages) => {
  const next = [...currentMessages]

  incomingMessages.forEach((message) => {
    const existingIndex = next.findIndex((existing) => existing.id === message.id)
    if (existingIndex >= 0) return

    const matchingIndex = next.findIndex((existing) => {
      if (
        String(existing.sender_id) !== String(message.sender_id) ||
        existing.sender_type !== message.sender_type ||
        existing.content !== message.content
      ) return false

      const existingTime = new Date(existing.created_at).getTime()
      const messageTime = new Date(message.created_at).getTime()
      return Number.isFinite(existingTime) && Number.isFinite(messageTime)
        && Math.abs(existingTime - messageTime) <= 10000
    })
    if (matchingIndex >= 0) {
      const existingIsLocal = String(next[matchingIndex].id).startsWith('local-')
      const messageIsLocal = String(message.id).startsWith('local-')
      if (existingIsLocal && !messageIsLocal) {
        next[matchingIndex] = message
      }
      return
    }

    next.push(message)
  })

  return next.sort((left, right) => new Date(left.created_at) - new Date(right.created_at))
}

const cleanAgentContent = (content) => String(content || '')
  .replace(/【[^】\n]{1,80}】/g, '')
  .replace(/\[\d+†L\d+(?:-L\d+)?\]/g, '')
  .replace(/[ \t]{2,}/g, ' ')
  .replace(/\n{3,}/g, '\n\n')
  .trim()

const Chat = () => {
  const { id } = useParams()
  const { workspace } = useWorkspace()
  const { user } = useAuth()
  
  const { 
    wsStatus, 
    sendMessage, 
    sendTyping, 
    typingUsers, 
    wsMessages,
    setWsMessages
  } = useOutletContext()

  const [messages, setMessages] = useState([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [hasMore, setHasMore] = useState(false)
  const [showMentionPicker, setShowMentionPicker] = useState(false)
  const [mentionSearch, setMentionSearch] = useState('')
  const [expandedCitations, setExpandedCitations] = useState({})
  const [showScrollPill, setShowScrollPill] = useState(false)

  const messagesEndRef = useRef(null)
  const listContainerRef = useRef(null)
  const typingTimeoutRef = useRef(null)

  const channelId = workspace?.channels?.team_chat

  const agents = [
    { key: 'research', name: 'Research Agent', desc: 'Queries workspace documents and previous decisions', icon: BookOpen },
    { key: 'planner', name: 'Planner Agent', desc: 'Structures execution roadmaps, milestones and tasks', icon: Calendar },
    { key: 'docs', name: 'Documentation Agent', desc: 'Drafts comprehensive markdown specs and summaries', icon: FileText }
  ]

  const fetchHistory = useCallback(async () => {
    if (!channelId) return
    setLoading(true)
    try {
      const response = await client.get(`/channels/${channelId}/messages?limit=50`)
      setMessages(mergeIncomingMessages([], response.data.messages))
      setHasMore(response.data.has_more)
      setTimeout(scrollToBottom, 50)
    } catch (err) {
      console.error("Failed to load messages", err)
    } finally {
      setLoading(false)
    }
  }, [channelId])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  useEffect(() => {
    const channelMessages = wsMessages.filter((message) => message.channel_id === channelId)
    if (channelMessages.length > 0) {
      setMessages((prev) => mergeIncomingMessages(prev, channelMessages))
      setWsMessages((prev) => prev.filter((message) => message.channel_id !== channelId))
      
      const container = listContainerRef.current
      if (container) {
        const threshold = 100
        const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight <= threshold
        if (isNearBottom) {
          setTimeout(scrollToBottom, 30)
        } else {
          setShowScrollPill(true)
        }
      }
    }
  }, [wsMessages, channelId, setWsMessages])

  useEffect(() => {
    if (!channelId) return undefined

    const intervalId = setInterval(async () => {
      try {
        const response = await client.get(`/channels/${channelId}/messages?limit=50`)
        setMessages((prev) => mergeIncomingMessages(response.data.messages, prev))
      } catch (err) {
        console.debug('Chat history reconciliation skipped', err)
      }
    }, 1200)

    return () => clearInterval(intervalId)
  }, [channelId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    setShowScrollPill(false)
  }

  const handleContentChange = (e) => {
    const val = e.target.value
    setContent(val)
    
    const lastWord = val.split(' ').pop()
    if (lastWord.startsWith('@')) {
      setShowMentionPicker(true)
      setMentionSearch(lastWord.substring(1).toLowerCase())
    } else {
      setShowMentionPicker(false)
    }

    if (channelId) {
      sendTyping(channelId, true)
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current)
      typingTimeoutRef.current = setTimeout(() => {
        sendTyping(channelId, false)
        typingTimeoutRef.current = null
      }, 1500)
    }
  }

  const selectMention = (agentKey) => {
    const words = content.split(' ')
    words.pop()
    words.push(`@${agentKey} `)
    setContent(words.join(' '))
    setShowMentionPicker(false)
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!content.trim() || !channelId) return

    const messageContent = content
    setContent('')
    setShowMentionPicker(false)
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
      typingTimeoutRef.current = null
    }
    sendTyping(channelId, false)

    const optimisticMessage = {
      id: `local-${Date.now()}`,
      workspace_id: id,
      channel_id: channelId,
      sender_type: 'user',
      sender_id: user?.id,
      sender_name: user?.name || 'You',
      content: messageContent,
      citations: [],
      run_id: null,
      mentioned_agents: [],
      indexed: false,
      created_at: new Date().toISOString()
    }

    if (wsStatus === 'open') {
      setMessages((prev) => [...prev, optimisticMessage])
      sendMessage(channelId, messageContent)
      setTimeout(scrollToBottom, 30)
      return
    }

    try {
      const response = await client.post(`/channels/${channelId}/messages`, { content: messageContent })
      setMessages((prev) => {
        if (prev.some((m) => m.id === response.data.id)) return prev
        return [...prev, response.data]
      })
      setTimeout(scrollToBottom, 30)
    } catch (err) {
      console.error("Failed to send message while WebSocket is unavailable", err)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(e)
    }
    if (e.key === 'Escape') {
      setShowMentionPicker(false)
    }
  }

  const toggleCitations = (msgId) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }))
  }

  const filteredAgents = agents.filter(a => a.key.includes(mentionSearch))

  return (
    <div className="absolute inset-0 flex flex-col bg-[#F8F8F6] text-[#18181B] h-full overflow-hidden">
      {/* Scroll indicator pill */}
      <AnimatePresence>
        {showScrollPill && (
          <motion.button 
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            onClick={scrollToBottom}
            className="absolute bottom-24 left-1/2 -translate-x-1/2 bg-[#18181B] text-white px-3.5 py-1.5 rounded-full text-xs font-semibold shadow-md z-20 hover:bg-[#27272A] transition-all active:scale-95 flex items-center space-x-1.5"
          >
            <span>New messages</span>
            <ArrowDown className="w-3.5 h-3.5" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Messages viewport */}
      <div 
        ref={listContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 space-y-5"
        onScroll={() => {
          const container = listContainerRef.current
          if (container && container.scrollHeight - container.scrollTop - container.clientHeight < 40) {
            setShowScrollPill(false)
          }
        }}
      >
        {loading ? (
          <div className="w-full space-y-4 pt-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="flex flex-col space-y-2 max-w-[65%]">
                <div className="h-3 w-20 bg-[#E4E4E0] rounded animate-pulse"></div>
                <div className="h-14 bg-white border border-[#E4E4E0] rounded-xl animate-pulse shadow-xs"></div>
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 select-none max-w-lg mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-[#F4F4F2] border border-[#E4E4E0] flex items-center justify-center text-[#18181B] mb-4 shadow-xs">
              <Bot className="w-6 h-6" />
            </div>
            <h3 className="font-display font-bold text-lg text-[#18181B]">Team Discussion</h3>
            <p className="text-[#71717A] text-xs mt-1.5 max-w-sm leading-relaxed">
              Collaborate directly with teammates or prompt specialist AI agents with deep workspace context.
            </p>
            
            {/* Quick Mention Suggestions */}
            <div className="mt-6 w-full flex flex-col gap-2">
              <div className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">
                Specialist AI Agents Ready:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {agents.map((agent) => (
                  <button
                    key={agent.key}
                    onClick={() => selectMention(agent.key)}
                    className="p-3 bg-white border border-[#E4E4E0] rounded-xl text-left hover:border-[#18181B] hover:shadow-xs transition-all group"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="w-6 h-6 rounded-lg bg-[#F4F4F2] text-[#18181B] flex items-center justify-center">
                        <agent.icon className="w-3.5 h-3.5" />
                      </span>
                      <span className="font-semibold text-xs text-[#18181B]">@{agent.key}</span>
                    </div>
                    <div className="text-[10px] text-[#71717A] mt-1.5 leading-tight">{agent.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full space-y-4">
            {messages.map((msg) => {
              const isMe = msg.sender_id === user?.id
              const isAgent = msg.sender_type === 'agent'
              const timeStr = format(new Date(msg.created_at), 'HH:mm')
              
              if (isAgent) {
                return (
                  <motion.article 
                    key={msg.id} 
                    initial={{ opacity: 0, y: 6 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    transition={{ duration: 0.15 }} 
                    className="w-full bg-white border border-[#E4E4E0] border-l-[3px] border-l-[#18181B] rounded-2xl p-5 shadow-xs space-y-3.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-6 h-6 rounded-lg bg-[#18181B] flex items-center justify-center text-white">
                          <Bot className="w-3.5 h-3.5" />
                        </div>
                        <h4 className="font-display font-bold text-xs text-[#18181B]">{msg.sender_name}</h4>
                        <span className="text-[10px] bg-[#F4F4F2] text-[#52525B] border border-[#E4E4E0] px-1.5 py-0.2 rounded font-mono font-medium">
                          Agent
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-[#71717A]">
                        {timeStr}
                      </div>
                    </div>
                    
                    <div className="chat-markdown select-text pl-1">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                        components={{
                          table: ({ node, ...props }) => (
                            <div className="chat-markdown-table-wrap">
                              <table {...props} />
                            </div>
                          ),
                          th: ({ node, ...props }) => <th className="chat-markdown-th" {...props} />,
                          td: ({ node, ...props }) => <td className="chat-markdown-td" {...props} />
                        }}
                      >
                        {cleanAgentContent(msg.content)}
                      </ReactMarkdown>
                    </div>
                    
                    {/* Citations list */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-2.5 border-t border-[#F4F4F2] select-none">
                        <button 
                          onClick={() => toggleCitations(msg.id)}
                          className="flex items-center space-x-1.5 text-xs text-[#18181B] font-semibold hover:text-[#52525B] focus:outline-none"
                        >
                          <ChevronRight className={`w-3.5 h-3.5 transition-transform duration-200 ${expandedCitations[msg.id] ? 'rotate-90' : ''}`} />
                          <span>{msg.citations.length} verified {msg.citations.length === 1 ? 'source' : 'sources'}</span>
                        </button>
                        
                        {expandedCitations[msg.id] && (
                          <div className="mt-2.5 space-y-2 pl-2">
                            {msg.citations.map((c, i) => (
                              <div key={i} className="bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl p-2.5 text-xs flex flex-col font-sans">
                                <span className="text-[#18181B] font-semibold truncate flex items-center space-x-1.5">
                                  <FileText className="w-3.5 h-3.5 shrink-0 text-[#71717A]" />
                                  <span>[{i+1}] {c.source_type === 'document' ? `${c.filename || 'Document'} (Page ${c.page || 1})` : 'Chat reference'}</span>
                                </span>
                                <span className="mt-1 line-clamp-2 leading-relaxed text-[#52525B] pl-5 text-[11px] italic">
                                  "{c.snippet || 'Snippet content available in workspace brain'}"
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </motion.article>
                )
              }

              return (
                <motion.div 
                  key={msg.id} 
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15 }}
                  className={`flex flex-col space-y-1 ${isMe ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center space-x-2 text-[11px] text-[#71717A] select-none px-1">
                    <span className="font-semibold text-[#18181B]">{msg.sender_name}</span>
                    <span>·</span>
                    <span>{timeStr}</span>
                  </div>
                  
                  <div 
                    className={`max-w-[75%] sm:max-w-[70%] rounded-2xl px-4 py-2.5 text-sm select-text leading-relaxed whitespace-pre-wrap ${
                      isMe 
                        ? 'bg-[#18181B] text-white rounded-tr-sm shadow-xs' 
                        : 'bg-white border border-[#E4E4E0] text-[#18181B] rounded-tl-sm shadow-xs'
                    }`}
                  >
                    {msg.content.split(' ').map((word, wIdx) => {
                      if (word.startsWith('@')) {
                        return (
                          <span 
                            key={wIdx} 
                            className={`font-semibold font-mono text-xs px-1.5 py-0.5 rounded mr-1 ${
                              isMe 
                                ? 'bg-white/20 text-white' 
                                : 'bg-[#F4F4F2] text-[#18181B] border border-[#E4E4E0]'
                            }`}
                          >
                            {word}
                          </span>
                        )
                      }
                      return word + ' '
                    })}
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Live typing skeleton */}
        {Object.entries(typingUsers).map(([typingUserId, typingState]) => {
          if (typingState.channel_id !== channelId) return null
          const typist = typingState.user_name
          const isAgentTypist = typist.includes('Agent')
          return (
            <div 
              key={typist}
              className="w-full flex items-center space-x-2.5 select-none"
            >
              {isAgentTypist ? (
                <div className="w-full bg-white border border-[#E4E4E0] rounded-2xl p-4 shadow-xs flex items-center space-x-3">
                  <div className="w-6 h-6 rounded-lg bg-[#18181B] flex items-center justify-center text-white animate-spin">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-[#18181B]">{typist} is reasoning...</div>
                    <div className="text-[11px] text-[#71717A]">Searching workspace memory index</div>
                  </div>
                  <div className="flex space-x-1">
                    <span className="w-1.5 h-1.5 bg-[#18181B] rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-[#18181B] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 bg-[#18181B] rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </div>
              ) : (
                <div className="bg-white border border-[#E4E4E0] rounded-2xl px-4 py-2 flex items-center space-x-2 shadow-xs">
                  <span className="text-xs text-[#52525B]">{typist} is typing</span>
                  <span className="flex space-x-1">
                    <span className="w-1.5 h-1.5 bg-[#71717A] rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-[#71717A] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 bg-[#71717A] rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  </span>
                </div>
              )}
            </div>
          )
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Input Area */}
      <div className="p-4 bg-white/95 backdrop-blur-md border-t border-[#E4E4E0] relative select-none">
        {/* Mention picker dropdown */}
        <AnimatePresence>
          {showMentionPicker && filteredAgents.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="absolute bottom-full left-4 sm:left-8 mb-3 w-72 bg-white border border-[#E4E4E0] rounded-xl shadow-lg z-30 divide-y divide-[#F4F4F2] overflow-hidden"
            >
              <div className="px-3 py-2 text-[10px] font-semibold text-[#71717A] uppercase tracking-wider bg-[#F8F8F6]">
                Mention AI Specialist
              </div>
              {filteredAgents.map((a) => (
                <button 
                  key={a.key}
                  onClick={() => selectMention(a.key)}
                  className="w-full text-left px-3.5 py-2.5 hover:bg-[#F4F4F2] flex items-center space-x-2.5 transition-colors cursor-pointer group"
                >
                  <span className="w-7 h-7 rounded-lg bg-[#F4F4F2] text-[#18181B] flex items-center justify-center shrink-0">
                    <a.icon className="w-3.5 h-3.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-bold text-[#18181B]">@{a.key}</div>
                    <div className="text-[10px] text-[#71717A] truncate leading-tight mt-0.5">{a.desc}</div>
                  </div>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="w-full">
          <form 
            onSubmit={handleSend} 
            className="flex items-center space-x-2 bg-white border border-[#E4E4E0] hover:border-[#D4D4D0] focus-within:border-[#18181B] focus-within:ring-2 focus-within:ring-[#18181B]/10 rounded-xl px-3 py-1.5 transition-all shadow-xs"
          >
            <button
              type="button"
              onClick={() => setShowMentionPicker(!showMentionPicker)}
              className="text-[#71717A] hover:text-[#18181B] p-1 rounded-lg hover:bg-[#F4F4F2] transition-colors"
              title="Mention an Agent"
            >
              <AtSign className="w-4 h-4" />
            </button>

            <input 
              type="text"
              required
              value={content}
              onChange={handleContentChange}
              onKeyDown={handleKeyDown}
              placeholder="Type a message or mention @research, @planner, @docs..."
              className="flex-grow bg-transparent text-[#18181B] text-xs sm:text-sm placeholder:text-[#A1A1AA] focus:outline-none py-1.5"
            />

            <button 
              type="submit"
              disabled={!content.trim()}
              className="w-8 h-8 rounded-lg bg-[#18181B] text-white hover:bg-[#27272A] disabled:opacity-30 disabled:hover:bg-[#18181B] flex items-center justify-center transition-all active:scale-95 shadow-xs shrink-0"
              title="Send Message"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-[#71717A] mt-1.5 px-1 font-mono">
            <span>Type @ to summon specialist agents</span>
            <span>Enter to send · Shift+Enter for newline</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Chat
