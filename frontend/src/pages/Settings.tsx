import { useState, useEffect } from 'react'
import { api, SystemStatus, SchedulerStatus, OAuthStatus, DatabaseStats } from '../api/client'
import StatusBadge from '../components/StatusBadge'

export default function Settings() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  const [oauthStatus, setOAuthStatus] = useState<OAuthStatus | null>(null)
  const [stats, setStats] = useState<DatabaseStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true)
        const [system, scheduler, oauth, dbStats] = await Promise.all([
          api.getSystemStatus(),
          api.getSchedulerStatus(),
          api.getOAuthStatus(),
          api.getStats(),
        ])
        setSystemStatus(system)
        setSchedulerStatus(scheduler)
        setOAuthStatus(oauth)
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

        {/* Gmail OAuth */}
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Gmail Connection</h2>
          {oauthStatus && (
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-gray-500">Authenticated</dt>
                <dd>
                  <StatusBadge
                    status={oauthStatus.authenticated ? 'success' : 'error'}
                    text={oauthStatus.authenticated ? 'Yes' : 'No'}
                  />
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Token File</dt>
                <dd>
                  <StatusBadge
                    status={oauthStatus.token_exists ? 'success' : 'error'}
                    text={oauthStatus.token_exists ? 'Present' : 'Missing'}
                  />
                </dd>
              </div>
              <div className="pt-2">
                <p className="text-sm text-gray-600">{oauthStatus.message}</p>
              </div>
            </dl>
          )}
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
        <a
          href={api.exportCsv()}
          className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export to CSV
        </a>
      </div>
    </div>
  )
}
