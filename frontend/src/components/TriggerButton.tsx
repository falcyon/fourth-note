import { useState, useRef } from 'react'

interface ProgressEvent {
  step: string
  message: string
  details: Record<string, unknown>
  timestamp: string
}

interface TriggerButtonProps {
  onComplete?: () => void
}

export default function TriggerButton({ onComplete }: TriggerButtonProps) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<ProgressEvent[]>([])
  const [showProgress, setShowProgress] = useState(false)
  const [finalResult, setFinalResult] = useState<{ status: string; message: string } | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const handleClick = async () => {
    setLoading(true)
    setProgress([])
    setShowProgress(true)
    setFinalResult(null)

    // Use Server-Sent Events for real-time progress
    const eventSource = new EventSource('/api/v1/trigger/fetch-emails/stream')
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data: ProgressEvent = JSON.parse(event.data)
        setProgress(prev => [...prev, data])

        if (data.step === 'complete' || data.step === 'error') {
          eventSource.close()
          setLoading(false)
          setFinalResult({
            status: data.step === 'complete' ? 'success' : 'error',
            message: data.message,
          })
          if (data.step === 'complete' && onComplete) {
            onComplete()
          }
        }
      } catch (e) {
        console.error('Failed to parse SSE data:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setLoading(false)
      setFinalResult({
        status: 'error',
        message: 'Connection lost',
      })
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
        <div className="absolute top-full right-0 mt-2 w-96 max-h-96 overflow-y-auto bg-white rounded-lg shadow-xl border border-gray-200 z-50">
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

          <div className="p-3 space-y-1">
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
