import React from 'react'
import { useParams } from 'react-router-dom'
import { Wifi, WifiOff, Users, Sparkles, ChevronRight, Layers } from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext'

const TopBar = ({ wsStatus, onlineCount }) => {
  const { workspace } = useWorkspace()

  const getStatusBadge = () => {
    switch (wsStatus) {
      case 'open':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#F0FDF4] text-[#15803D] border border-[#DCFCE7] shadow-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#15803D] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#15803D]"></span>
            </span>
            <span>Realtime Live</span>
          </span>
        )
      case 'connecting':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#F4F4F5] text-[#52525B] border border-[#E4E4E7] shadow-xs animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-[#71717A]"></span>
            <span>Reconnecting...</span>
          </span>
        )
      case 'closed':
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#F4F4F5] text-[#71717A] border border-[#E4E4E7]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#A1A1AA]"></span>
            <span>Offline</span>
          </span>
        )
    }
  }

  return (
    <header className="h-14 bg-white/95 backdrop-blur-md border-b border-[#E4E4E0] flex items-center justify-between px-6 select-none text-[#18181B] shrink-0 z-10">
      {/* Brand & Workspace Path */}
      <div className="flex items-center space-x-2.5 min-w-0">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-[#18181B] flex items-center justify-center text-white shadow-xs">
            <Layers className="w-3.5 h-3.5" />
          </div>
          <span className="font-display font-bold text-sm tracking-tight text-[#18181B]">
            CollabAI
          </span>
        </div>

        <ChevronRight className="w-3.5 h-3.5 text-[#A1A1AA] shrink-0" />

        <div className="flex items-center space-x-2 min-w-0">
          <span className="text-xs font-semibold text-[#18181B] truncate max-w-[200px] sm:max-w-[280px]">
            {workspace ? workspace.name : 'Loading Workspace...'}
          </span>
          <span className="hidden sm:inline-block text-[10px] font-mono uppercase tracking-wider bg-[#F4F4F2] text-[#71717A] px-1.5 py-0.5 rounded font-medium border border-[#E4E4E0]">
            Team
          </span>
        </div>
      </div>

      {/* Status & Online Indicators */}
      <div className="flex items-center space-x-2.5 sm:space-x-3">
        {/* Presence Indicator */}
        {workspace && (
          <div className="flex items-center space-x-1.5 text-[#52525B] bg-[#F8F8F6] border border-[#E4E4E0] text-xs font-medium py-1 px-2.5 rounded-full shadow-xs">
            <Users className="w-3.5 h-3.5 text-[#71717A]" />
            <span>
              {onlineCount} {onlineCount === 1 ? 'member' : 'members'}
            </span>
          </div>
        )}

        {/* Live WS connection status */}
        {getStatusBadge()}
      </div>
    </header>
  )
}

export default TopBar
