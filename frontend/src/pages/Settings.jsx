import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useWorkspace } from '../context/WorkspaceContext'
import { useAuth } from '../context/AuthContext'
import { Users, UserPlus, UserMinus, Shield, Mail, Calendar, Settings as SettingsIcon, CheckCircle2, AlertCircle } from 'lucide-react'
import client from '../api/client'
import { format } from 'date-fns'

const Settings = () => {
  const { id } = useParams()
  const { workspace, refreshStats } = useWorkspace()
  const { user } = useAuth()
  
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const isOwner = workspace?.owner_id === user?.id

  const handleAddMember = async (e) => {
    e.preventDefault()
    if (!email.trim() || !isOwner) return

    setSubmitting(true)
    setError(null)
    setSuccess(null)
    try {
      await client.post(`/workspaces/${id}/members`, { email: email.trim() })
      setEmail('')
      setSuccess("Teammate added successfully!")
      refreshStats()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add member. Make sure they already have an account.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemoveMember = async (targetUserId) => {
    if (!isOwner) return
    if (targetUserId === workspace.owner_id) {
      alert("Cannot remove the owner of the workspace.")
      return
    }

    const confirmDelete = window.confirm("Are you sure you want to remove this member from the workspace?")
    if (!confirmDelete) return

    try {
      await client.delete(`/workspaces/${id}/members/${targetUserId}`)
      setSuccess("Member removed successfully!")
      refreshStats()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to remove member.')
    }
  }

  return (
    <div className="absolute inset-0 flex flex-col bg-[#F8F8F6] text-[#18181B] h-full p-6 sm:p-8 overflow-y-auto select-none">
      <div className="max-w-3xl space-y-8">
        <div>
          <h2 className="font-display font-bold text-lg sm:text-xl text-[#18181B] tracking-tight">Workspace Settings</h2>
          <p className="text-[#71717A] text-xs mt-0.5">Manage team access permissions and workspace metadata.</p>
        </div>

        {/* Workspace Info */}
        <section className="bg-white border border-[#E4E4E0] rounded-2xl p-6 shadow-xs space-y-5">
          <div className="flex items-center space-x-2 border-b border-[#F4F4F2] pb-3">
            <div className="w-7 h-7 rounded-lg bg-[#F4F4F2] text-[#18181B] flex items-center justify-center">
              <SettingsIcon className="w-4 h-4" />
            </div>
            <h3 className="font-display font-bold text-sm text-[#18181B]">General Information</h3>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <div className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">Workspace Name</div>
              <div className="text-sm font-bold text-[#18181B] mt-1">{workspace?.name}</div>
            </div>

            <div>
              <div className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">Created Date</div>
              <div className="text-xs text-[#52525B] mt-1 flex items-center space-x-1.5 font-sans">
                <Calendar className="w-3.5 h-3.5 text-[#71717A]" />
                <span>{workspace ? format(new Date(workspace.created_at), 'dd MMMM yyyy') : ''}</span>
              </div>
            </div>
            
            <div className="sm:col-span-2">
              <div className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">Description</div>
              <div className="text-xs text-[#52525B] mt-1 select-text leading-relaxed">
                {workspace?.description || 'No description provided for this workspace.'}
              </div>
            </div>
          </div>
        </section>

        {/* Member Management */}
        <section className="bg-white border border-[#E4E4E0] rounded-2xl p-6 shadow-xs space-y-5">
          <div className="flex items-center space-x-2 border-b border-[#F4F4F2] pb-3">
            <div className="w-7 h-7 rounded-lg bg-[#F4F4F2] text-[#18181B] flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
            <h3 className="font-display font-bold text-sm text-[#18181B]">Team Members ({workspace?.members?.length || 0})</h3>
          </div>

          {/* Add member by email - Owner Only */}
          {isOwner ? (
            <div className="bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl p-4 space-y-3">
              <h4 className="text-xs font-semibold text-[#18181B]">Invite a Teammate</h4>
              
              {error && (
                <div className="p-2.5 bg-[#FEF2F2] border border-[#FEE2E2] text-[#991B1B] text-xs rounded-lg flex items-center space-x-1.5">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#DC2626]" />
                  <span>{error}</span>
                </div>
              )}
              {success && (
                <div className="p-2.5 bg-[#F0FDF4] border border-[#DCFCE7] text-[#15803D] text-xs rounded-lg flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-[#15803D]" />
                  <span>{success}</span>
                </div>
              )}

              <form onSubmit={handleAddMember} className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-2.5">
                <div className="relative flex-grow">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
                  <input 
                    type="email" 
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="teammate@company.com"
                    className="w-full bg-white border border-[#E4E4E0] text-[#18181B] text-xs sm:text-sm pl-9 pr-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#18181B]/10 focus:border-[#18181B] transition-all placeholder:text-[#A1A1AA]"
                  />
                </div>
                <button 
                  type="submit"
                  disabled={submitting}
                  className="btn-primary"
                >
                  <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                  <span>{submitting ? 'Adding...' : 'Add Member'}</span>
                </button>
              </form>
              <div className="text-[11px] text-[#71717A]">
                Note: Teammates must already have registered an account with this email.
              </div>
            </div>
          ) : (
            <div className="p-3.5 bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl text-xs text-[#71717A] flex items-center space-x-2">
              <Shield className="w-4 h-4 text-[#71717A] shrink-0" />
              <span>You are viewing settings as a Member. Only Workspace Owners can manage workspace members.</span>
            </div>
          )}

          {/* Members list */}
          <div className="border border-[#E4E4E0] rounded-xl overflow-hidden divide-y divide-[#F4F4F2]">
            {workspace?.members?.map((m) => {
              const memberIsOwner = m.role === 'owner'
              const isTargetMe = m.user_id === user?.id
              
              return (
                <div key={m.user_id} className="p-3.5 sm:p-4 flex items-center justify-between hover:bg-[#F8F8F6] transition-colors">
                  <div className="flex items-center space-x-3 min-w-0">
                    <div 
                      className="w-8 h-8 rounded-lg flex items-center justify-center font-display font-bold text-white text-xs shrink-0 shadow-xs bg-[#18181B]"
                    >
                      {m.name.substring(0, 2).toUpperCase()}
                    </div>
                    
                    <div className="truncate">
                      <div className="text-xs sm:text-sm font-bold text-[#18181B] leading-tight flex items-center space-x-1.5">
                        <span>{m.name}</span>
                        {isTargetMe && <span className="text-[10px] font-mono text-[#52525B] bg-[#F4F4F2] border border-[#E4E4E0] px-1.5 py-0.2 rounded font-medium">(you)</span>}
                      </div>
                      <span className="text-[11px] text-[#71717A] font-sans mt-0.5 block">
                        Joined {format(new Date(m.joined_at), 'dd MMM yyyy')}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2.5">
                    {/* Role Badge */}
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded flex items-center space-x-1 uppercase tracking-wider ${
                      memberIsOwner 
                        ? 'bg-[#18181B] text-white' 
                        : 'bg-[#F4F4F2] text-[#52525B] border border-[#E4E4E0]'
                    }`}>
                      {memberIsOwner && <Shield className="w-3 h-3 text-white mr-0.5" />}
                      <span>{m.role}</span>
                    </span>

                    {/* Remove Button - Owner Only */}
                    {isOwner && !memberIsOwner && (
                      <button 
                        onClick={() => handleRemoveMember(m.user_id)}
                        className="text-[#71717A] hover:text-[#DC2626] p-1.5 rounded-lg hover:bg-[#FEF2F2] transition-colors"
                        title="Remove member"
                      >
                        <UserMinus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}

export default Settings
