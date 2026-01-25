import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import InvestmentDetail from './pages/InvestmentDetail'
import Settings from './pages/Settings'

function App() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path
      ? 'bg-blue-700 text-white'
      : 'text-blue-100 hover:bg-blue-600'
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
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/investment/:id" element={<InvestmentDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
