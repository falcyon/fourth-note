import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, SystemStatus, SchedulerStatus, DatabaseStats } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'

// Gmail OAuth scopes
const GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

export default function Settings() {
  const { user, refreshUser } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  const [stats, setStats] = useState<DatabaseStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [gmailConnecting, setGmailConnecting] = useState(false)
  const [gmailSuccess, setGmailSuccess] = useState<string | null>(null)

  // Handle Gmail OAuth callback
  const handleGmailCallback = useCallback(async (code: string) => {
    setGmailConnecting(true)
    setError(null)
    try {
      const redirectUri = `${window.location.origin}/settings`
      await api.exchangeGmailCode(code, redirectUri)
      await refreshUser()
      setGmailSuccess('Gmail connected successfully!')
      // Clear the code from URL
      setSearchParams({})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Gmail')
    } finally {
      setGmailConnecting(false)
    }
  }, [refreshUser, setSearchParams])

  // Check for OAuth callback code on mount
  useEffect(() => {
    const code = searchParams.get('code')
    if (code) {
      handleGmailCallback(code)
    }
  }, [searchParams, handleGmailCallback])

  // Initiate Gmail OAuth flow
  const connectGmail = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    if (!clientId) {
      setError('Google Client ID not configured')
      return
    }

    const redirectUri = `${window.location.origin}/settings`
    const scope = GMAIL_SCOPES.join(' ')

    const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
    authUrl.searchParams.set('client_id', clientId)
    authUrl.searchParams.set('redirect_uri', redirectUri)
    authUrl.searchParams.set('response_type', 'code')
    authUrl.searchParams.set('scope', scope)
    authUrl.searchParams.set('access_type', 'offline')
    authUrl.searchParams.set('prompt', 'consent')

    window.location.href = authUrl.toString()
  }

  // Disconnect Gmail
  const disconnectGmail = async () => {
    setGmailConnecting(true)
    setError(null)
    try {
      await api.disconnectGmail()
      await refreshUser()
      setGmailSuccess('Gmail disconnected')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect Gmail')
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

        {/* Gmail Connection Status */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Gmail Connection</h2>
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
            <div className="pt-2">
              <p className="text-sm text-gray-600">
                {user?.has_gmail_connected
                  ? 'Gmail is connected. Investment emails will be fetched automatically.'
                  : 'Connect your Gmail to fetch investment update emails.'}
              </p>
            </div>
            {gmailSuccess && (
              <div className="p-3 bg-green-100 text-green-700 rounded text-sm">
                {gmailSuccess}
              </div>
            )}
            <div className="pt-2">
              {user?.has_gmail_connected ? (
                <button
                  onClick={disconnectGmail}
                  disabled={gmailConnecting}
                  className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                >
                  {gmailConnecting ? 'Disconnecting...' : 'Disconnect Gmail'}
                </button>
              ) : (
                <button
                  onClick={connectGmail}
                  disabled={gmailConnecting}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.283 10.356h-8.327v3.451h4.792c-.446 2.193-2.313 3.453-4.792 3.453a5.27 5.27 0 0 1-5.279-5.28 5.27 5.27 0 0 1 5.279-5.279c1.259 0 2.397.447 3.29 1.178l2.6-2.599c-1.584-1.381-3.615-2.233-5.89-2.233a8.908 8.908 0 0 0-8.934 8.934 8.907 8.907 0 0 0 8.934 8.934c4.467 0 8.529-3.249 8.529-8.934 0-.528-.081-1.097-.202-1.625z"/>
                  </svg>
                  {gmailConnecting ? 'Connecting...' : 'Connect Gmail'}
                </button>
              )}
            </div>
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
