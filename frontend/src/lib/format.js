// Display helpers shared by every screen.

export const STATUS = {
  queued: { label: 'Waiting', tone: 'neutral', busy: true },
  reading: { label: 'Reading handwriting', tone: 'info', busy: true },
  needs_review: { label: 'Needs your check', tone: 'warn' },
  grading: { label: 'Marking', tone: 'info', busy: true },
  graded: { label: 'Ready to approve', tone: 'warn' },
  running: { label: 'Writing', tone: 'info', busy: true },
  ready: { label: 'Ready to review', tone: 'warn' },
  approved: { label: 'Approved', tone: 'ok' },
  error: { label: 'Failed', tone: 'error' },
}

export const isBusy = (status) => Boolean(STATUS[status]?.busy)
export const needsTeacher = (status) => ['needs_review', 'graded', 'ready'].includes(status)

export function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  return (parts[0]?.[0] ?? '?').toUpperCase() + (parts[1]?.[0] ?? '').toUpperCase()
}

export function percent(ratio) {
  return ratio == null ? '–' : `${Math.round(ratio * 100)}%`
}

export function scoreText(sub) {
  return sub?.score_total ? `${sub.score_correct ?? 0}/${sub.score_total}` : '–'
}

export function scoreRatio(sub) {
  return sub?.score_total ? (sub.score_correct ?? 0) / sub.score_total : null
}

// Model output can arrive as a string or a list; always give the UI a list.
export function asList(value) {
  if (Array.isArray(value)) return value.filter((v) => v != null && String(v).trim() !== '')
  if (value == null || value === '') return []
  return [value]
}

export function shortDate(value) {
  if (!value) return ''
  const date = new Date(value.replace(' ', 'T') + (value.includes('Z') ? '' : 'Z'))
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

export const QUESTION_TYPE_LABEL = {
  number: 'Number',
  choice: 'Multiple choice',
  text: 'Exact word',
  short_answer: 'Written answer',
}

export const GRADED_BY_LABEL = {
  code: 'Checked exactly',
  ai: 'Marked by AI',
  teacher: 'Set by you',
  ai_pending: 'Waiting for AI',
}
