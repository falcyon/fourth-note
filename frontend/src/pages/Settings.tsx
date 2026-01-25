import { useState, useEffect, useCallback } from 'react'
import { api, SystemStatus, SchedulerStatus, DatabaseStats } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { user, refreshUser } = useAuth()
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  const [stats, setStats] = useState<DatabaseStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [gmailConnecting, setGmailConnecting] = useState(false)
  const [gmailError, setGmailError] = useState<string | null>(null)
  const [googleLoaded, setGoogleLoaded] = useState(false)

  // Load Google Identity Services script
  useEffect(() => {
    // Check if already loaded
    if (window.google?.accounts?.oauth2) {
      setGoogleLoaded(true)
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => setGoogleLoaded(true)
    document.body.appendChild(script)
  }, [])

  const handleConnectGmail = useCallback(() => {
    if (!googleLoaded || !window.google) {
      setGmailError('Google Sign-In not loaded')
      return
    }

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    if (!clientId) {
      setGmailError('Google Client ID not configured')
      return
    }

    setGmailConnecting(true)
    setGmailError(null)

    const codeClient = window.google.accounts.oauth2.initCodeClient({
      client_id: clientId,
      scope: 'https://www.googleapis.com/auth/gmail.readonly',
      ux_mode: 'popup',
      callback: async (response) => {
        if (response.error) {
          setGmailError(response.error)
          setGmailConnecting(false)
          return
        }

        try {
          // Exchange the code for tokens
          await api.exchangeGmailCode(response.code, window.location.origin)
          // Refresh user to update has_gmail_connected
          await refreshUser()
          setGmailError(null)
        } catch (err) {
          setGmailError(err instanceof Error ? err.message : 'Failed to connect Gmail')
        } finally {
          setGmailConnecting(false)
        }
      },
    })

    codeClient.requestCode()
  }, [googleLoaded, refreshUser])

  const handleDisconnectGmail = async () => {
    try {
      setGmailConnecting(true)
      setGmailError(null)
      await api.disconnectGmail()
      await refreshUser()
    } catch (err) {
      setGmailError(err instanceof Error ? err.message : 'Failed to disconnect Gmail')
    } finally {
      setGmailConnecting(false)
    }
  }

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true)
        const [system, scheduler, dbStats] = await Promise.all([
          api.getSystemStatus(),
          api.getSchedulerStatus(),
          api.getStats(),
        ])
        setSystemStatus(system)
        setSchedulerStatus(scheduler)
        setStats(dbStats)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load status')
      } finally {
        setLoading(false)
      }
    }

    fetchAll()
    // Refresh every 30 seconds
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* System Status */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">System Status</h2>
          {systemStatus && (
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-gray-500">Overall</dt>
                <dd>
                  <StatusBadge
                    status={systemStatus.status === 'healthy' ? 'success' : 'warning'}
                    text={systemStatus.status}
                  />
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Database</dt>
                <dd>
                  <StatusBadge
                    status={systemStatus.database === 'connected' ? 'success' : 'error'}
                    text={systemStatus.database}
                  />
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Gmail</dt>
                <dd>
                  <StatusBadge
                    status={systemStatus.gmail === 'connected' ? 'success' : 'error'}
                    text={systemStatus.gmail}
                  />
                </dd>
              </div>
            </dl>
          )}
        </div>

        {/* Gmail OAuth - Per-user connection */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Your Gmail Connection</h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-gray-500">Status</dt>
              <dd>
                <StatusBadge
                  status={user?.has_gmail_connected ? 'success' : 'warning'}
                  text={user?.has_gmail_connected ? 'Connected' : 'Not Connected'}
                />
              </dd>
            </div>
            {user?.has_gmail_connected ? (
              <div className="pt-2">
                <p className="text-sm text-gray-600 mb-3">
                  Your Gmail account is connected. Emails will be fetched from your inbox.
                </p>
                <button
                  onClick={handleDisconnectGmail}
                  disabled={gmailConnecting}
                  className="inline-flex items-center px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 transition-colors disabled:opacity-50"
                >
                  {gmailConnecting ? 'Disconnecting...' : 'Disconnect Gmail'}
                </button>
              </div>
            ) : (
              <div className="pt-2">
                <p className="text-sm text-gray-600 mb-3">
                  Connect your Gmail account to fetch investment emails and PDFs.
                </p>
                <button
                  onClick={handleConnectGmail}
                  disabled={gmailConnecting || !googleLoaded}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  {gmailConnecting ? 'Connecting...' : 'Connect Gmail'}
                </button>
              </div>
            )}
            {gmailError && (
              <div className="pt-2">
                <p className="text-sm text-red-600">{gmailError}</p>
              </div>
            )}
          </dl>
        </div>

        {/* Scheduler */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Scheduler</h2>
          {schedulerStatus && (
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd>
                  <StatusBadge
                    status={schedulerStatus.running ? 'success' : 'error'}
                    text={schedulerStatus.running ? 'Running' : 'Stopped'}
                  />
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Interval</dt>
                <dd className="text-gray-900">Every {schedulerStatus.interval_hours} hours</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Next Run</dt>
                <dd className="text-gray-900">
                  {schedulerStatus.next_run
                    ? new Date(schedulerStatus.next_run).toLocaleString()
                    : '-'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Last Run</dt>
                <dd className="text-gray-900">
                  {schedulerStatus.last_run
                    ? new Date(schedulerStatus.last_run).toLocaleString()
                    : 'Never'}
                </dd>
              </div>
            </dl>
          )}
        </div>

        {/* Database Stats */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Database Statistics</h2>
          {stats && (
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-gray-500">Total Emails</dt>
                <dd className="text-gray-900 font-medium">{stats.total_emails}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Total Documents</dt>
                <dd className="text-gray-900 font-medium">{stats.total_documents}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Total Investments</dt>
                <dd className="text-gray-900 font-medium">{stats.total_investments}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Pending Documents</dt>
                <dd className="text-gray-900 font-medium">{stats.pending_documents}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Failed Documents</dt>
                <dd className="text-gray-900 font-medium">{stats.failed_documents}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>

      {/* Export Section */}
      <div className="mt-6 bg-white shadow-md rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Data Export</h2>
        <p className="text-gray-600 mb-4">
          Download all extracted investment data as a CSV file for use in spreadsheets.
        </p>
        <button
          onClick={() => api.exportCsv()}
          className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export to CSV
        </button>
      </div>
    </div>
  )
}
