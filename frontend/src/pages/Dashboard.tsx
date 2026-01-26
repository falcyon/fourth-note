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
  const [sortBy, setSortBy] = useState('updated_at')
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

  const SortButton = ({ column, label }: { column: string; label: string }) => (
    <button
      onClick={() => handleSort(column)}
      className={`text-xs uppercase tracking-wider transition-colors ${
        sortBy === column ? 'text-accent-300' : 'text-gray-500 hover:text-gray-300'
      }`}
    >
      {label} {sortBy === column && (sortOrder === 'asc' ? '↑' : '↓')}
    </button>
  )

  return (
    <div>
      {/* Demo Hero Section */}
      <div className="bg-white/5 backdrop-blur-sm rounded-lg p-8 mb-8 text-white border border-white/10">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">Fourth Note</h1>
          <p className="text-xl text-gray-400 mb-6">
            Your centralized brain for investment tracking. Automatically fetch pitch decks from your email,
            extract key metrics with AI, and keep all your investment data organized in one place.
          </p>
          <a
            href="https://accounts.google.com/signin"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-6 py-3 bg-accent text-white font-semibold rounded-lg hover:bg-accent-600 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Sign in with Google
          </a>
          <p className="mt-4 text-sm text-gray-500">
            The list below shows a demo account. Send an investment pitch to{' '}
            <span className="font-semibold text-accent-300">fourthnotetest@gmail.com</span>{' '}
            to see it in action!
          </p>
        </div>
      </div>

      {/* Dashboard Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">Demo Investments</h2>
        <div className="flex items-center space-x-3">
          <TriggerButton onComplete={fetchData} />
          <button
            onClick={() => api.exportCsv()}
            className="px-4 py-2 bg-white/10 text-white rounded-md hover:bg-white/20 transition-colors border border-white/10"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Search and Sort */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <input
          type="text"
          placeholder="Search investments..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="flex-1 min-w-[200px] max-w-md px-4 py-2 bg-white/5 border border-white/10 rounded-md text-white placeholder-gray-500 focus:ring-2 focus:ring-accent focus:border-transparent"
        />
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-500">Sort:</span>
          <SortButton column="updated_at" label="Updated" />
          <SortButton column="investment_name" label="Name" />
          <SortButton column="firm" label="Firm" />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-500/20 text-red-300 rounded-md border border-red-500/30">
          {error}
        </div>
      )}

      {/* Investment Rows */}
      <div className="space-y-2">
        {loading ? (
          <div className="py-12 text-center text-gray-500">Loading...</div>
        ) : data?.items.length === 0 ? (
          <div className="py-12 text-center text-gray-500">
            No investments found. Click "Fetch Emails" to process new pitch decks.
          </div>
        ) : (
          data?.items.map((inv) => (
            <Link
              key={inv.id}
              to={`/investment/${inv.id}`}
              className="block bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg p-4 transition-colors group"
            >
              <div className="flex items-start gap-6">
                {/* Primary Info - Grows to fill space */}
                <div className="flex-[2] min-w-0">
                  <div className="text-xs text-gray-500 truncate">{inv.firm || 'Unknown Firm'}</div>
                  <h3 className="text-white font-medium group-hover:text-accent-300 transition-colors truncate">
                    {inv.investment_name || 'Unnamed Investment'}
                  </h3>
                  {inv.strategy_description && (
                    <p className="text-sm text-gray-400 mt-1 line-clamp-2">{inv.strategy_description}</p>
                  )}
                </div>

                {/* Leaders */}
                <div className="hidden lg:block w-[140px] flex-shrink-0">
                  <div className="text-xs text-gray-500 mb-1">Leaders</div>
                  <div className="max-h-[3.5rem] overflow-hidden">
                    {inv.leaders ? (
                      <div className="flex flex-wrap gap-1">
                        {inv.leaders.split(',').map((leader, idx) => (
                          <span key={idx} className="text-xs bg-white/10 text-gray-400 px-2 py-0.5 rounded truncate max-w-[100px]">
                            {leader.trim()}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </div>
                </div>

                {/* Metrics - Two columns */}
                <div className="flex gap-8 text-sm">
                  {/* Column 1: Mgmt & Incentive */}
                  <div className="w-[140px]">
                    <div>
                      <div className="text-xs text-gray-500">Mgmt</div>
                      <div className="text-gray-300 truncate">{inv.management_fees || '-'}</div>
                    </div>
                    <div className="mt-1">
                      <div className="text-xs text-gray-500">Incentive</div>
                      <div className="text-gray-300 truncate">{inv.incentive_fees || '-'}</div>
                    </div>
                  </div>
                  {/* Column 2: Liquidity & Target */}
                  <div className="w-[140px]">
                    <div>
                      <div className="text-xs text-gray-500">Liquidity</div>
                      <div className="text-gray-300 truncate">{inv.liquidity_lock || '-'}</div>
                    </div>
                    <div className="mt-1">
                      <div className="text-xs text-gray-500">Target</div>
                      <div className="text-gray-300 truncate">{inv.target_net_returns || '-'}</div>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="mt-4">
          <Pagination
            currentPage={page}
            totalPages={data.pages}
            onPageChange={setPage}
          />
        </div>
      )}

      {/* Stats */}
      {data && (
        <div className="mt-4 text-sm text-gray-500">
          Showing {data.items.length} of {data.total} investments
        </div>
      )}
    </div>
  )
}
