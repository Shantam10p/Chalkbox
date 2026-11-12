import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import { AppBar, EmptyState, ListLink, Page, Skeleton, StatusBadge } from '../components/ui.jsx'
import { isBusy, shortDate } from '../lib/format.js'
import { usePolling } from '../lib/hooks.js'
import { canDeleteLesson, confirmAndDeleteLesson } from '../lib/lessons.js'

export default function PlanList() {
  const { current, refresh } = useClass()
  const toast = useToast()
  const [editing, setEditing] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const lessons = current?.lessons ?? []
  usePolling(refresh, lessons.some((l) => isBusy(l.status)))

  const remove = async (lesson) => {
    setDeletingId(lesson.id)
    try {
      if (await confirmAndDeleteLesson(lesson, current?.worksheets)) {
        toast('Plan deleted')
        const updated = await refresh()
        if (!updated?.lessons.length) setEditing(false)
      }
    } catch (e) {
      toast(e.message, 'error')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <AppBar
        title="Plan"
        subtitle="Lessons and worksheets"
        actions={
          lessons.length > 0 && (
            <button type="button" className="btn ghost small" onClick={() => setEditing((e) => !e)}>
              {editing ? 'Done' : 'Edit'}
            </button>
          )
        }
      />
      <Page roomy>
        {!editing && (
          <Link to="/plan/new" className="btn primary block">
            <Icon name="plus" /> New lesson
          </Link>
        )}

        {!current ? (
          <Skeleton />
        ) : lessons.length === 0 ? (
          <div className="card">
            <EmptyState icon="plan" title="No lessons yet">
              Tell ChalkBox the topic and it writes a full lesson plan and a worksheet you can print.
            </EmptyState>
          </div>
        ) : (
          <ul className="card flush list">
            {lessons.map((lesson) => (
              <li key={lesson.id}>
                {editing ? (
                  <div className="list-item" style={{ cursor: 'default' }}>
                    <div className="grow">
                      <div className="title ellipsis">{lesson.topic}</div>
                      <div className="meta">{lesson.subject} · {shortDate(lesson.created_at)}</div>
                    </div>
                    {canDeleteLesson(lesson) ? (
                      <button
                        type="button"
                        className="icon-btn danger-icon"
                        aria-label={`Delete ${lesson.topic}`}
                        disabled={deletingId === lesson.id}
                        onClick={() => remove(lesson)}
                      >
                        <Icon name="trash" />
                      </button>
                    ) : (
                      <StatusBadge status={lesson.status} />
                    )}
                  </div>
                ) : (
                  <ListLink
                    to={`/plan/${lesson.id}`}
                    title={lesson.topic}
                    meta={`${lesson.subject} · ${shortDate(lesson.created_at)}`}
                    trailing={<StatusBadge status={lesson.status} />}
                  />
                )}
              </li>
            ))}
          </ul>
        )}
        {editing && (
          <p className="small muted" style={{ textAlign: 'center' }}>
            Plans that are still being written can be deleted once they finish.
          </p>
        )}
      </Page>
    </>
  )
}
