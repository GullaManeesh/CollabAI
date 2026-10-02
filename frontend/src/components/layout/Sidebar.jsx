import React from 'react'
import { NavLink, useParams, useNavigate } from 'react-router-dom'
import { MessageSquare, Bot, FileText, CheckSquare, Settings as SettingsIcon, LogOut, ChevronDown, Layers } from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext'
import { useAuth } from '../../context/AuthContext'

const Sidebar = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { workspace, workspaces, selectWorkspace } = useWorkspace()
  const { user, logout } = useAuth()

  const navItems = [
    { name: 'Team Chat', path: `/w/${id}/chat`, icon: MessageSquare },
    { name: 'Project Copilot', path: `/w/${id}/copilot`, icon: Bot, isAgent: true },
    { name: 'Documents', path: `/w/${id}/docs`, icon: FileText },
    { name: 'Tasks', path: `/w/${id}/tasks`, icon: CheckSquare },
    { name: 'Settings', path: `/w/${id}/settings`, icon: SettingsIcon },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleWorkspaceChange = (e) => {
    const nextId = e.target.value
    if (nextId) {
      selectWorkspace(nextId)
      navigate(`/w/${nextId}/chat`)
    }
  }

  return (
    <aside className="w-64 bg-white border-r border-[#E4E4E0] flex flex-col text-[#18181B] h-screen overflow-hidden select-none shrink-0 shadow-xs">
      {/* Workspace Selector Header */}
      <div className="p-4 border-b border-[#E4E4E0]">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">Workspace</div>
          <span className="text-[10px] font-mono text-[#52525B] bg-[#F4F4F2] px-1.5 py-0.5 rounded border border-[#E4E4E0]">
            Pro
          </span>
        </div>
        
        <div className="relative">
          <select 
            value={id || ''} 
            onChange={handleWorkspaceChange}
            aria-label="Select workspace"
            className="w-full appearance-none bg-[#F8F8F6] border border-[#E4E4E0] text-[#18181B] text-xs font-semibold px-3 py-2 pr-8 rounded-xl hover:border-[#D4D4D0] focus:outline-none focus:ring-2 focus:ring-[#18181B]/10 focus:border-[#18181B] transition-all cursor-pointer truncate shadow-xs"
          >
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.id}>
                {ws.name}
              </option>
            ))}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-[#71717A] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-2 pt-1 pb-1 text-[11px] font-semibold text-[#71717A] uppercase tracking-wider">
          Workspace Apps
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) => 
                `flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all group ${
                  isActive 
                    ? 'bg-[#E7F0E9] text-[#365742] border border-[#D3E3D6] shadow-xs' 
                    : 'text-[#52525B] hover:bg-[#F4F4F2] hover:text-[#18181B]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={`flex items-center justify-center w-7 h-7 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-[#D3E3D6] text-[#365742]'
                      : 'text-[#71717A] group-hover:text-[#18181B]'
                  }`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  <span className="flex-1 truncate">{item.name}</span>
                  {item.isAgent && (
                    <span className={`text-[10px] font-medium tracking-wide uppercase px-1.5 py-0.2 rounded font-mono ${
                      isActive ? 'bg-white/20 text-white' : 'bg-[#F4F4F2] text-[#52525B]'
                    }`}>
                      AI
                    </span>
                  )}
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Workspace Brain Status Card */}
      <div className="p-3">
        <div className="bg-[#F8F8F6] border border-[#E4E4E0] rounded-xl p-3 shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-[#18181B]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#15803D] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#15803D]"></span>
              </span>
              <span>Memory Index</span>
            </div>
            <span className="text-[10px] font-mono text-[#52525B] bg-white border border-[#E4E4E0] px-1.5 py-0.5 rounded shadow-xs">
              active
            </span>
          </div>
          <div className="mt-2 text-lg font-bold text-[#18181B] tracking-tight">
            {workspace?.stats?.indexed_chunks || 0}{' '}
            <span className="text-xs font-normal text-[#71717A] font-sans">chunks</span>
          </div>
          <p className="text-[11px] text-[#71717A] mt-0.5 leading-snug">
            Isolated contextual vector knowledge
          </p>
        </div>
      </div>

      {/* User Profile Footer */}
      <div className="border-t border-[#E4E4E0] p-3 bg-white">
        <div className="flex items-center justify-between p-1">
          <div className="flex items-center space-x-2.5 overflow-hidden min-w-0">
            <div 
              className="w-8 h-8 rounded-lg flex items-center justify-center font-display font-bold text-white text-xs shrink-0 shadow-xs bg-[#18181B]"
            >
              {user?.name?.substring(0, 2).toUpperCase() || 'U'}
            </div>
            <div className="truncate min-w-0">
              <div className="text-xs font-semibold text-[#18181B] truncate leading-tight">{user?.name}</div>
              <div className="text-[11px] text-[#71717A] truncate leading-tight mt-0.5">{user?.email}</div>
            </div>
          </div>
          
          <button 
            onClick={handleLogout}
            className="text-[#71717A] hover:text-[#DC2626] p-1.5 rounded-lg hover:bg-[#FEE2E2]/60 transition-colors shrink-0"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
