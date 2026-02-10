import { API_BASE, TOKEN_KEY, USER_KEY } from '../constants'

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    return { 'Authorization': `Bearer ${token}` }
  }
  return {}
}

// Leader with optional LinkedIn profile
export interface LeaderInfo {
  name: string
  linkedin_url: string | null
}

// Field attribution for tracking sources
export interface FieldAttribution {
  value: string | LeaderInfo[] | null  // Can be string or JSON array
  source_type: string
  source_id: string | null
  source_name: string | null
  confidence: string
  extracted_at: string
}

export interface FieldWithHistory extends FieldAttribution {
  all_values: FieldAttribution[]
}

// Document linked to an investment
export interface InvestmentDocument {
  id: string
  document_id: string
  filename: string
  relationship: string
  has_pdf: boolean
  has_markdown: boolean
  added_at: string
}

// Base investment fields
export interface Investment {
  id: string
  investment_name: string | null
  firm: string | null
  strategy_description: string | null
  leaders_json: LeaderInfo[] | null
  management_fees: string | null
  incentive_fees: string | null
  liquidity_lock: string | null
  target_net_returns: string | null
  notes: string | null
  is_archived: boolean
  source_count: number
  created_at: string
  updated_at: string
}

// Detailed investment with attributions and documents
export interface InvestmentDetail extends Investment {
  field_attributions: Record<string, FieldWithHistory> | null
  documents: InvestmentDocument[]
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

export interface DocumentInfo {
  id: string
  email_id: string
  filename: string
  file_path: string | null
  markdown_file_path: string | null
  processing_status: string
  error_message: string | null
  created_at: string
  updated_at: string
  has_pdf: boolean
  has_markdown: boolean
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options?.headers,
    },
  })

  if (!response.ok) {
    // Handle 401 by clearing auth and redirecting to login
    if (response.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      window.location.href = '/login'
      throw new Error('Session expired. Please log in again.')
    }

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
    include_archived?: boolean
  }): Promise<InvestmentListResponse> => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.per_page) query.set('per_page', String(params.per_page))
    if (params?.search) query.set('search', params.search)
    if (params?.sort_by) query.set('sort_by', params.sort_by)
    if (params?.sort_order) query.set('sort_order', params.sort_order)
    if (params?.include_archived) query.set('include_archived', String(params.include_archived))
    const queryString = query.toString()
    return fetchApi(`/investments${queryString ? `?${queryString}` : ''}`)
  },

  getInvestment: (id: string): Promise<InvestmentDetail> => {
    return fetchApi(`/investments/${id}`)
  },

  updateInvestment: (id: string, data: Partial<Investment>): Promise<InvestmentDetail> => {
    return fetchApi(`/investments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  exportCsv: async (): Promise<void> => {
    const response = await fetch(`${API_BASE}/investments/export/csv`, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        window.location.href = '/login'
        throw new Error('Session expired. Please log in again.')
      }
      throw new Error('Failed to export CSV')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'investments.csv'
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
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
  getDocument: (id: string): Promise<DocumentInfo> => {
    return fetchApi(`/documents/${id}`)
  },

  getDocumentMarkdown: (id: string): Promise<{ id: string; filename: string; markdown_content: string | null }> => {
    return fetchApi(`/documents/${id}/markdown`)
  },

  downloadDocumentPdf: async (id: string, filename: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/documents/${id}/download/pdf`, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        window.location.href = '/login'
        throw new Error('Session expired. Please log in again.')
      }
      throw new Error('Failed to download PDF')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  },

  downloadDocumentMarkdown: async (id: string, filename: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/documents/${id}/download/markdown`, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        window.location.href = '/login'
        throw new Error('Session expired. Please log in again.')
      }
      throw new Error('Failed to download markdown')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // Replace .pdf with .md for the filename
    a.download = filename.replace(/\.pdf$/i, '.md')
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  },

  // Gmail Connection
  exchangeGmailCode: (code: string, redirectUri: string): Promise<{ message: string }> => {
    return fetchApi('/auth/gmail/exchange', {
      method: 'POST',
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    })
  },

  disconnectGmail: (): Promise<{ message: string }> => {
    return fetchApi('/auth/gmail/disconnect', { method: 'DELETE' })
  },

  // User info
  getCurrentUser: (): Promise<{
    id: string
    email: string
    name: string | null
    picture_url: string | null
    has_gmail_connected: boolean
  }> => {
    return fetchApi('/auth/me')
  },
}
