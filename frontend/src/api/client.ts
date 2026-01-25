const API_BASE = '/api/v1'

export interface Investment {
  id: string
  document_id: string
  investment_name: string | null
  firm: string | null
  strategy_description: string | null
  leaders: string | null
  management_fees: string | null
  incentive_fees: string | null
  liquidity_lock: string | null
  target_net_returns: string | null
  raw_extraction_json: Record<string, unknown> | null
  created_at: string
  updated_at: string
  source_filename: string | null
  source_email_subject: string | null
}

export interface InvestmentListResponse {
  items: Investment[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface SystemStatus {
  status: string
  database: string
  gmail: string
  timestamp: string
}

export interface SchedulerStatus {
  running: boolean
  interval_hours: number
  next_run: string | null
  last_run: string | null
  last_result: Record<string, unknown> | null
}

export interface OAuthStatus {
  authenticated: boolean
  token_exists: boolean
  token_expired: boolean | null
  message: string
  error: string | null
}

export interface DatabaseStats {
  total_emails: number
  total_documents: number
  total_investments: number
  pending_documents: number
  failed_documents: number
}

export interface TriggerResponse {
  message: string
  status: string
  emails_fetched: number | null
  investments_extracted: number | null
  error: string | null
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Investments
  listInvestments: (params?: {
    page?: number
    per_page?: number
    search?: string
    sort_by?: string
    sort_order?: string
  }): Promise<InvestmentListResponse> => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.per_page) query.set('per_page', String(params.per_page))
    if (params?.search) query.set('search', params.search)
    if (params?.sort_by) query.set('sort_by', params.sort_by)
    if (params?.sort_order) query.set('sort_order', params.sort_order)
    const queryString = query.toString()
    return fetchApi(`/investments${queryString ? `?${queryString}` : ''}`)
  },

  getInvestment: (id: string): Promise<Investment> => {
    return fetchApi(`/investments/${id}`)
  },

  updateInvestment: (id: string, data: Partial<Investment>): Promise<Investment> => {
    return fetchApi(`/investments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  exportCsv: (): string => {
    return `${API_BASE}/investments/export/csv`
  },

  // Status
  getSystemStatus: (): Promise<SystemStatus> => {
    return fetchApi('/status')
  },

  getSchedulerStatus: (): Promise<SchedulerStatus> => {
    return fetchApi('/scheduler/status')
  },

  getOAuthStatus: (): Promise<OAuthStatus> => {
    return fetchApi('/oauth/status')
  },

  getStats: (): Promise<DatabaseStats> => {
    return fetchApi('/stats')
  },

  // Trigger
  triggerFetchEmails: (): Promise<TriggerResponse> => {
    return fetchApi('/trigger/fetch-emails', { method: 'POST' })
  },

  // Documents
  getDocumentMarkdown: (id: string): Promise<{ id: string; filename: string; markdown_content: string | null }> => {
    return fetchApi(`/documents/${id}/markdown`)
  },
}
