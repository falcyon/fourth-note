import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'

interface User {
  id: string
  email: string
  name: string | null
  picture_url: string | null
  has_gmail_connected: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isDemo: boolean
  demoFailed: boolean
  login: (idToken: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE = '/api/v1'
const TOKEN_KEY = 'fourth_note_token'
const USER_KEY = 'fourth_note_user'
const DEMO_EMAIL = 'fourthnotetest@gmail.com'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(true)
  const [demoFailed, setDemoFailed] = useState(false)

  // Demo login - auto-login without Google OAuth
  const demoLogin = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/demo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setToken(data.access_token)
        setUser(data.user)
        setIsDemo(true)
        localStorage.setItem(TOKEN_KEY, data.access_token)
        localStorage.setItem(USER_KEY, JSON.stringify(data.user))
        setDemoFailed(false)
      } else {
        setDemoFailed(true)
      }
    } catch {
      setDemoFailed(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load saved auth state on mount, or auto-login as demo user
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = localStorage.getItem(USER_KEY)

    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))

      // Verify token is still valid
      verifyToken(savedToken)
    } else {
      // No saved token - auto-login as demo user
      demoLogin()
    }
  }, [demoLogin])

  const verifyToken = async (accessToken: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        setIsDemo(userData.email === DEMO_EMAIL)
        localStorage.setItem(USER_KEY, JSON.stringify(userData))
        setIsLoading(false)
      } else {
        // Token is invalid - re-login as demo user
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        await demoLogin()
      }
    } catch {
      // Error - re-login as demo user
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      await demoLogin()
    }
  }

  const login = async (idToken: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token: idToken }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }

      const data = await response.json()

      setToken(data.access_token)
      setUser(data.user)
      setIsDemo(data.user.email === DEMO_EMAIL)

      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    // In demo mode, logout just re-logins as demo user
    setToken(null)
    setUser(null)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    demoLogin()
  }

  const refreshUser = async () => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    if (savedToken) {
      await verifyToken(savedToken)
    }
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, isDemo, demoFailed, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Helper to get auth header for API calls
export function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    return { 'Authorization': `Bearer ${token}` }
  }
  return {}
}
