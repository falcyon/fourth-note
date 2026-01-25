import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api, InvestmentListResponse } from '../api/client'
import TriggerButton from '../components/TriggerButton'
import Pagination from '../components/Pagination'

export default function Dashboard() {
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
      {/* Demo Hero Section */}
      <div className="bg-gradient-to-r from-blue-800 to-blue-600 rounded-lg p-8 mb-8 text-white">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">Fourth Note</h1>
          <p className="text-xl text-blue-100 mb-6">
            Your centralized brain for investment tracking. Automatically fetch pitch decks from your email,
            extract key metrics with AI, and keep all your investment data organized in one place.
          </p>
          <a
            href="https://accounts.google.com/signin"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-6 py-3 bg-white text-blue-800 font-semibold rounded-lg hover:bg-blue-50 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Sign in with Google
          </a>
          <p className="mt-4 text-sm text-blue-200">
            The table below shows a demo account. Send an investment pitch to{' '}
            <span className="font-semibold text-white">fourthnotetest@gmail.com</span>{' '}
            to see it in action!
          </p>
        </div>
      </div>

      {/* Dashboard Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Demo Investments</h2>
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
