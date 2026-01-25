import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { user, isLoading } = useAuth()
  const navigate = useNavigate()

  // Redirect if already logged in (demo auto-login should handle this)
  useEffect(() => {
    if (user && !isLoading) {
      navigate('/')
    }
  }, [user, isLoading, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-800 mb-2">Fourth Note</h1>
          <p className="text-gray-600">
            Your centralized brain for investment tracking
          </p>
        </div>

        <div className="flex justify-center">
          <div className="text-gray-500">Loading demo...</div>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Connecting to demo account...</p>
        </div>
      </div>
    </div>
  )
}
