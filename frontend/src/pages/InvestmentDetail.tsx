import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, Investment } from '../api/client'

export default function InvestmentDetail() {
  const { id } = useParams<{ id: string }>()
  const [investment, setInvestment] = useState<Investment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState<Partial<Investment>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) return

    const fetchInvestment = async () => {
      try {
        setLoading(true)
        const data = await api.getInvestment(id)
        setInvestment(data)
        setFormData(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load investment')
      } finally {
        setLoading(false)
      }
    }

    fetchInvestment()
  }, [id])

  const handleSave = async () => {
    if (!id) return

    try {
      setSaving(true)
      const updated = await api.updateInvestment(id, formData)
      setInvestment(updated)
      setEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (field: keyof Investment, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  if (error || !investment) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error || 'Investment not found'}</div>
        <Link to="/" className="text-blue-600 hover:text-blue-800">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  const fields: { key: keyof Investment; label: string; multiline?: boolean }[] = [
    { key: 'investment_name', label: 'Investment Name' },
    { key: 'firm', label: 'Firm' },
    { key: 'strategy_description', label: 'Strategy Description', multiline: true },
    { key: 'leaders', label: 'Leaders/PM/CEO' },
    { key: 'management_fees', label: 'Management Fees' },
    { key: 'incentive_fees', label: 'Incentive Fees' },
    { key: 'liquidity_lock', label: 'Liquidity/Lock' },
    { key: 'target_net_returns', label: 'Target Net Returns' },
  ]

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <Link to="/" className="text-blue-600 hover:text-blue-800 text-sm">
            ← Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2">
            {investment.investment_name || 'Unnamed Investment'}
          </h1>
          {investment.source_filename && (
            <p className="text-sm text-gray-500 mt-1">
              Source: {investment.source_filename}
            </p>
          )}
        </div>
        <div>
          {editing ? (
            <div className="space-x-2">
              <button
                onClick={() => {
                  setFormData(investment)
                  setEditing(false)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Edit
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {/* Fields */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="divide-y divide-gray-200">
          {fields.map(({ key, label, multiline }) => (
            <div key={key} className="px-6 py-4">
              <label className="block text-sm font-medium text-gray-500 mb-1">
                {label}
              </label>
              {editing ? (
                multiline ? (
                  <textarea
                    value={(formData[key] as string) || ''}
                    onChange={(e) => handleChange(key, e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <input
                    type="text"
                    value={(formData[key] as string) || ''}
                    onChange={(e) => handleChange(key, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                )
              ) : (
                <div className="text-gray-900">
                  {(investment[key] as string) || (
                    <span className="text-gray-400 italic">Not extracted</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-6 bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Metadata</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Extracted At</dt>
            <dd className="text-gray-900">{new Date(investment.created_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Updated</dt>
            <dd className="text-gray-900">{new Date(investment.updated_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Document ID</dt>
            <dd className="text-gray-900 font-mono text-xs">{investment.document_id}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Email Subject</dt>
            <dd className="text-gray-900">{investment.source_email_subject || '-'}</dd>
          </div>
        </dl>
      </div>

      {/* Raw JSON (collapsible) */}
      {investment.raw_extraction_json && (
        <details className="mt-6">
          <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
            View Raw Extraction JSON
          </summary>
          <pre className="mt-2 p-4 bg-gray-800 text-gray-100 rounded-lg text-xs overflow-x-auto">
            {JSON.stringify(investment.raw_extraction_json, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}
