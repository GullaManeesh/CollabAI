import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { WorkspaceProvider } from './context/WorkspaceContext'
import WorkspaceLayout from './components/layout/WorkspaceLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Workspaces from './pages/Workspaces'
import Chat from './pages/Chat'
import Copilot from './pages/Copilot'
import Documents from './pages/Documents'
import Tasks from './pages/Tasks'
import Settings from './pages/Settings'
import Landing from './pages/Landing'

// Protected Route wrapper component
const ProtectedRoute = ({ children }) => {
  const { token, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="h-screen w-screen bg-slate-50 flex items-center justify-center flex-col space-y-3">
        <div className="w-9 h-9 border-3 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
        <div className="text-slate-500 text-xs font-medium tracking-wide">Verifying session...</div>
      </div>
    )
  }
  
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

const WorkspaceRedirect = () => {
  return <Navigate to="chat" replace />
}

function App() {
  return (
    <AuthProvider>
      <WorkspaceProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Root Workspace Selection */}
            <Route 
              path="/workspaces" 
              element={
                <ProtectedRoute>
                  <Workspaces />
                </ProtectedRoute>
              } 
            />

            {/* Workspace-scoped routes in Layout */}
            <Route
              path="/w/:id"
              element={
                <ProtectedRoute>
                  <WorkspaceLayout />
                </ProtectedRoute>
              }
            >
              {/* Redirect /w/:id to /w/:id/chat */}
              <Route index element={<WorkspaceRedirect />} />
              <Route path="chat" element={<Chat />} />
              <Route path="copilot" element={<Copilot />} />
              <Route path="docs" element={<Documents />} />
              <Route path="tasks" element={<Tasks />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Default fallback redirects */}
            <Route path="*" element={<Navigate to="/workspaces" replace />} />
          </Routes>
        </BrowserRouter>
      </WorkspaceProvider>
    </AuthProvider>
  )
}

export default App
