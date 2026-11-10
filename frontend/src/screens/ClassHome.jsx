import { useState } from 'react'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { AppBar, Avatar, EmptyState, ListLink, Page, Skeleton } from '../components/ui.jsx'
import { shortDate } from '../lib/format.js'

export default function ClassHome() {
  const { current } = useClass()
  const [query, setQuery] = useState('')
  const students = (current?.students ?? []).filter((s) =>
    s.name.toLowerCase().includes(query.trim().toLowerCase()),
  )
  const worksheets = current?.worksheets ?? []

  return (
    <>
      <AppBar title={current?.name ?? 'Class'} subtitle={current ? `Grade ${current.grade} · ${current.teacher}` : ''} />
      <Page>
        {!current ? (
          <Skeleton count={4} />
        ) : (
          <>
            <h2 className="section-title">Results by worksheet</h2>
            {worksheets.length === 0 ? (
              <div className="card"><EmptyState icon="chart" title="No results yet">Check a worksheet to see the class picture.</EmptyState></div>
            ) : (
              <ul className="card flush list">
                {worksheets.map((w) => (
                  <li key={w.id}>
                    <ListLink
                      to={`/class/worksheets/${w.id}`}
                      leading={<span className="avatar"><Icon name="chart" size={20} /></span>}
                      title={w.title}
                      meta={`${w.submission_count} sheet${w.submission_count === 1 ? '' : 's'} · ${shortDate(w.created_at)}`}
                    />
                  </li>
                ))}
              </ul>
            )}

            <h2 className="section-title">Students · {current.students.length}</h2>
            <input
              className="input"
              type="search"
              placeholder="Search students"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search students"
            />
            <ul className="card flush list">
              {students.map((s) => (
                <li key={s.id}>
                  <ListLink to={`/class/students/${s.id}`} leading={<Avatar name={s.name} />} title={s.name} meta={s.language} />
                </li>
              ))}
              {students.length === 0 && <li className="list-item muted">No student matches “{query}”.</li>}
            </ul>
          </>
        )}
      </Page>
    </>
  )
}
