import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, InvestmentDetail as InvestmentDetailType, Investment, InvestmentDocument, FieldWithHistory, LeaderInfo } from '../api/client'
import MissingValue, { displayValue } from '../components/MissingValue'

// Info icon that shows source/history on click
function SourceInfo({ source }: { source: FieldWithHistory | null }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!source) {
    return null
  }

  return (
    <div className="relative inline-block ml-1.5">
      <button
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(!isOpen)
        }}
        className="w-4 h-4 rounded-full bg-gray-200 dark:bg-white/20 text-gray-500 dark:text-gray-400 text-[10px] font-medium hover:bg-gray-300 dark:hover:bg-white/30 transition-colors flex items-center justify-center"
        title="View source info"
      >
        ?
      </button>
      {isOpen && (
        <>
          {/* Backdrop to close on click outside */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-50 bottom-full right-0 mb-2 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg min-w-[200px] max-w-[300px]">
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
                  const formattedValue = Array.isArray(val.value)
                    ? val.value.map((v: LeaderInfo) => v.name).join(', ')
                    : val.value
                  return (
                    <div key={idx} className="text-gray-300 truncate">
                      "{formattedValue}" — {val.source_name || 'Unknown'}
                    </div>
                  )
                })}
              </div>
            )}
            <div className="absolute bottom-0 right-2 transform translate-y-full">
              <div className="border-8 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        </>
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

  const handleExportInvestment = () => {
    if (!investment) return

    const leaders = investment.leaders_json || []
    const docs = investment.documents || []

    const lines = [
      `# ${investment.investment_name || 'Unnamed Investment'}`,
      '',
      `**Firm:** ${displayValue(investment.firm)}`,
      '',
      '## Key Terms',
      '',
      `- **Management Fees:** ${displayValue(investment.management_fees)}`,
      `- **Incentive Fees:** ${displayValue(investment.incentive_fees)}`,
      `- **Liquidity/Lock:** ${displayValue(investment.liquidity_lock)}`,
      `- **Target Returns:** ${displayValue(investment.target_net_returns)}`,
      '',
      '## Strategy',
      '',
      displayValue(investment.strategy_description),
      '',
    ]

    if (leaders.length > 0) {
      lines.push('## Investment Team', '')
      leaders.forEach(l => lines.push(`- ${l.name}`))
      lines.push('')
    }

    if (investment.notes) {
      lines.push('## Notes', '', investment.notes, '')
    }

    if (docs.length > 0) {
      lines.push('## Source Documents', '')
      docs.forEach(d => lines.push(`- ${d.filename}`))
      lines.push('')
    }

    lines.push('---', '', `*Exported on ${new Date().toLocaleDateString()}*`)

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${(investment.investment_name || 'investment').replace(/\s+/g, '_')}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const renderStrategy = (text: string) => {
    // Split on newlines, then clean up each line
    const points = text
      .split('\n')
      .map(s => s.replace(/^[•\-\*]\s*/, '').trim())
      .filter(Boolean)

    if (points.length <= 1) {
      // Single paragraph - just show as-is
      return <p className="text-gray-700 dark:text-gray-200 leading-relaxed">{text}</p>
    }

    // Multiple points - render as bullet list
    return (
      <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-200">
        {points.map((point, i) => (
          <li key={i}>{point}</li>
        ))}
      </ul>
    )
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
      <div className="bg-white dark:bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-gray-200 dark:border-white/10 shadow-sm dark:shadow-none">
        {/* Header with Edit Button */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1 flex flex-col">
            {/* Firm - On Top */}
            {editing ? (
              <input
                type="text"
                value={formData.firm || ''}
                onChange={(e) => handleChange('firm', e.target.value)}
                className="w-full text-sm bg-gray-100 dark:bg-white/10 border border-gray-300 dark:border-white/20 rounded px-2 py-1 text-gray-600 dark:text-gray-400 mb-2"
                placeholder="Firm Name"
              />
            ) : (
              <div className="flex items-end mb-2">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {investment.firm || <MissingValue />}
                </p>
                <SourceInfo source={getFieldSource('firm')} />
              </div>
            )}

            {/* Investment Name - Main Heading */}
            {editing ? (
              <input
                type="text"
                value={formData.investment_name || ''}
                onChange={(e) => handleChange('investment_name', e.target.value)}
                className="w-full text-2xl font-bold bg-gray-100 dark:bg-white/10 border border-gray-300 dark:border-white/20 rounded px-2 py-1 text-gray-900 dark:text-white"
                placeholder="Investment Name"
              />
            ) : (
              <div className="flex items-end">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {investment.investment_name || 'Unnamed Investment'}
                </h1>
                <SourceInfo source={getFieldSource('investment_name')} />
              </div>
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
                  className="px-3 py-1.5 text-sm border border-gray-300 dark:border-white/20 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10"
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
              <div className="flex space-x-2">
                <button
                  onClick={handleExportInvestment}
                  className="px-3 py-1.5 text-sm border border-gray-300 dark:border-white/20 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 inline-flex items-center gap-1.5"
                  title="Export as Markdown"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export
                </button>
                <button
                  onClick={() => setEditing(true)}
                  className="px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent-600"
                >
                  Edit
                </button>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/20 text-red-300 rounded text-sm">
            {error}
          </div>
        )}

        {/* Investment Team */}
        {(editing || leaders.length > 0) && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Investment Team</div>
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
                className="w-full bg-gray-100 dark:bg-white/10 border border-gray-300 dark:border-white/20 rounded px-3 py-2 text-gray-900 dark:text-white text-sm"
                placeholder="One leader per line. Format: Name | LinkedIn URL (optional)"
              />
            ) : (
              <div className="flex items-end">
                <p className="text-gray-700 dark:text-gray-200 text-sm">
                  {leaders.map(l => l.name).join(', ')}
                </p>
                <SourceInfo source={getFieldSource('leaders_json')} />
              </div>
            )}
          </div>
        )}

        {/* Fees, Liquidity, Returns - Single Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 py-4 border-y border-gray-200 dark:border-white/10">
          {[
            { key: 'management_fees', label: 'Mgmt Fees' },
            { key: 'incentive_fees', label: 'Incentive' },
            { key: 'liquidity_lock', label: 'Liquidity' },
            { key: 'target_net_returns', label: 'Target Returns' },
          ].map(({ key, label }) => (
            <div key={key}>
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</div>
              {editing ? (
                <input
                  type="text"
                  value={(formData[key as keyof Investment] as string) || ''}
                  onChange={(e) => handleChange(key as keyof Investment, e.target.value)}
                  className="w-full bg-gray-100 dark:bg-white/10 border border-gray-300 dark:border-white/20 rounded px-2 py-1 text-gray-900 dark:text-white text-sm"
                />
              ) : (
                <div className="flex items-end">
                  <div className="text-gray-900 dark:text-white text-sm">
                    {(investment[key as keyof Investment] as string) || <MissingValue />}
                  </div>
                  <SourceInfo source={getFieldSource(key)} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Strategy Description - Larger */}
        <div className="mb-6">
          <div className="flex items-end mb-2">
            <div className="text-xs text-gray-500 dark:text-gray-400">Strategy</div>
            {!editing && <SourceInfo source={getFieldSource('strategy_description')} />}
          </div>
          {editing ? (
            <textarea
              value={formData.strategy_description || ''}
              onChange={(e) => handleChange('strategy_description', e.target.value)}
              rows={5}
              className="w-full bg-gray-100 dark:bg-white/10 border border-gray-300 dark:border-white/20 rounded px-3 py-2 text-gray-900 dark:text-white"
              placeholder="Strategy description..."
            />
          ) : (
            <div>
              {investment.strategy_description ? (
                renderStrategy(investment.strategy_description)
              ) : (
                <MissingValue />
              )}
            </div>
          )}
        </div>

        {/* Notes */}
        <div className="mb-6">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Notes</div>
          {editing ? (
            <textarea
              value={formData.notes || ''}
              onChange={(e) => handleChange('notes', e.target.value)}
              rows={3}
              className="w-full bg-gray-100 dark:bg-white/10 border border-gray-300 dark:border-white/20 rounded px-3 py-2 text-gray-900 dark:text-white text-sm"
              placeholder="Add notes..."
            />
          ) : (
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              {investment.notes || <MissingValue />}
            </p>
          )}
        </div>

        {/* Documents - Icons */}
        {investment.documents && investment.documents.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Documents</div>
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
        <div className="pt-4 border-t border-gray-200 dark:border-white/10 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
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
