import { useState, useRef, useEffect } from 'react'

const TOKEN_KEY = 'fourth_note_token'

export interface ProgressEvent {
  step: string
  message: string
  details: Record<string, unknown>
  timestamp: string
}

interface TriggerButtonProps {
  onComplete?: () => void
  onProgress?: (event: ProgressEvent) => void
}

export default function TriggerButton({ onComplete, onProgress }: TriggerButtonProps) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<ProgressEvent[]>([])
  const [showProgress, setShowProgress] = useState(false)
  const [finalResult, setFinalResult] = useState<{ status: string; message: string } | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const progressContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll progress panel to show latest entry
  useEffect(() => {
    if (progressContainerRef.current) {
      progressContainerRef.current.scrollTop = progressContainerRef.current.scrollHeight
    }
  }, [progress])

  const handleClick = async () => {
    setLoading(true)
    setProgress([])
    setShowProgress(true)
    setFinalResult(null)

    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      setFinalResult({
        status: 'error',
        message: 'Not authenticated',
      })
      return
    }

    // Use fetch with streaming for SSE with auth headers
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      const response = await fetch('/api/v1/trigger/fetch-emails/stream', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        signal: abortController.signal,
      })

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem('fourth_note_user')
          window.location.href = '/login'
          return
        }
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          setLoading(false)
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: ProgressEvent = JSON.parse(line.slice(6))
              setProgress(prev => [...prev, data])

              // Notify parent of progress (for real-time updates)
              if (onProgress) {
                onProgress(data)
              }

              if (data.step === 'complete' || data.step === 'error') {
                setLoading(false)
                setFinalResult({
                  status: data.step === 'complete' ? 'success' : 'error',
                  message: data.message,
                })
                if (data.step === 'complete' && onComplete) {
                  onComplete()
                }
                reader.cancel()
                return
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setLoading(false)
        setFinalResult({
          status: 'error',
          message: err instanceof Error ? err.message : 'Connection lost',
        })
      }
    }
  }

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'gmail': return '📧'
      case 'fetch': return '📥'
      case 'pdf': return '📄'
      case 'ocr': return '🔍'
      case 'convert': return '📝'
      case 'processing': return '⚙️'
      case 'extraction': return '🤖'
      case 'complete': return '✅'
      case 'error': return '❌'
      default: return '•'
    }
  }

  const getStepColor = (step: string) => {
    switch (step) {
      case 'complete': return 'text-green-600'
      case 'error': return 'text-red-600'
      default: return 'text-gray-700'
    }
  }

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        disabled={loading}
        className={`
          px-4 py-2 rounded-md font-medium transition-colors
          ${loading
            ? 'bg-blue-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
          }
        `}
      >
        {loading ? (
          <span className="flex items-center">
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Processing...
          </span>
        ) : (
          'Fetch Emails'
        )}
      </button>

      {/* Progress Panel */}
      {showProgress && (
        <div className="absolute top-full right-0 mt-2 w-96 max-h-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 flex flex-col">
          <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-2 flex justify-between items-center">
            <span className="font-medium text-gray-700">
              {loading ? 'Processing...' : (finalResult?.status === 'success' ? 'Complete' : 'Failed')}
            </span>
            {!loading && (
              <button
                onClick={() => setShowProgress(false)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            )}
          </div>

          <div ref={progressContainerRef} className="p-3 space-y-1 flex-1 overflow-y-auto">
            {progress.map((event, idx) => (
              <div key={idx} className={`text-sm flex items-start gap-2 ${getStepColor(event.step)}`}>
                <span className="flex-shrink-0">{getStepIcon(event.step)}</span>
                <div className="flex-1 min-w-0">
                  <span className="break-words">{event.message}</span>
                  {event.details && Object.keys(event.details).length > 0 && (
                    <div className="text-xs text-gray-500 mt-0.5">
                      {Object.entries(event.details).map(([key, value]) => (
                        <span key={key} className="mr-2">
                          {key}: <span className="font-medium">{String(value)}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Waiting for next update...</span>
              </div>
            )}
          </div>

          {finalResult && (
            <div className={`sticky bottom-0 px-4 py-2 border-t ${
              finalResult.status === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            }`}>
              <span className="font-medium">{finalResult.message}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
