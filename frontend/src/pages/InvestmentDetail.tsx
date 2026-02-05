import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, InvestmentDetail as InvestmentDetailType, Investment, InvestmentDocument, FieldWithHistory, LeaderInfo } from '../api/client'

// Tooltip component for showing source/history on hover
function SourceTooltip({
  source,
  children
}: {
  source: FieldWithHistory | null
  children: React.ReactNode
}) {
  const [showTooltip, setShowTooltip] = useState(false)

  if (!source) {
    return <>{children}</>
  }

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className="absolute z-50 bottom-full left-0 mb-2 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg min-w-[200px] max-w-[300px]">
          <div className="font-medium mb-1">
            Source: {source.source_type === 'manual' ? 'Manual Edit' : (source.source_name || 'Unknown')}
          </div>
          <div className="text-gray-300 mb-2">
            Confidence: {source.confidence}
          </div>
          {source.all_values && source.all_values.length > 1 && (
            <div className="border-t border-gray-700 pt-2 mt-2">
              <div className="font-medium mb-1">History:</div>
              {source.all_values.slice(0, 5).map((val, idx) => {
                // Format value - handle arrays (like leaders_json) by converting to string
                const displayValue = Array.isArray(val.value)
                  ? val.value.map((v: LeaderInfo) => v.name).join(', ')
                  : val.value
                return (
                  <div key={idx} className="text-gray-300 truncate">
                    "{displayValue}" — {val.source_name || 'Unknown'}
                  </div>
                )
              })}
            </div>
          )}
          <div className="absolute bottom-0 left-4 transform translate-y-full">
            <div className="border-8 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  )
}

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

  const getFieldSource = (key: string) => {
    if (!investment?.field_attributions || !investment.field_attributions[key]) {
      return null
    }
    return investment.field_attributions[key]
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  if (error || !investment) {
    return (
      <div className="text-center py-12">
        <div className="text-red-400 mb-4">{error || 'Investment not found'}</div>
        <Link to="/" className="text-accent hover:text-accent-400">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  // Get leaders from JSON array
  const leaders: LeaderInfo[] = investment.leaders_json || []

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back link */}
      <Link to="/" className="text-accent hover:text-accent-400 text-sm inline-flex items-center mb-4">
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </Link>

      {/* Main Card */}
      <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
        {/* Header with Edit Button */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1 flex flex-col">
            {/* Firm - On Top */}
            {editing ? (
              <input
                type="text"
                value={formData.firm || ''}
                onChange={(e) => handleChange('firm', e.target.value)}
                className="w-full text-sm bg-white/10 border border-white/20 rounded px-2 py-1 text-gray-400 mb-2"
                placeholder="Firm Name"
              />
            ) : (
              <SourceTooltip source={getFieldSource('firm')}>
                <p className="text-sm text-gray-400 cursor-help mb-2">
                  {investment.firm || <span className="italic text-gray-500">No firm</span>}
                </p>
              </SourceTooltip>
            )}

            {/* Investment Name - Main Heading */}
            {editing ? (
              <input
                type="text"
                value={formData.investment_name || ''}
                onChange={(e) => handleChange('investment_name', e.target.value)}
                className="w-full text-2xl font-bold bg-white/10 border border-white/20 rounded px-2 py-1 text-white"
                placeholder="Investment Name"
              />
            ) : (
              <SourceTooltip source={getFieldSource('investment_name')}>
                <h1 className="text-2xl font-bold text-white cursor-help">
                  {investment.investment_name || 'Unnamed Investment'}
                </h1>
              </SourceTooltip>
            )}
          </div>

          {/* Edit/Save Buttons */}
          <div className="ml-4">
            {editing ? (
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setFormData(investment)
                    setEditing(false)
                  }}
                  className="px-3 py-1.5 text-sm border border-white/20 rounded text-gray-300 hover:bg-white/10"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent-600"
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setEditing(true)}
                className="px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent-600"
              >
                Edit
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/20 text-red-300 rounded text-sm">
            {error}
          </div>
        )}

        {/* Leaders - Chips with LinkedIn links */}
        {(editing || leaders.length > 0) && (
          <div className="mb-4">
            {editing ? (
              <textarea
                value={formData.leaders_json
                  ? formData.leaders_json.map(l =>
                      l.linkedin_url ? `${l.name} | ${l.linkedin_url}` : l.name
                    ).join('\n')
                  : ''
                }
                onChange={(e) => {
                  const lines = e.target.value.split('\n').filter(Boolean)
                  const parsed: LeaderInfo[] = lines.map(line => {
                    const [name, url] = line.split('|').map(s => s.trim())
                    return { name: name || '', linkedin_url: url || null }
                  })
                  setFormData(prev => ({ ...prev, leaders_json: parsed }))
                }}
                rows={3}
                className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white text-sm"
                placeholder="One leader per line. Format: Name | LinkedIn URL (optional)"
              />
            ) : (
              <SourceTooltip source={getFieldSource('leaders_json')}>
                <div className="flex flex-wrap gap-2">
                  {leaders.map((leader, idx) => (
                    leader.linkedin_url ? (
                      <a
                        key={idx}
                        href={leader.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 bg-primary/50 text-white text-sm rounded-full hover:bg-primary/70 transition-colors inline-flex items-center gap-1.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {leader.name}
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                        </svg>
                      </a>
                    ) : (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-primary/50 text-white text-sm rounded-full"
                      >
                        {leader.name}
                      </span>
                    )
                  ))}
                </div>
              </SourceTooltip>
            )}
          </div>
        )}

        {/* Fees, Liquidity, Returns - Single Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 py-4 border-y border-white/10">
          {[
            { key: 'management_fees', label: 'Mgmt Fees' },
            { key: 'incentive_fees', label: 'Incentive' },
            { key: 'liquidity_lock', label: 'Liquidity' },
            { key: 'target_net_returns', label: 'Target Returns' },
          ].map(({ key, label }) => (
            <div key={key}>
              <div className="text-xs text-gray-400 mb-1">{label}</div>
              {editing ? (
                <input
                  type="text"
                  value={(formData[key as keyof Investment] as string) || ''}
                  onChange={(e) => handleChange(key as keyof Investment, e.target.value)}
                  className="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-white text-sm"
                />
              ) : (
                <SourceTooltip source={getFieldSource(key)}>
                  <div className="text-white text-sm cursor-help">
                    {(investment[key as keyof Investment] as string) || (
                      <span className="text-gray-500 italic">N/A</span>
                    )}
                  </div>
                </SourceTooltip>
              )}
            </div>
          ))}
        </div>

        {/* Strategy Description - Larger */}
        <div className="mb-6">
          <div className="text-xs text-gray-400 mb-2">Strategy</div>
          {editing ? (
            <textarea
              value={formData.strategy_description || ''}
              onChange={(e) => handleChange('strategy_description', e.target.value)}
              rows={5}
              className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white"
              placeholder="Strategy description..."
            />
          ) : (
            <SourceTooltip source={getFieldSource('strategy_description')}>
              <p className="text-gray-200 leading-relaxed cursor-help">
                {investment.strategy_description || (
                  <span className="text-gray-500 italic">No strategy description</span>
                )}
              </p>
            </SourceTooltip>
          )}
        </div>

        {/* Notes */}
        <div className="mb-6">
          <div className="text-xs text-gray-400 mb-2">Notes</div>
          {editing ? (
            <textarea
              value={formData.notes || ''}
              onChange={(e) => handleChange('notes', e.target.value)}
              rows={3}
              className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white text-sm"
              placeholder="Add notes..."
            />
          ) : (
            <p className="text-gray-300 text-sm">
              {investment.notes || (
                <span className="text-gray-500 italic">No notes</span>
              )}
            </p>
          )}
        </div>

        {/* Documents - Icons */}
        {investment.documents && investment.documents.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-400 mb-2">Documents</div>
            <div className="flex flex-wrap gap-2">
              {investment.documents.map((doc) => (
                <div key={doc.id} className="flex items-center space-x-1">
                  {doc.has_pdf && (
                    <button
                      onClick={() => handleDownloadPdf(doc)}
                      disabled={downloading === `pdf-${doc.document_id}`}
                      className="group relative p-2 bg-red-500/20 hover:bg-red-500/30 rounded transition-colors disabled:opacity-50"
                      title={`Download PDF: ${doc.filename}`}
                    >
                      <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                      {downloading === `pdf-${doc.document_id}` && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded">
                          <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        </div>
                      )}
                    </button>
                  )}
                  {doc.has_markdown && (
                    <button
                      onClick={() => handleDownloadMarkdown(doc)}
                      disabled={downloading === `md-${doc.document_id}`}
                      className="group relative p-2 bg-blue-500/20 hover:bg-blue-500/30 rounded transition-colors disabled:opacity-50"
                      title={`Download Markdown: ${doc.filename}`}
                    >
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {downloading === `md-${doc.document_id}` && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded">
                          <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        </div>
                      )}
                    </button>
                  )}
                  <span className="text-xs text-gray-400 max-w-[120px] truncate" title={doc.filename}>
                    {doc.filename}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata - Tiny Footer */}
        <div className="pt-4 border-t border-white/10 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
          <span>Created: {new Date(investment.created_at).toLocaleDateString()}</span>
          <span>Updated: {new Date(investment.updated_at).toLocaleDateString()}</span>
          <span>{investment.source_count} source{investment.source_count !== 1 ? 's' : ''}</span>
          <span className="font-mono">{investment.id}</span>
          {investment.is_archived && <span className="text-orange-400">Archived</span>}
        </div>
      </div>
    </div>
  )
}
