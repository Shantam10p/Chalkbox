import { Link } from 'react-router-dom'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { AppBar, EmptyState, ListLink, Page, Skeleton, StatusBadge } from '../components/ui.jsx'
import { isBusy, shortDate } from '../lib/format.js'
import { usePolling } from '../lib/hooks.js'

export default function PlanList() {
  const { current, refresh } = useClass()
  const lessons = current?.lessons ?? []
  usePolling(refresh, lessons.some((l) => isBusy(l.status)))

  return (
    <>
      <AppBar title="Plan" subtitle="Lessons and worksheets" />
      <Page>
        <Link to="/plan/new" className="btn primary block">
          <Icon name="plus" /> New lesson
        </Link>

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
                <ListLink
                  to={`/plan/${lesson.id}`}
                  title={lesson.topic}
                  meta={`${lesson.subject} · ${shortDate(lesson.created_at)}`}
                  trailing={<StatusBadge status={lesson.status} />}
                />
              </li>
            ))}
          </ul>
        )}
      </Page>
    </>
  )
}
