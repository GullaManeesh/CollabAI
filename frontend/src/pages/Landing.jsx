import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Bot, Check, FileText, MessageSquare, Sparkles, Shield, Zap, Compass, Users, CheckCircle2, ChevronRight, Database, Terminal, ArrowRight, Layers } from 'lucide-react'
import { motion } from 'framer-motion'

const Landing = () => {
  const [activeTab, setActiveTab] = useState('chat')

  const capabilities = [
    {
      id: 'chat',
      title: 'Human-Agent Team Chat',
      desc: 'Real-time WebSocket conversations with teammates and instant @agent mentions.',
      badge: 'Live Collab'
    },
    {
      id: 'copilot',
      title: 'Critic-Verified Copilot',
      desc: 'Multi-agent orchestration loop that writes milestone roadmaps and validates sources.',
      badge: 'Multi-Agent'
    },
    {
      id: 'memory',
      title: 'Isolated Vector Brain',
      desc: 'Upload PDFs, specs, and docs. Isolated semantic chunk memory per workspace.',
      badge: 'Workspace RAG'
    }
  ]

  return (
    <main className="min-h-screen bg-[#F8F8F6] text-[#18181B] selection:bg-zinc-200 selection:text-zinc-900 font-sans antialiased">
      {/* Navigation */}
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 lg:px-8 border-b border-[#E4E4E0] bg-[#F8F8F6]/90 backdrop-blur-md sticky top-0 z-30">
        <Link to="/" className="flex items-center gap-2.5 font-display text-base font-bold tracking-tight text-[#18181B]">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#18181B] text-white shadow-xs">
            <Layers className="h-3.5 w-3.5" />
          </span>
          <span>CollabAI</span>
        </Link>

        <div className="hidden md:flex items-center space-x-6 text-xs font-medium text-[#71717A]">
          <a href="#glimpse" className="hover:text-[#18181B] transition-colors">Project Glimpse</a>
          <a href="#features" className="hover:text-[#18181B] transition-colors">Specialist Agents</a>
          <a href="#pipeline" className="hover:text-[#18181B] transition-colors">Critic Pipeline</a>
        </div>

        <div className="flex items-center gap-3 text-xs sm:text-sm font-semibold">
          <Link to="/login" className="px-3 py-2 text-[#71717A] transition-colors hover:text-[#18181B]">
            Sign In
          </Link>
          <Link to="/register" className="btn-primary">
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="mx-auto max-w-6xl px-6 pt-16 pb-14 lg:px-8 lg:pt-24 text-center flex flex-col items-center">
        <motion.div 
          initial={{ opacity: 0, y: 12 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 rounded-full border border-[#E4E4E0] bg-white px-3.5 py-1 text-xs font-medium text-[#52525B] shadow-xs mb-6"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[#15803D]" />
          Autonomous Multi-Agent Workspace
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 14 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.45, delay: 0.05 }}
          className="max-w-3xl font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#18181B] leading-[1.08]"
        >
          The minimal team workspace with a living memory.
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 14 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.45, delay: 0.1 }}
          className="mt-6 max-w-2xl text-sm sm:text-base leading-relaxed text-[#52525B]"
        >
          CollabAI organizes your people, project documents, and autonomous specialist agents into one calm, ultra-focused environment. From technical research to critic-verified milestone tasks.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 14 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.45, delay: 0.15 }}
          className="mt-8 flex flex-wrap items-center justify-center gap-3.5"
        >
          <Link to="/register" className="btn-primary text-sm px-5 py-2.5 shadow-sm">
            Launch Workspace
            <ArrowUpRight className="ml-1.5 h-4 w-4" />
          </Link>
          <a href="#glimpse" className="btn-secondary text-sm px-5 py-2.5">
            View Live Preview
          </a>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }} 
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-[#71717A]"
        >
          <span className="flex items-center gap-1.5">
            <Check className="h-3.5 w-3.5 text-[#15803D]" /> Isolated Vector Memory
          </span>
          <span className="flex items-center gap-1.5">
            <Check className="h-3.5 w-3.5 text-[#15803D]" /> Multi-Agent Critic Loop
          </span>
          <span className="flex items-center gap-1.5">
            <Check className="h-3.5 w-3.5 text-[#15803D]" /> Realtime WebSocket Sync
          </span>
        </motion.div>
      </section>

      {/* Interactive Project Glimpse Section */}
      <section id="glimpse" className="mx-auto max-w-6xl px-6 pb-20 lg:px-8">
        <div className="bg-white border border-[#E4E4E0] rounded-2xl shadow-sm overflow-hidden">
          {/* Mockup Topbar */}
          <div className="border-b border-[#E4E4E0] bg-[#FBFBFA] px-5 py-3.5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#18181B]"></span>
              <span className="text-xs font-bold text-[#18181B]">MajorProject / Sprint Launch</span>
              <span className="text-[11px] font-mono text-[#71717A] bg-[#F4F4F2] px-2 py-0.5 rounded border border-[#E4E4E0]">
                #team-chat
              </span>
            </div>

            {/* View switcher tabs */}
            <div className="flex items-center space-x-1 bg-[#F4F4F2] p-1 rounded-xl border border-[#E4E4E0]">
              {capabilities.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveTab(c.id)}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === c.id
                      ? 'bg-white text-[#18181B] shadow-xs'
                      : 'text-[#71717A] hover:text-[#18181B]'
                  }`}
                >
                  {c.badge}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Screen Preview */}
          <div className="p-6 sm:p-8 bg-[#FAFAFA]">
            {activeTab === 'chat' && (
              <div className="space-y-4 max-w-3xl mx-auto">
                {/* Teammate message */}
                <div className="flex flex-col items-start space-y-1">
                  <span className="text-[11px] font-medium text-[#71717A] px-1">Maya · Product Lead · 10:24</span>
                  <div className="bg-white border border-[#E4E4E0] rounded-2xl rounded-tl-sm px-4 py-3 text-xs sm:text-sm text-[#18181B] shadow-xs leading-relaxed max-w-[85%]">
                    Can we cross-reference the architecture document and verify if the WebSocket sync meets our concurrency goals?
                  </div>
                </div>

                {/* User message */}
                <div className="flex flex-col items-end space-y-1">
                  <span className="text-[11px] font-medium text-[#71717A] px-1">You · 10:25</span>
                  <div className="bg-[#18181B] text-white rounded-2xl rounded-tr-sm px-4 py-3 text-xs sm:text-sm shadow-xs leading-relaxed max-w-[85%]">
                    Asking <span className="font-mono bg-white/20 text-white px-1.5 py-0.5 rounded">@research</span> and <span className="font-mono bg-white/20 text-white px-1.5 py-0.5 rounded">@planner</span> to review the vector database chunks and generate milestone tasks.
                  </div>
                </div>

                {/* AI Agent Response Card with real formatted code and table */}
                <div className="bg-white border border-[#E4E4E0] rounded-2xl p-5 shadow-xs space-y-3 relative">
                  <div className="flex items-center justify-between border-b border-[#F4F4F2] pb-2.5">
                    <div className="flex items-center space-x-2">
                      <div className="w-6 h-6 rounded-lg bg-[#18181B] text-white flex items-center justify-center">
                        <Bot className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-bold text-[#18181B]">Research Agent</span>
                      <span className="text-[10px] font-mono uppercase tracking-wider bg-[#F4F4F2] text-[#52525B] px-1.5 py-0.2 rounded border border-[#E4E4E0]">
                        AI Specialist
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-[#15803D] bg-[#F0FDF4] px-2 py-0.5 rounded border border-[#DCFCE7] font-medium">
                      ✓ 3 Citations Verified
                    </span>
                  </div>

                  <div className="chat-markdown text-xs sm:text-sm">
                    <p>
                      I queried <strong>system_architecture.pdf</strong> and verified the heartbeat interval and event payload structure. Here is the validated endpoint contract:
                    </p>

                    <pre>
                      <code>{`POST /api/v1/copilot/{workspace_id}/turn
Content-Type: application/json

{
  "content": "Generate task breakdown for Sprint 1",
  "temperature": 0.2
}`}</code>
                    </pre>

                    <div className="chat-markdown-table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th className="chat-markdown-th">Component</th>
                            <th className="chat-markdown-th">Channel</th>
                            <th className="chat-markdown-th">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="chat-markdown-td font-mono font-medium">WebSocket Hub</td>
                            <td className="chat-markdown-td">/ws/{'{id}'}</td>
                            <td className="chat-markdown-td text-[#15803D] font-semibold">Active</td>
                          </tr>
                          <tr>
                            <td className="chat-markdown-td font-mono font-medium">Planner Agent</td>
                            <td className="chat-markdown-td">Milestones</td>
                            <td className="chat-markdown-td text-[#15803D] font-semibold">Ready</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'copilot' && (
              <div className="space-y-5 max-w-3xl mx-auto">
                <div className="bg-white border border-[#E4E4E0] rounded-2xl p-5 shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-[#F4F4F2] pb-3">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-[#15803D]"></span>
                      <span className="text-xs font-bold text-[#18181B]">Multi-Agent Pipeline Execution Trace</span>
                    </div>
                    <span className="text-[11px] font-mono text-[#52525B]">Latency: 1.8s · Verdict Approved</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center text-xs">
                    {[
                      { step: 'Router', agent: 'Gemini', time: '0.2s' },
                      { step: 'Research', agent: 'RAG DB', time: '0.4s' },
                      { step: 'Planner', agent: 'Milestones', time: '0.5s' },
                      { step: 'Critic', agent: 'Validator', time: '0.3s' },
                      { step: 'Docs', agent: 'Markdown', time: '0.2s' },
                      { step: 'Finalize', agent: 'Approved', time: '0.2s' },
                    ].map((item, idx) => (
                      <div key={idx} className="bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl p-2.5">
                        <div className="text-[10px] font-mono text-[#71717A] uppercase">{item.step}</div>
                        <div className="font-bold text-[#18181B] mt-0.5">{item.agent}</div>
                        <div className="text-[10px] font-mono text-[#15803D] mt-1">{item.time}</div>
                      </div>
                    ))}
                  </div>

                  <div className="bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl p-4 text-xs leading-relaxed text-[#52525B]">
                    <strong className="text-[#18181B]">Critic Agent Note:</strong> Plan was inspected for citation validity and milestone granularity. All 4 tasks were committed directly to the Workspace Kanban.
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'memory' && (
              <div className="space-y-4 max-w-3xl mx-auto">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {[
                    { name: 'architecture_spec.pdf', size: '2.4 MB', chunks: '48 chunks', date: 'Indexed 2h ago' },
                    { name: 'api_contract.md', size: '140 KB', chunks: '12 chunks', date: 'Indexed 5h ago' },
                    { name: 'meeting_notes_sep.txt', size: '42 KB', chunks: '6 chunks', date: 'Indexed yesterday' },
                  ].map((doc, idx) => (
                    <div key={idx} className="bg-white border border-[#E4E4E0] rounded-xl p-4 shadow-xs space-y-2">
                      <div className="w-8 h-8 rounded-lg bg-[#F4F4F2] text-[#18181B] flex items-center justify-center font-bold text-xs">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="text-xs font-bold text-[#18181B] truncate">{doc.name}</div>
                      <div className="flex items-center justify-between text-[11px] font-mono text-[#71717A]">
                        <span>{doc.size}</span>
                        <span className="text-[#15803D] font-medium">{doc.chunks}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 3 Pillars Section */}
      <section id="features" className="border-t border-[#E4E4E0] bg-white py-20 px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="max-w-xl mb-14">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#71717A]">Architecture</span>
            <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-[#18181B] mt-1">
              Built for high-trust human and AI collaboration.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="border border-[#E4E4E0] rounded-2xl p-6 bg-[#FBFBFA]">
              <div className="w-10 h-10 rounded-xl bg-[#18181B] text-white flex items-center justify-center mb-4">
                <Users className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-[#18181B]">Isolated Workspace Privacy</h3>
              <p className="mt-2 text-xs sm:text-sm leading-relaxed text-[#52525B]">
                Documents and vector embeddings never bleed across workspaces. Every project room retains its own context and permissions.
              </p>
            </div>

            <div className="border border-[#E4E4E0] rounded-2xl p-6 bg-[#FBFBFA]">
              <div className="w-10 h-10 rounded-xl bg-[#18181B] text-white flex items-center justify-center mb-4">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-[#18181B]">Critic Validation Loop</h3>
              <p className="mt-2 text-xs sm:text-sm leading-relaxed text-[#52525B]">
                AI answers are verified by an autonomous critic agent before they are finalized, eliminating hallucinated sources.
              </p>
            </div>

            <div className="border border-[#E4E4E0] rounded-2xl p-6 bg-[#FBFBFA]">
              <div className="w-10 h-10 rounded-xl bg-[#18181B] text-white flex items-center justify-center mb-4">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-base text-[#18181B]">Living Milestone Kanban</h3>
              <p className="mt-2 text-xs sm:text-sm leading-relaxed text-[#52525B]">
                Specialist planner agents convert chat decisions directly into milestone cards with priority levels and dates.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#E4E4E0] bg-[#F8F8F6] py-10 px-6 lg:px-8 text-xs text-[#71717A]">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <span className="font-display font-bold text-sm text-[#18181B]">CollabAI</span>
            <span>—</span>
            <span>Minimal Collaborative Team Intelligence</span>
          </div>
          <div>
            Built for focused teams and high-speed execution.
          </div>
        </div>
      </footer>
    </main>
  )
}

export default Landing
