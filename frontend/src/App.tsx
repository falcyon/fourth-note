import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Dashboard from './pages/Dashboard'
import InvestmentDetail from './pages/InvestmentDetail'
import Settings from './pages/Settings'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import UserMenu from './components/UserMenu'

function AppContent() {
  const location = useLocation()
  const { user } = useAuth()

  const isActive = (path: string) => {
    return location.pathname === path
      ? 'bg-blue-700 text-white'
      : 'text-blue-100 hover:bg-blue-600'
  }

  // Don't show navigation on login page
  if (location.pathname === '/login') {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-blue-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-white font-bold text-xl">
                Fourth Note
              </Link>
              {user && (
                <div className="flex space-x-2">
                  <Link
                    to="/"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/')}`}
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/settings"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${isActive('/settings')}`}
                  >
                    Settings
                  </Link>
                </div>
              )}
            </div>
            {user && <UserMenu />}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4">
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
