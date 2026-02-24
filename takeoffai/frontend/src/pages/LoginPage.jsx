import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegister) {
        await register(email, password, name)
      } else {
        await login(email, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />

      {/* Left panel - branding */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden items-center justify-center"
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1e40af 100%)' }}>
        <div className="absolute inset-0 opacity-[0.06]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.4) 1px, transparent 1px)',
          backgroundSize: '32px 32px'
        }} />
        <div className="absolute top-20 right-20 w-64 h-64 rounded-full opacity-10" style={{ background: 'radial-gradient(circle, #60a5fa, transparent)' }} />
        <div className="absolute bottom-32 left-16 w-48 h-48 rounded-full opacity-10" style={{ background: 'radial-gradient(circle, #93c5fd, transparent)' }} />

        <div className="relative z-10 px-12 max-w-md">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur flex items-center justify-center border border-white/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12h4l2-4 2 8 2-4h4" />
                <rect x="14" y="6" width="8" height="12" rx="1" strokeWidth="1.5" />
              </svg>
            </div>
            <span className="text-xl font-bold text-white tracking-tight">AECAI</span>
          </div>
          <h2 className="text-3xl font-bold text-white leading-tight mb-4">
            Automated fixture counting for electrical drawings
          </h2>
          <p className="text-blue-200/70 text-sm leading-relaxed">
            Upload your PDF drawing sets. Our VLM-powered grid inspection identifies and counts every lighting fixture label — accurately and fast.
          </p>
          <div className="flex gap-6 mt-10">
            <div>
              <p className="text-2xl font-bold text-white">98%</p>
              <p className="text-xs text-blue-300/60 mt-0.5">Accuracy</p>
            </div>
            <div className="w-px bg-white/10" />
            <div>
              <p className="text-2xl font-bold text-white">5min</p>
              <p className="text-xs text-blue-300/60 mt-0.5">Per sheet</p>
            </div>
            <div className="w-px bg-white/10" />
            <div>
              <p className="text-2xl font-bold text-white">XLSX</p>
              <p className="text-xs text-blue-300/60 mt-0.5">Output</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel - form */}
      <div className="flex-1 flex items-center justify-center bg-slate-50 px-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: '#1e3a5f' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12h4l2-4 2 8 2-4h4" />
              </svg>
            </div>
            <span className="text-lg font-bold text-slate-800 tracking-tight">AECAI</span>
          </div>

          <h1 className="text-2xl font-bold text-slate-800 mb-1">
            {isRegister ? 'Create your account' : 'Welcome back'}
          </h1>
          <p className="text-slate-400 text-sm mb-8">
            {isRegister ? 'Start counting fixtures in minutes' : 'Sign in to your account'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-sm font-medium text-slate-600 mb-1.5">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-slate-800 text-sm placeholder-slate-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition"
                  placeholder="Your name"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-slate-800 text-sm placeholder-slate-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-slate-800 text-sm placeholder-slate-300 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-2.5">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full text-white rounded-xl py-2.5 text-sm font-semibold disabled:opacity-40 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/20"
              style={{ background: 'linear-gradient(135deg, #1e3a5f, #1e40af)' }}
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                  Please wait...
                </span>
              ) : isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <p className="text-center text-sm text-slate-400 mt-8">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              onClick={() => { setIsRegister(!isRegister); setError('') }}
              className="text-blue-600 font-semibold hover:text-blue-700 transition"
            >
              {isRegister ? 'Sign in' : 'Register'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
