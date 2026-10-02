import React, { createContext, useState, useEffect, useContext } from 'react'
import client from '../api/client'
import { useAuth } from './AuthContext'

const WorkspaceContext = createContext(null)

export const WorkspaceProvider = ({ children }) => {
  const { token } = useAuth()
  const [workspaces, setWorkspaces] = useState([])
  const [workspace, setWorkspace] = useState(null)
  const [activeWorkspaceId, setActiveWorkspaceId] = useState(null)
  const [loadingWorkspaces, setLoadingWorkspaces] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Fetch workspaces list
  const fetchWorkspaces = async () => {
    if (!token) return
    setLoadingWorkspaces(true)
    try {
      const response = await client.get('/workspaces')
      setWorkspaces(response.data)
    } catch (error) {
      console.error("Failed to load workspaces list", error)
    } finally {
      setLoadingWorkspaces(false)
    }
  }

  // Fetch detailed workspace information
  const fetchWorkspaceDetail = async (id) => {
    if (!id || !token) return
    setLoadingDetail(true)
    try {
      const response = await client.get(`/workspaces/${id}`)
      setWorkspace(response.data)
    } catch (error) {
      console.error(`Failed to load workspace details for ${id}`, error)
      setWorkspace(null)
    } finally {
      setLoadingDetail(false)
    }
  }

  useEffect(() => {
    if (token) {
      fetchWorkspaces()
    } else {
      setWorkspaces([])
      setWorkspace(null)
      setActiveWorkspaceId(null)
    }
  }, [token])

  useEffect(() => {
    if (activeWorkspaceId) {
      fetchWorkspaceDetail(activeWorkspaceId)
    } else {
      setWorkspace(null)
    }
  }, [activeWorkspaceId])

  const selectWorkspace = (id) => {
    setActiveWorkspaceId(id)
  }

  const createWorkspace = async (name, description) => {
    try {
      const response = await client.post('/workspaces', { name, description })
      const newWs = response.data
      await fetchWorkspaces()
      return newWs
    } catch (error) {
      console.error("Failed to create workspace", error)
      throw error
    }
  }

  const refreshStats = async () => {
    if (activeWorkspaceId) {
      await fetchWorkspaceDetail(activeWorkspaceId)
    }
  }

  return (
    <WorkspaceContext.Provider value={{
      workspaces,
      workspace,
      activeWorkspaceId,
      loadingWorkspaces,
      loadingDetail,
      selectWorkspace,
      createWorkspace,
      fetchWorkspaces,
      refreshStats
    }}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext)
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider')
  }
  return context
}
