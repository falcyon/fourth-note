import { NA_TEXT } from '../constants'

/**
 * Styled N/A indicator for missing field values.
 * Use inline for data fields, or call displayValue() for plain-text contexts (exports, tooltips).
 */
export default function MissingValue() {
  return (
    <span className="text-gray-500/70 italic text-xs border border-dashed border-gray-500/40 px-2 py-0.5 rounded">
      {NA_TEXT}
    </span>
  )
}

/** Returns the value if truthy, otherwise the N/A string. For plain-text contexts like markdown export. */
export function displayValue(value: string | null | undefined): string {
  return value || NA_TEXT
}
