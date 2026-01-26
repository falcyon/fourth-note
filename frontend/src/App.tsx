import { useState, useRef, useEffect } from 'react'
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Dashboard from './pages/Dashboard'
import InvestmentDetail from './pages/InvestmentDetail'
import Settings from './pages/Settings'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'

function UserDropdown() {
  const { user, isDemo, logout } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!user) return null

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
      >
        {user.picture_url ? (
          <img
            src={user.picture_url}
            alt={user.name || user.email}
            className="w-9 h-9 rounded-full border-2 border-white/30"
          />
        ) : (
          <div className="w-9 h-9 rounded-full bg-accent/80 flex items-center justify-center text-white border-2 border-white/30">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        )}
        <svg className={`w-4 h-4 text-white/70 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl py-1 z-50">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-900">{user.name || 'User'}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
            {isDemo && (
              <span className="inline-block mt-1 text-xs bg-accent/10 text-accent px-2 py-0.5 rounded">Demo</span>
            )}
          </div>
          <button
            onClick={() => {
              setIsOpen(false)
              navigate('/settings')
            }}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
          >
            <svg className="w-4 h-4 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Settings
          </button>
          {!isDemo && (
            <button
              onClick={() => {
                setIsOpen(false)
                logout()
              }}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center border-t border-gray-100"
            >
              <svg className="w-4 h-4 mr-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign out
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function AppContent() {
  const location = useLocation()
  const { user } = useAuth()

  // Don't show navigation on login page
  if (location.pathname === '/login') {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a1730] to-[#0d0a15]">
      {/* Minimal Top Bar */}
      <header className="fixed top-0 left-0 right-0 z-40 px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo - extreme left */}
          <Link to="/" className="text-white font-semibold text-xl hover:text-accent-300 transition-colors">
            Fourth Note
          </Link>

          {/* User Dropdown - extreme right */}
          {user && <UserDropdown />}
        </div>
      </header>

      {/* Spacer for fixed header */}
      <div className="h-16"></div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto pb-6 px-4">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/investment/:id"
            element={
              <ProtectedRoute>
                <InvestmentDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
