import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Layers, Mail, Lock, AlertCircle } from 'lucide-react'

const Login = () => {
  const { login, token } = useAuth()
  const navigate = useNavigate()
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (token) {
      navigate('/workspaces')
    }
  }, [token, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await login(email, password)
      navigate('/workspaces')
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Invalid email or password. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full overflow-y-auto flex items-center justify-center bg-[#F8F8F6] px-4 py-8 sm:p-6 font-sans select-none selection:bg-zinc-200 selection:text-zinc-900">
      <div className="w-full max-w-md bg-white border border-[#E4E4E0] rounded-2xl p-5 sm:p-8 shadow-xl">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-11 h-11 rounded-xl bg-[#18181B] flex items-center justify-center text-white mb-3 shadow-xs">
            <Layers className="w-5 h-5" />
          </div>
          <h2 className="font-display font-bold text-2xl text-[#18181B] tracking-tight">Welcome back</h2>
          <p className="text-[#71717A] text-xs mt-1">Sign in to your intelligent team workspace</p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-[#FEF2F2] border border-[#FEE2E2] text-[#991B1B] text-xs rounded-xl flex items-center space-x-2 leading-relaxed">
            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#18181B]">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full bg-[#F8F8F6] border border-[#E4E4E0] text-[#18181B] text-sm pl-10 pr-4 py-2.5 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#18181B]/10 focus:border-[#18181B] transition-all placeholder:text-[#A1A1AA]"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#18181B]">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#F8F8F6] border border-[#E4E4E0] text-[#18181B] text-sm pl-10 pr-4 py-2.5 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#18181B]/10 focus:border-[#18181B] transition-all placeholder:text-[#A1A1AA]"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full btn-primary py-2.5 text-sm mt-2"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        {/* Register link */}
        <div className="mt-6 text-center text-xs text-[#71717A]">
          New to CollabAI?{' '}
          <Link to="/register" className="text-[#18181B] font-semibold underline underline-offset-2 hover:text-[#52525B]">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Login
