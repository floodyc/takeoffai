import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Layout({ children }) {
  const { user, logout } = useAuth()

  const navLink = ({ isActive }) =>
    `text-sm font-medium transition px-3 py-1.5 rounded-lg ${
      isActive
        ? 'text-blue-700 bg-blue-50'
        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
    }`

  return (
    <div className="min-h-screen bg-slate-50" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />

      {/* Top nav */}
      <header className="bg-white border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-8">
            {/* Logo */}
            <NavLink to="/" className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1e3a5f, #1e40af)' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M2 12h4l2-4 2 8 2-4h4" />
                </svg>
              </div>
              <span className="text-sm font-bold text-slate-800 tracking-tight">AECAI</span>
            </NavLink>

            {/* Nav links */}
            <nav className="flex items-center gap-1">
              <NavLink to="/" end className={navLink}>Dashboard</NavLink>
              <NavLink to="/new" className={navLink}>New Job</NavLink>
              <NavLink to="/billing" className={navLink}>Billing</NavLink>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">{user?.email}</span>
            <button
              onClick={logout}
              className="text-xs text-slate-400 hover:text-slate-600 transition px-2 py-1 rounded-md hover:bg-slate-100"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  )
}
