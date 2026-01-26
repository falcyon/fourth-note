import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
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
            element: HTMLElement,
            config: { theme: string; size: string; width: number }
          ) => void
        }
      }
    }
  }
}

export default function Login() {
  const { user, isLoading, demoFailed, login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const googleButtonRef = useRef<HTMLDivElement>(null)
  const [loginError, setLoginError] = useState<string | null>(null)

  // Check if user explicitly wants to sign in with a new account
  const forceNewLogin = searchParams.get('new') === 'true'

  // Redirect if already logged in (unless forcing new login)
  useEffect(() => {
    if (user && !isLoading && !forceNewLogin) {
      navigate('/')
    }
  }, [user, isLoading, navigate, forceNewLogin])

  // Initialize Google Sign-In when demo fails OR when user explicitly wants to sign in
  useEffect(() => {
    if ((!demoFailed && !forceNewLogin) || !googleButtonRef.current) return

    const initializeGoogle = () => {
      if (!window.google) {
        // Retry after a short delay if Google hasn't loaded yet
        setTimeout(initializeGoogle, 100)
        return
      }

      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
      if (!clientId) {
        setLoginError('Google Client ID not configured')
        return
      }

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          try {
            setLoginError(null)
            await login(response.credential)
            navigate('/')
          } catch (err) {
            setLoginError(err instanceof Error ? err.message : 'Login failed')
          }
        },
      })

      window.google.accounts.id.renderButton(googleButtonRef.current!, {
        theme: 'outline',
        size: 'large',
        width: 280,
      })
    }

    initializeGoogle()
  }, [demoFailed, forceNewLogin, login, navigate])

  // Show loading while checking demo login
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a1730] to-[#0d0a15]">
        <div className="bg-white/10 backdrop-blur-sm p-8 rounded-lg shadow-lg max-w-md w-full border border-white/20">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Fourth Note</h1>
            <p className="text-gray-400">
              Your centralized brain for investment tracking
            </p>
          </div>
          <div className="flex justify-center">
            <div className="text-gray-400">Loading...</div>
          </div>
        </div>
      </div>
    )
  }

  // Show Google Sign-In when demo failed OR user explicitly wants to sign in
  if (demoFailed || forceNewLogin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a1730] to-[#0d0a15]">
        <div className="bg-white/10 backdrop-blur-sm p-8 rounded-lg shadow-lg max-w-md w-full border border-white/20">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Fourth Note</h1>
            <p className="text-gray-400">
              Your centralized brain for investment tracking
            </p>
          </div>

          <div className="text-center mb-6">
            <p className="text-gray-300 text-sm mb-4">
              {forceNewLogin ? 'Sign in with your Google account' : 'Demo account not configured. Sign in with Google to set up.'}
            </p>
          </div>

          {loginError && (
            <div className="mb-4 p-3 bg-red-500/20 text-red-300 rounded text-sm text-center">
              {loginError}
            </div>
          )}

          <div className="flex justify-center">
            <div ref={googleButtonRef}></div>
          </div>
        </div>
      </div>
    )
  }

  // Fallback (shouldn't reach here if user exists)
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a1730] to-[#0d0a15]">
      <div className="text-gray-400">Redirecting...</div>
    </div>
  )
}
