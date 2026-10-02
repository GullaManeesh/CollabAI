import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useOutletContext } from 'react-router-dom'
import { Sparkles, Bot, Send, Brain, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, Circle, Clock, CheckSquare, ArrowRight, Zap, ListChecks, Compass, Terminal } from 'lucide-react'
import client from '../api/client'
import { useWorkspace } from '../context/WorkspaceContext'
import { useAuth } from '../context/AuthContext'
import { useCopilotRun } from '../hooks/useCopilotRun'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { motion, AnimatePresence } from 'framer-motion'

const Copilot = () => {
  const { id } = useParams()
  const { workspace, refreshStats } = useWorkspace()
  const { user } = useAuth()
  
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState('')
  const [loadingHistory, setLoadingHistory] = useState(true)
  
  const [activeRunId, setActiveRunId] = useState(null)
  const [runFailedMessage, setRunFailedMessage] = useState(null)

  const messagesEndRef = useRef(null)

  const fetchCopilotHistory = useCallback(async () => {
    setLoadingHistory(true)
    try {
      const response = await client.get(`/copilot/${id}/history`)
      setMessages(response.data)
      setTimeout(scrollToBottom, 50)
    } catch (err) {
      console.error("Failed to load copilot history", err)
    } finally {
      setLoadingHistory(false)
    }
  }, [id])

  useEffect(() => {
    fetchCopilotHistory()
  }, [fetchCopilotHistory])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const { lastWsMessage, setLastWsMessage } = useOutletContext()
  const channelId = workspace?.channels?.copilot

  useEffect(() => {
    if (lastWsMessage && lastWsMessage.channel_id === channelId) {
      setMessages((prev) => {
        if (prev.some((m) => m.id === lastWsMessage.id)) return prev
        return [...prev, lastWsMessage]
      })
      setLastWsMessage(null)
      setTimeout(scrollToBottom, 50)
      refreshStats()
    }
  }, [lastWsMessage, channelId, refreshStats, setLastWsMessage])

  const handleRunCompleted = (completedRun) => {
    setActiveRunId(null)
    setQuery('')
    fetchCopilotHistory()
  }

  const handleRunFailed = (errMsg) => {
    setActiveRunId(null)
    setRunFailedMessage(errMsg)
  }

  const { run, error: pollError } = useCopilotRun(activeRunId, handleRunCompleted, handleRunFailed)

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!query.trim()) return

    setRunFailedMessage(null)
    const turnQuery = query

    try {
      const response = await client.post(`/copilot/${id}/turn`, { content: turnQuery })
      const { run_id } = response.data
      
      setQuery('')
      setMessages((prev) => [
        ...prev,
        {
          id: `temp-${Date.now()}`,
          sender_type: 'user',
          sender_name: user?.name || 'You',
          content: turnQuery,
          created_at: new Date().toISOString()
        }
      ])
      setTimeout(scrollToBottom, 30)
      
      setActiveRunId(run_id)
    } catch (err) {
      console.error("Failed to start copilot run", err)
      setRunFailedMessage(err.response?.data?.detail || 'Failed to initialize Copilot turn.')
    }
  }

  const handlePromptSuggestion = (promptText) => {
    setQuery(promptText)
  }

  const stepsList = ['router', 'research', 'planner', 'critic', 'docs', 'finalize']
  const getStepStatus = (stepName) => {
    if (!run) return 'pending'
    const trace = run.trace || []
    
    const stepInTrace = trace.find((s) => s.agent === stepName)
    if (stepInTrace) {
      return { status: 'done', latency: stepInTrace.latency_ms }
    }
    
    if (run.current_step === stepName) {
      return { status: 'running' }
    }
    
    return { status: 'pending' }
  }

  return (
    <div className="absolute inset-0 flex flex-col bg-[#F8F8F6] text-[#18181B] h-full overflow-hidden">
      {/* Messages Viewport */}
      <div className="flex-grow overflow-y-auto px-4 py-6 sm:px-8 space-y-6">
        {loadingHistory ? (
          <div className="max-w-3xl mx-auto space-y-4 pt-4">
            {[1, 2].map((n) => (
              <div key={n} className="flex flex-col space-y-2 max-w-[70%]">
                <div className="h-3 w-24 bg-[#E4E4E0] rounded animate-pulse"></div>
                <div className="h-20 bg-white border border-[#E4E4E0] rounded-xl animate-pulse shadow-xs"></div>
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 select-none max-w-lg mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-[#F4F4F2] border border-[#E4E4E0] flex items-center justify-center text-[#18181B] mb-4 shadow-xs">
              <Brain className="w-6 h-6" />
            </div>
            <h3 className="font-display font-bold text-lg text-[#18181B]">Project Copilot</h3>
            <p className="text-[#71717A] text-xs mt-1.5 max-w-sm leading-relaxed">
              Autonomous multi-agent orchestration. Ask complex questions, request sprint breakdowns, or let agents synthesize living documentation.
            </p>

            {/* Quick Prompts */}
            <div className="mt-6 w-full flex flex-col gap-2">
              <div className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">
                Suggested Prompts
              </div>
              <div className="flex flex-col gap-2">
                {[
                  "Draft a technical milestone plan for our upcoming release",
                  "Synthesize key insights and action items from indexed documents",
                  "Break down high-priority tasks and assign recommended owners"
                ].map((promptText, i) => (
                  <button
                    key={i}
                    onClick={() => handlePromptSuggestion(promptText)}
                    className="p-3 bg-white border border-[#E4E4E0] rounded-xl text-left hover:border-[#18181B] hover:shadow-xs transition-all flex items-center justify-between group"
                  >
                    <span className="text-xs text-[#27272A] font-medium group-hover:text-[#18181B] truncate">
                      {promptText}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#71717A] group-hover:text-[#18181B] group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map((msg) => {
              const isMe = msg.sender_type === 'user'
              if (isMe) {
                return (
                  <motion.div 
                    key={msg.id} 
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.15 }}
                    className="flex flex-col items-end space-y-1"
                  >
                    <span className="text-[11px] text-[#71717A] font-mono select-none px-1">{msg.sender_name}</span>
                    <div className="bg-[#18181B] text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-[75%] sm:max-w-[70%] leading-relaxed whitespace-pre-wrap select-text shadow-xs">
                      {msg.content}
                    </div>
                  </motion.div>
                )
              } else {
                return (
                  <CopilotAnswerCard key={msg.id} message={msg} />
                )
              }
            })}
          </div>
        )}

        {/* Polling live pipeline strip */}
        {activeRunId && run && (
          <motion.div 
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-3xl mx-auto bg-white border border-[#E4E4E0] rounded-2xl p-5 shadow-xs space-y-4"
          >
            <div className="flex items-center justify-between border-b border-[#F4F4F2] pb-2.5 select-none">
              <span className="text-xs font-semibold text-[#18181B] flex items-center space-x-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#18181B] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#18181B]"></span>
                </span>
                <span>Multi-Agent Orchestration Pipeline</span>
              </span>
              <span className="text-xs font-semibold text-[#18181B] bg-[#F4F4F2] border border-[#E4E4E0] px-2 py-0.5 rounded-full flex items-center space-x-1">
                <span>Running step: {run.current_step || 'router'}</span>
              </span>
            </div>
            
            {/* Live Pipeline Strip */}
            <div className="flex items-center justify-between py-2 select-none overflow-x-auto">
              {stepsList.map((step, index) => {
                const stepMeta = getStepStatus(step)
                const isDone = stepMeta.status === 'done'
                const isRunning = stepMeta.status === 'running'
                
                return (
                  <React.Fragment key={step}>
                    <div className="flex flex-col items-center space-y-1 shrink-0 min-w-[56px]">
                      <div className="flex items-center justify-center">
                        {isDone ? (
                          <div className="w-6 h-6 rounded-full bg-[#F0FDF4] border border-[#DCFCE7] flex items-center justify-center">
                            <CheckCircle2 className="w-4 h-4 text-[#15803D]" />
                          </div>
                        ) : isRunning ? (
                          <div className="w-6 h-6 rounded-full bg-[#F4F4F2] border border-[#E4E4E0] flex items-center justify-center">
                            <span className="w-3.5 h-3.5 rounded-full border-2 border-[#18181B] border-t-transparent animate-spin"></span>
                          </div>
                        ) : (
                          <div className="w-6 h-6 rounded-full bg-[#F8F8F6] border border-[#E4E4E0] flex items-center justify-center">
                            <Circle className="w-3 h-3 text-[#A1A1AA]" />
                          </div>
                        )}
                      </div>
                      <span className={`text-[11px] font-semibold capitalize ${isRunning ? 'text-[#18181B]' : isDone ? 'text-[#15803D]' : 'text-[#71717A]'}`}>
                        {step}
                      </span>
                      {isDone && stepMeta.latency && (
                        <span className="text-[9px] font-mono text-[#71717A]">{(stepMeta.latency/1000).toFixed(1)}s</span>
                      )}
                    </div>
                    {index < stepsList.length - 1 && (
                      <div className={`flex-1 h-0.5 mx-1.5 transition-colors ${isDone ? 'bg-[#15803D]' : isRunning ? 'bg-[#18181B]' : 'bg-[#E4E4E0]'}`}></div>
                    )}
                  </React.Fragment>
                )
              })}
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Failures displays */}
      {(runFailedMessage || pollError) && (
        <div className="max-w-3xl mx-auto w-full px-4 mb-2">
          <div className="p-3 bg-[#FEF2F2] border border-[#FEE2E2] text-[#991B1B] text-xs rounded-xl flex items-center space-x-2 shadow-xs">
            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
            <span>{runFailedMessage || pollError}</span>
          </div>
        </div>
      )}

      {/* Composer Input Area */}
      <div className="p-4 bg-white/95 backdrop-blur-md border-t border-[#E4E4E0] select-none">
        <div className="max-w-3xl mx-auto">
          <form 
            onSubmit={handleSubmit} 
            className="flex items-center space-x-2 bg-white border border-[#E4E4E0] hover:border-[#D4D4D0] focus-within:border-[#18181B] focus-within:ring-2 focus-within:ring-[#18181B]/10 rounded-xl px-3 py-1.5 transition-all shadow-xs"
          >
            <input 
              type="text"
              required
              value={query}
              disabled={!!activeRunId}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={activeRunId ? "Copilot agents orchestrating answer..." : "Ask Copilot for planning, roadmap breakdown, or knowledge query..."}
              className="flex-grow bg-transparent text-[#18181B] text-xs sm:text-sm focus:outline-none placeholder:text-[#A1A1AA] py-1.5 disabled:opacity-50"
            />
            <button 
              type="submit"
              disabled={!!activeRunId || !query.trim()}
              className="w-8 h-8 rounded-lg bg-[#18181B] text-white hover:bg-[#27272A] disabled:opacity-30 disabled:hover:bg-[#18181B] flex items-center justify-center transition-all active:scale-95 shadow-xs shrink-0"
              title="Execute Copilot Run"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-[#71717A] mt-1.5 px-1 font-mono">
            <span>Verified by multi-agent critic loop</span>
            <span>Structured output with citation trace</span>
          </div>
        </div>
      </div>
    </div>
  )
}

const CopilotAnswerCard = ({ message }) => {
  const [expandedTrace, setExpandedTrace] = useState(false)
  const [runDetails, setRunDetails] = useState(null)
  
  const handleTraceToggle = async () => {
    if (!expandedTrace && !runDetails && message.run_id) {
      try {
        const response = await client.get(`/copilot/runs/${message.run_id}`)
        setRunDetails(response.data)
      } catch (err) {
        console.error("Failed to load run trace details", err)
      }
    }
    setExpandedTrace(!expandedTrace)
  }

  const tokensCount = runDetails?.total_tokens || 0
  const latency = runDetails?.total_latency_ms ? (runDetails.total_latency_ms / 1000).toFixed(1) : 0
  const revisionCount = runDetails?.revision_count || 0

  return (
    <motion.div 
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className="w-full bg-white border border-[#E4E4E0] border-l-[3px] border-l-[#18181B] rounded-2xl p-5 shadow-xs space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#F4F4F2] pb-3 select-none">
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-lg bg-[#18181B] flex items-center justify-center text-white">
            <Brain className="w-3.5 h-3.5" />
          </div>
          <h4 className="font-display font-bold text-xs text-[#18181B]">Project Copilot Synthesis</h4>
          <span className="text-[10px] bg-[#F4F4F2] text-[#52525B] border border-[#E4E4E0] px-2 py-0.2 rounded font-mono font-medium">
            Orchestrated Plan
          </span>
        </div>
        <div className="text-[10px] font-mono text-[#15803D] bg-[#F0FDF4] border border-[#DCFCE7] px-2 py-0.5 rounded font-medium">
          Critic Approved
        </div>
      </div>

      {/* Answer Body with complete Markdown components for tables and code blocks */}
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
          {message.content}
        </ReactMarkdown>
      </div>

      {/* Trace Toggler */}
      {message.run_id && (
        <div className="pt-3 border-t border-[#F4F4F2] select-none">
          <div className="flex items-center justify-between">
            <button 
              onClick={handleTraceToggle}
              className="flex items-center space-x-1.5 text-xs text-[#18181B] font-semibold hover:text-[#52525B] focus:outline-none cursor-pointer"
            >
              {expandedTrace ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              <span>Agent Execution Telemetry</span>
            </button>
            
            {revisionCount >= 1 && (
              <span className="text-[10px] text-[#71717A] bg-[#F4F4F2] border border-[#E4E4E0] px-2 py-0.5 rounded font-medium">
                Refined once by Critic Agent
              </span>
            )}
          </div>

          {/* Trace details accordion list */}
          {expandedTrace && (
            <div className="mt-3 space-y-2.5 pl-3 border-l-2 border-[#E4E4E0]">
              {!runDetails ? (
                <div className="text-xs font-mono text-[#71717A] animate-pulse">Loading telemetry trace...</div>
              ) : (
                runDetails.trace.map((step, idx) => (
                  <div key={idx} className="space-y-1 font-mono text-xs text-[#52525B] bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl p-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[#18181B] font-bold">Step {step.step}: {step.agent.toUpperCase()}</span>
                      {step.provider && (
                        <span className="text-[10px] bg-white border border-[#E4E4E0] px-1.5 py-0.5 rounded text-[#71717A]">
                          {step.provider} · {step.model} · {(step.latency_ms/1000).toFixed(1)}s
                        </span>
                      )}
                    </div>
                    {step.output_summary && (
                      <pre className="bg-[#18181B] text-[#F4F4F5] p-2.5 rounded-lg border border-[#27272A] overflow-x-auto text-[10px] max-h-32 font-mono leading-relaxed select-text mt-1.5">
                        {step.output_summary}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Telemetry info strip */}
      {runDetails && (
        <div className="flex items-center justify-between text-[11px] text-[#71717A] select-none bg-[#F8F8F6] border border-[#E4E4E0] px-3 py-1.5 rounded-lg font-sans">
          <div className="flex items-center space-x-3">
            <span>Latency: <strong className="text-[#18181B]">{latency}s</strong></span>
            <span>Tokens: <strong className="text-[#18181B]">{tokensCount}</strong></span>
          </div>
          <Link to={`/w/${message.workspace_id}/tasks`} className="text-[#18181B] hover:text-[#52525B] font-semibold flex items-center space-x-1">
            <CheckSquare className="w-3.5 h-3.5 inline" />
            <span>View Tasks Board →</span>
          </Link>
        </div>
      )}
    </motion.div>
  )
}

export default Copilot
