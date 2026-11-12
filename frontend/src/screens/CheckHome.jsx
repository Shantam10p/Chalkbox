import { Link } from 'react-router-dom'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { AppBar, EmptyState, ListLink, Page, Skeleton } from '../components/ui.jsx'
import { shortDate } from '../lib/format.js'

export default function CheckHome() {
  const { current } = useClass()
  const worksheets = current?.worksheets ?? []

  return (
    <>
      <AppBar title="Check work" subtitle="Pick the worksheet the class did" />
      <Page roomy>
        {!current ? (
          <Skeleton />
        ) : worksheets.length === 0 ? (
          <div className="card">
            <EmptyState
              icon="camera"
              title="No worksheets yet"
              action={<Link className="btn primary" to="/plan/new"><Icon name="plus" /> Plan a lesson</Link>}
            >
              Approve a lesson first. Its worksheet appears here, ready to check.
            </EmptyState>
          </div>
        ) : (
          <ul className="card flush list">
            {worksheets.map((w) => (
              <li key={w.id}>
                <ListLink
                  to={`/check/${w.id}`}
                  leading={<span className="avatar"><Icon name="plan" size={20} /></span>}
                  title={w.title}
                  meta={`${w.subject} · ${w.submission_count} sheet${w.submission_count === 1 ? '' : 's'} · ${shortDate(w.created_at)}`}
                />
              </li>
            ))}
          </ul>
        )}
      </Page>
    </>
  )
}
