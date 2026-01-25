import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, InvestmentDetail as InvestmentDetailType, Investment, InvestmentDocument } from '../api/client'

export default function InvestmentDetail() {
  const { id } = useParams<{ id: string }>()
  const [investment, setInvestment] = useState<InvestmentDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState<Partial<Investment>>({})
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState<string | null>(null)

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

  const handleDownloadPdf = async (doc: InvestmentDocument) => {
    try {
      setDownloading(`pdf-${doc.document_id}`)
      await api.downloadDocumentPdf(doc.document_id, doc.filename)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download PDF')
    } finally {
      setDownloading(null)
    }
  }

  const handleDownloadMarkdown = async (doc: InvestmentDocument) => {
    try {
      setDownloading(`md-${doc.document_id}`)
      await api.downloadDocumentMarkdown(doc.document_id, doc.filename)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download markdown')
    } finally {
      setDownloading(null)
    }
  }

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

  // Get source info for a field
  const getFieldSource = (key: string) => {
    if (!investment.field_attributions || !investment.field_attributions[key]) {
      return null
    }
    return investment.field_attributions[key]
  }

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
          {investment.source_count > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              {investment.source_count} source{investment.source_count !== 1 ? 's' : ''}
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
          {fields.map(({ key, label, multiline }) => {
            const source = getFieldSource(key)
            return (
              <div key={key} className="px-6 py-4">
                <div className="flex justify-between items-start mb-1">
                  <label className="block text-sm font-medium text-gray-500">
                    {label}
                  </label>
                  {!editing && source && (
                    <span className="text-xs text-gray-400" title={`From: ${source.source_name}`}>
                      {source.source_type === 'manual' ? '✓ Verified' : source.source_name}
                    </span>
                  )}
                </div>
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
            )
          })}
        </div>
      </div>

      {/* Notes Section */}
      <div className="mt-6 bg-white shadow-md rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Notes</h2>
        {editing ? (
          <textarea
            value={formData.notes || ''}
            onChange={(e) => handleChange('notes', e.target.value)}
            rows={4}
            placeholder="Add your notes about this investment..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        ) : (
          <div className="text-gray-900">
            {investment.notes || (
              <span className="text-gray-400 italic">No notes added</span>
            )}
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="mt-6 bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Metadata</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Created</dt>
            <dd className="text-gray-900">{new Date(investment.created_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Updated</dt>
            <dd className="text-gray-900">{new Date(investment.updated_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Investment ID</dt>
            <dd className="text-gray-900 font-mono text-xs">{investment.id}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Status</dt>
            <dd className="text-gray-900">
              {investment.is_archived ? (
                <span className="text-orange-600">Archived</span>
              ) : (
                <span className="text-green-600">Active</span>
              )}
            </dd>
          </div>
        </dl>
      </div>

      {/* Related Documents */}
      {investment.documents && investment.documents.length > 0 && (
        <div className="mt-6 bg-white shadow-md rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Related Documents</h2>
          <div className="space-y-3">
            {investment.documents.map((doc) => (
              <div key={doc.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                      <div>
                        <p className="font-medium text-gray-900">{doc.filename}</p>
                        <p className="text-sm text-gray-500">
                          {doc.relationship} • Added {new Date(doc.added_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="px-4 py-3 flex flex-wrap gap-2">
                  {doc.has_pdf && (
                    <button
                      onClick={() => handleDownloadPdf(doc)}
                      disabled={downloading === `pdf-${doc.document_id}`}
                      className="inline-flex items-center px-3 py-1.5 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      {downloading === `pdf-${doc.document_id}` ? 'Downloading...' : 'Download PDF'}
                    </button>
                  )}
                  {doc.has_markdown && (
                    <button
                      onClick={() => handleDownloadMarkdown(doc)}
                      disabled={downloading === `md-${doc.document_id}`}
                      className="inline-flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      {downloading === `md-${doc.document_id}` ? 'Downloading...' : 'Download Markdown'}
                    </button>
                  )}
                  {!doc.has_pdf && !doc.has_markdown && (
                    <p className="text-sm text-gray-500 italic">No files available for download</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Field History (collapsible) */}
      {investment.field_attributions && Object.keys(investment.field_attributions).length > 0 && (
        <details className="mt-6">
          <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
            View Field History
          </summary>
          <div className="mt-2 p-4 bg-gray-50 rounded-lg text-sm">
            {Object.entries(investment.field_attributions).map(([field, attr]) => (
              <div key={field} className="mb-4 last:mb-0">
                <h4 className="font-medium text-gray-700 mb-2">{field}</h4>
                <ul className="space-y-1 pl-4">
                  {attr.all_values.map((val, idx) => (
                    <li key={idx} className={`${val.value === attr.value ? 'font-medium' : 'text-gray-500'}`}>
                      "{val.value}" — {val.source_name} ({val.confidence})
                      {val.value === attr.value && ' ← current'}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
