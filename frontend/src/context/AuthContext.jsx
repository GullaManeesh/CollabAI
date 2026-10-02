import React, { createContext, useState, useEffect, useContext } from 'react'
import client from '../api/client'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        try {
          // Fetch current user from API
          const response = await client.get('/auth/me')
          setUser(response.data)
        } catch (error) {
          console.error("Auth validation failed", error)
          logout()
        }
      }
      setLoading(false)
    }
    initAuth()
  }, [token])

  const login = async (email, password) => {
    try {
      const response = await client.post('/auth/login', { email, password })
      const { token: jwtToken, user: userData } = response.data
      
      localStorage.setItem('token', jwtToken)
      localStorage.setItem('user', JSON.stringify(userData))
      
      setToken(jwtToken)
      setUser(userData)
      return userData
    } catch (error) {
      console.error("Login failed context", error)
      throw error
    }
  }

  const register = async (name, email, password) => {
    try {
      const response = await client.post('/auth/register', { name, email, password })
      const { token: jwtToken, user: userData } = response.data
      
      localStorage.setItem('token', jwtToken)
      localStorage.setItem('user', JSON.stringify(userData))
      
      setToken(jwtToken)
      setUser(userData)
      return userData
    } catch (error) {
      console.error("Registration failed context", error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
