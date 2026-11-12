import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import SignOutButton from '../components/SignOutButton.jsx'
import { AppBar, ErrorState, Greeting, ListLink, Page, Skeleton, StatusBadge } from '../components/ui.jsx'
import { isBusy, needsTeacher } from '../lib/format.js'
import { useLoad, usePolling } from '../lib/hooks.js'

// "Today": what needs the teacher right now, plus the two main actions.
async function loadTodo(classInfo) {
  const [reports, perWorksheet] = await Promise.all([
    api.reports(classInfo.id),
    Promise.all(
      classInfo.worksheets.map(async (w) => ({
        worksheet: w,
        submissions: await api.submissions(w.id),
        practice: await api.practiceSheets(w.id),
      })),
    ),
  ])

  const items = []
  let working = 0
  for (const { worksheet, submissions, practice } of perWorksheet) {
    const review = submissions.filter((s) => s.status === 'needs_review').length
    const approve = submissions.filter((s) => s.status === 'graded').length
    working += submissions.filter((s) => isBusy(s.status)).length + practice.filter((p) => isBusy(p.status)).length
    if (review) items.push({ key: `r${worksheet.id}`, to: `/check/${worksheet.id}`, icon: 'alert', title: `Check ${review} unclear answer sheet${review > 1 ? 's' : ''}`, meta: worksheet.title, status: 'needs_review' })
    if (approve) items.push({ key: `a${worksheet.id}`, to: `/check/${worksheet.id}`, icon: 'check', title: `Approve ${approve} marked sheet${approve > 1 ? 's' : ''}`, meta: worksheet.title, status: 'graded' })
    const sheets = practice.filter((p) => p.status === 'ready').length
    if (sheets) items.push({ key: `p${worksheet.id}`, to: `/class/worksheets/${worksheet.id}/practice`, icon: 'book', title: `Review ${sheets} practice sheet${sheets > 1 ? 's' : ''}`, meta: worksheet.title, status: 'ready' })
  }
  for (const lesson of classInfo.lessons.filter((l) => needsTeacher(l.status))) {
    items.push({ key: `l${lesson.id}`, to: `/plan/${lesson.id}`, icon: 'plan', title: 'Approve lesson plan', meta: lesson.topic, status: lesson.status })
  }
  working += classInfo.lessons.filter((l) => isBusy(l.status)).length + reports.filter((r) => isBusy(r.status)).length
  const notes = reports.filter((r) => r.status === 'ready').length
  if (notes) items.push({ key: 'reports', to: '/reports', icon: 'report', title: `Approve ${notes} parent note${notes > 1 ? 's' : ''}`, status: 'ready' })

  return { items, working }
}

export default function Home() {
  const { current, classes, classId, setClassId, error: classError } = useClass()
  const todo = useLoad(() => (current ? loadTodo(current) : null), current)
  usePolling(todo.reload, Boolean(todo.data?.working))

  const teacher = current?.teacher ?? 'teacher'

  return (
    <>
      <AppBar
        title={<span className="brand">ChalkBox</span>}
        actions={
          <>
            {classes?.length > 1 && (
              <select
                className="select"
                style={{ width: 'auto', minHeight: 40 }}
                value={classId ?? ''}
                onChange={(e) => setClassId(Number(e.target.value))}
                aria-label="Class"
              >
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            )}
            <SignOutButton />
          </>
        }
      />
      <Page>
        {classError && <ErrorState message={`Can't reach the ChalkBox hub: ${classError}`} />}

        <Greeting
          title={`Hello, ${teacher}`}
          meta={current ? `${current.name} · ${current.students.length} students` : 'Loading your class…'}
        />

        <div className="grid-2">
          <Link to="/plan/new" className="big-action" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
            <span className="ba-icon"><Icon name="plan" /></span>
            <span>
              <span className="ba-title">Plan a lesson</span>
              <span className="ba-sub" style={{ display: 'block' }}>Lesson + worksheet</span>
            </span>
          </Link>
          <Link to="/check" className="big-action" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
            <span className="ba-icon"><Icon name="camera" /></span>
            <span>
              <span className="ba-title">Check work</span>
              <span className="ba-sub" style={{ display: 'block' }}>Photograph sheets</span>
            </span>
          </Link>
        </div>

        <h2 className="section-title">Needs you</h2>
        {!current || todo.loading ? (
          <Skeleton count={2} />
        ) : todo.error ? (
          <ErrorState message={todo.error} onRetry={todo.reload} />
        ) : todo.data?.items.length ? (
          <ul className="card flush list">
            {todo.data.items.map((item) => (
              <li key={item.key}>
                <ListLink
                  to={item.to}
                  leading={<span className="avatar"><Icon name={item.icon} size={20} /></span>}
                  title={item.title}
                  meta={item.meta}
                />
              </li>
            ))}
          </ul>
        ) : (
          <div className="card">
            <p className="muted">You're all caught up. Nothing is waiting for your approval.</p>
          </div>
        )}

        {todo.data?.working > 0 && (
          <div className="card row">
            <StatusBadge status="running" />
            <span className="small muted">
              ChalkBox is working on {todo.data.working} item{todo.data.working > 1 ? 's' : ''}. This page updates by itself.
            </span>
          </div>
        )}
      </Page>
    </>
  )
}
