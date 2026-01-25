import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: { credential: string }) => void
          }) => void
          renderButton: (
            element: HTMLElement | null,
            config: {
              theme?: string
              size?: string
              text?: string
              width?: number
            }
          ) => void
        }
        oauth2: {
          initCodeClient: (config: {
            client_id: string
            scope: string
            ux_mode?: string
            callback: (response: { code: string; error?: string }) => void
            redirect_uri?: string
          }) => {
            requestCode: () => void
          }
        }
      }
    }
  }
}

export default function Login() {
  const { login, user, isLoading } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [googleLoaded, setGoogleLoaded] = useState(false)

  // Redirect if already logged in
  useEffect(() => {
    if (user && !isLoading) {
      navigate('/')
    }
  }, [user, isLoading, navigate])

  // Load Google Sign-In script
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => setGoogleLoaded(true)
    document.body.appendChild(script)

    return () => {
      document.body.removeChild(script)
    }
  }, [])

  // Initialize Google Sign-In button
  useEffect(() => {
    if (!googleLoaded || !window.google) return

    // Get client ID from environment or meta tag
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

    if (!clientId) {
      setError('Google Client ID not configured')
      return
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleCredentialResponse,
    })

    const buttonDiv = document.getElementById('google-signin-button')
    if (buttonDiv) {
      window.google.accounts.id.renderButton(buttonDiv, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        width: 280,
      })
    }
  }, [googleLoaded])

  const handleCredentialResponse = async (response: { credential: string }) => {
    try {
      setError(null)
      await login(response.credential)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-800 mb-2">Fourth Note</h1>
          <p className="text-gray-600">
            Your centralized brain for investment tracking
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        <div className="flex justify-center">
          {!googleLoaded ? (
            <div className="text-gray-500">Loading Google Sign-In...</div>
          ) : (
            <div id="google-signin-button"></div>
          )}
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Sign in with your Google account to access your investment data.</p>
        </div>
      </div>
    </div>
  )
}
