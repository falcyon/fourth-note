interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'info'
  text: string
}

const colors = {
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
}

export default function StatusBadge({ status, text }: StatusBadgeProps) {
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status]}`}>
      {text}
    </span>
  )
}
