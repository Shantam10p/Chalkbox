import { api } from '../api.js'
import { isBusy } from './format.js'

export const canDeleteLesson = (lesson) => !isBusy(lesson.status)

// Asks the teacher to confirm, then deletes the plan. Returns true if it was deleted.
// `worksheets` (from the class) tells us whether student work was already checked.
export async function confirmAndDeleteLesson(lesson, worksheets = []) {
  const worksheet = worksheets.find((w) => w.id === lesson.worksheet_id)
  const checkedWork = (worksheet?.submission_count ?? 0) > 0
  const consequence = !lesson.worksheet_id
    ? 'This cannot be undone.'
    : checkedWork
      ? "Students' checked worksheets and results will be kept. This cannot be undone."
      : 'Its worksheet will be deleted too. This cannot be undone.'

  if (!window.confirm(`Delete the plan “${lesson.topic}”?\n\n${consequence}`)) return false
  await api.deleteLesson(lesson.id)
  return true
}
