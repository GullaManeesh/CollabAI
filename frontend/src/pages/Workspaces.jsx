import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkspace } from '../context/WorkspaceContext'
import { useAuth } from '../context/AuthContext'
import { FolderPlus, Users, Clock, Bot, Briefcase, Plus, X, Layers, LogOut, ArrowRight, Shield } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { motion, AnimatePresence } from 'framer-motion'

const Workspaces = () => {
  const { workspaces, loadingWorkspaces, createWorkspace, fetchWorkspaces } = useWorkspace()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchWorkspaces()
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return

    setCreating(true)
    setError(null)
    try {
      const newWs = await createWorkspace(name, description)
      setShowModal(false)
      setName('')
      setDescription('')
      navigate(`/w/${newWs.id}/chat`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create workspace. Try again.')
    } finally {
      setCreating(false)
    }
  }

  const handleWorkspaceClick = (id) => {
    navigate(`/w/${id}/chat`)
  }

  return (
    <div className="min-h-screen w-screen bg-[#F8F8F6] text-[#18181B] p-6 sm:p-10 font-sans overflow-y-auto selection:bg-zinc-200 selection:text-zinc-900">
      {/* Top Header */}
      <header className="max-w-6xl mx-auto flex items-center justify-between border-b border-[#E4E4E0] pb-6 mb-8 select-none">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-[#18181B] flex items-center justify-center text-white shadow-xs">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-display font-bold text-xl sm:text-2xl text-[#18181B] tracking-tight">CollabAI Workspaces</h1>
            <p className="text-[#71717A] text-xs mt-0.5">Select a workspace or create a new team environment</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center space-x-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>New Workspace</span>
          </button>
          
          <button 
            onClick={() => { logout(); navigate('/login'); }}
            className="inline-flex items-center space-x-1 text-[#71717A] hover:text-[#DC2626] hover:bg-[#FEE2E2]/50 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-colors"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Log Out</span>
          </button>
        </div>
      </header>

      {/* Main content grid */}
      <main className="max-w-6xl mx-auto">
        {loadingWorkspaces ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-44 bg-white border border-[#E4E4E0] rounded-2xl p-6 flex flex-col justify-between animate-pulse shadow-xs">
                <div>
                  <div className="h-5 w-36 bg-[#E4E4E0] rounded-md mb-3"></div>
                  <div className="h-3 w-48 bg-[#F4F4F2] rounded-md"></div>
                </div>
                <div className="flex space-x-4 border-t border-[#F4F4F2] pt-4">
                  <div className="h-3 w-16 bg-[#F4F4F2] rounded"></div>
                  <div className="h-3 w-24 bg-[#F4F4F2] rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : workspaces.length === 0 ? (
          <div className="bg-white border border-[#E4E4E0] rounded-2xl p-12 text-center max-w-xl mx-auto mt-12 flex flex-col items-center shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-[#F4F4F2] flex items-center justify-center text-[#71717A] mb-4">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="font-display font-bold text-lg text-[#18181B]">No workspaces found</h3>
            <p className="text-[#71717A] text-xs max-w-sm mt-1.5 mb-6 leading-relaxed">
              Create your first team workspace to start organizing documents, tracking tasks, and collaborating with context-aware AI agents.
            </p>
            <button 
              onClick={() => setShowModal(true)}
              className="btn-primary"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              <span>Create First Workspace</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {workspaces.map((ws) => (
              <motion.div 
                key={ws.id} 
                whileHover={{ y: -2 }}
                onClick={() => handleWorkspaceClick(ws.id)}
                className="bg-white border border-[#E4E4E0] rounded-2xl p-6 flex flex-col justify-between hover:border-[#18181B] hover:shadow-md cursor-pointer transition-all group duration-150"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="w-8 h-8 rounded-lg bg-[#F4F4F2] text-[#18181B] flex items-center justify-center font-bold text-xs">
                      {ws.name.substring(0, 2).toUpperCase()}
                    </span>
                    <span className="text-[11px] font-mono text-[#71717A] group-hover:text-[#18181B] flex items-center space-x-0.5">
                      <span>Open</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </span>
                  </div>

                  <h3 className="font-display font-bold text-base text-[#18181B] group-hover:text-[#18181B] transition-colors truncate">
                    {ws.name}
                  </h3>
                  <div className="mt-1 text-[#71717A] text-xs line-clamp-2 h-8 leading-relaxed">
                    Collaborative human-agent workspace
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-[#F4F4F2] text-xs text-[#71717A]">
                  <div className="flex items-center space-x-1.5 bg-[#F8F8F6] px-2 py-0.5 rounded-md border border-[#E4E4E0]">
                    <Users className="w-3.5 h-3.5 text-[#71717A]" />
                    <span>{ws.member_count} {ws.member_count === 1 ? 'member' : 'members'}</span>
                  </div>
                  
                  <div className="flex items-center space-x-1 text-[#A1A1AA] text-[11px]">
                    <Clock className="w-3 h-3" />
                    <span>
                      {formatDistanceToNow(new Date(ws.last_activity_at), { addSuffix: true })}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>

      {/* Creation Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 bg-[#18181B]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              className="w-full max-w-lg bg-white border border-[#E4E4E0] rounded-2xl p-6 sm:p-7 shadow-2xl relative"
            >
              <button 
                onClick={() => setShowModal(false)}
                className="absolute right-5 top-5 text-[#71717A] hover:text-[#18181B] p-1 rounded-lg hover:bg-[#F4F4F2] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <h3 className="font-display font-bold text-xl text-[#18181B] tracking-tight mb-1">Create New Workspace</h3>
              <p className="text-[#71717A] text-xs mb-6 leading-relaxed">Set up an isolated project room with dedicated documents, tasks, and memory.</p>

              {error && (
                <div className="mb-4 p-3 bg-[#FEF2F2] border border-[#FEE2E2] text-[#991B1B] text-xs rounded-xl">
                  {error}
                </div>
              )}

              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#18181B]">Workspace Name</label>
                  <input 
                    type="text" 
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Major Project - Team 7"
                    className="w-full bg-[#F8F8F6] border border-[#E4E4E0] text-[#18181B] text-sm px-3.5 py-2.5 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#18181B]/10 focus:border-[#18181B] transition-all placeholder:text-[#A1A1AA]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#18181B]">Description (Optional)</label>
                  <textarea 
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Briefly describe what this workspace is for..."
                    rows="3"
                    className="w-full bg-[#F8F8F6] border border-[#E4E4E0] text-[#18181B] text-sm px-3.5 py-2.5 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#18181B]/10 focus:border-[#18181B] transition-all placeholder:text-[#A1A1AA] resize-none"
                  />
                </div>

                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#F4F4F2]">
                  <button 
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    disabled={creating}
                    className="btn-primary"
                  >
                    {creating ? (
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    ) : (
                      <span>Create Workspace</span>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Workspaces
