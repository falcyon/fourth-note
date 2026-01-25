import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api, InvestmentListResponse } from '../api/client'
import TriggerButton from '../components/TriggerButton'
import Pagination from '../components/Pagination'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<InvestmentListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('investment_name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const result = await api.listInvestments({
        page,
        per_page: 20,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      })
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load investments')
    } finally {
      setLoading(false)
    }
  }, [page, search, sortBy, sortOrder])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }

  const SortIcon = ({ column }: { column: string }) => {
    if (sortBy !== column) return null
    return <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Investments Dashboard</h1>
        <div className="flex items-center space-x-4">
          <TriggerButton onComplete={fetchData} />
          <button
            onClick={() => api.exportCsv()}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Gmail not connected warning */}
      {user && !user.has_gmail_connected && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-yellow-400 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-yellow-800">Gmail not connected</h3>
              <p className="mt-1 text-sm text-yellow-700">
                Connect your Gmail account in{' '}
                <Link to="/settings" className="font-medium underline hover:text-yellow-800">
                  Settings
                </Link>
                {' '}to fetch investment emails from your inbox.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search investments..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  onClick={() => handleSort('investment_name')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Investment <SortIcon column="investment_name" />
                </th>
                <th
                  onClick={() => handleSort('firm')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Firm <SortIcon column="firm" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Leaders
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mgmt Fees
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Incentive
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Liquidity
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Target Returns
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-gray-500">
                    No investments found. Click "Fetch Emails" to process new pitch decks.
                  </td>
                </tr>
              ) : (
                data?.items.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/investment/${inv.id}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {inv.investment_name || 'Unnamed'}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {inv.firm || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate" title={inv.strategy_description || ''}>
                      {inv.strategy_description || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {inv.leaders || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {inv.management_fees || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {inv.incentive_fees || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {inv.liquidity_lock || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {inv.target_net_returns || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <Pagination
            currentPage={page}
            totalPages={data.pages}
            onPageChange={setPage}
          />
        )}
      </div>

      {/* Stats */}
      {data && (
        <div className="mt-4 text-sm text-gray-500">
          Showing {data.items.length} of {data.total} investments
        </div>
      )}
    </div>
  )
}
