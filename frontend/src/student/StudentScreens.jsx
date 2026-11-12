import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAuth } from '../components/AuthContext.jsx'
import Icon from '../components/Icon.jsx'
import SignOutButton from '../components/SignOutButton.jsx'
import {
  AppBar, Avatar, EmptyState, ErrorState, ListLink, Loading, Page, ScoreRing, Skeleton, Stat,
} from '../components/ui.jsx'
import { percent, shortDate } from '../lib/format.js'
import { useLoad } from '../lib/hooks.js'

// What a student sees: their own checked work (after the teacher approved it),
// practice sheets made for them, and their progress. Answers to practice are hidden.

const TREND = {
  improving: { label: 'Getting better', tone: 'ok' },
  slipping: { label: 'Needs a little more practice', tone: 'warn' },
  steady: { label: 'Steady', tone: 'info' },
}

export function StudentHome() {
  const { user } = useAuth()
  const overview = useLoad(() => api.myOverview(), 'overview')
  const work = useLoad(() => api.myWork(), 'work')

  return (
    <>
      <AppBar title={<span className="brand">ChalkBox</span>} actions={<SignOutButton />} />
      <Page>
        <section className="hero">
          <Icon name="wifiOff" size={20} title="Works without internet" />
          <h2>Hi, {user.display_name}!</h2>
          <p>
            {overview.data
              ? `${overview.data.class.name} · ${overview.data.class.teacher}'s class`
              : 'Loading…'}
          </p>
        </section>

        <h2 className="section-title">My checked work</h2>
        {work.error ? (
          <ErrorState message={work.error} onRetry={work.reload} />
        ) : !work.data ? (
          <Skeleton count={2} />
        ) : work.data.length === 0 ? (
          <div className="card">
            <EmptyState icon="plan" title="Nothing yet">
              When your teacher checks your worksheets, they appear here with your feedback.
            </EmptyState>
          </div>
        ) : (
          <ul className="card flush list">
            {work.data.map((w) => (
              <li key={w.id}>
                <ListLink
                  to={`/work/${w.id}`}
                  leading={<span className="avatar"><Icon name="check" size={20} /></span>}
                  title={w.title}
                  meta={`${w.subject} · ${shortDate(w.created_at)}`}
                  trailing={<span className="badge">{w.score_correct}/{w.score_total}</span>}
                />
              </li>
            ))}
          </ul>
        )}
      </Page>
    </>
  )
}

export function StudentWork() {
  const { submissionId } = useParams()
  const { data, error, reload } = useLoad(() => api.myWorkDetail(submissionId), submissionId)
  const [showPhoto, setShowPhoto] = useState(false)

  if (error) return (<><AppBar title="My work" back="/" /><Page><ErrorState message={error} onRetry={reload} /></Page></>)
  if (!data) return (<><AppBar title="My work" back="/" /><Loading /></>)

  return (
    <>
      <AppBar title={data.title} subtitle={shortDate(data.date)} back="/" />
      <Page>
        <div className="card row" style={{ gap: 16 }}>
          <ScoreRing correct={data.score_correct ?? 0} total={data.score_total ?? 0} />
          <div className="grow stack" style={{ gap: 4 }}>
            <b>{data.score_correct === data.score_total ? 'All correct! 🎉' : 'Here is how you did'}</b>
            <span className="small muted">{data.subject}</span>
          </div>
        </div>

        {data.feedback && (
          <section className="card stack">
            <div className="card-title" style={{ marginBottom: 0 }}><Icon name="sparkle" /> From your teacher</div>
            <p className="pre">{data.feedback}</p>
          </section>
        )}

        <div className="card flush">
          {data.answers.map((a) => (
            <div className="q-row" key={a.question_no}>
              <div className="q-head">
                <span className={`q-num ${a.correct ? 'ok' : 'bad'}`} aria-label={a.correct ? 'Correct' : 'Not quite'}>
                  <Icon name={a.correct ? 'check' : 'cross'} size={18} />
                </span>
                <div className="grow stack" style={{ gap: 6 }}>
                  <span className="small muted">Question {a.question_no} · {a.question}</span>
                  <div className="answer-pair">
                    <span>You wrote: <b>{a.your_answer || '(blank)'}</b></span>
                    {a.correct_answer && <span className="muted">Answer: <b>{a.correct_answer}</b></span>}
                  </div>
                </div>
              </div>
              {(a.mistake || a.explanation) && (
                <div className="why">
                  {a.mistake && <b style={{ display: 'block' }}>{a.mistake}</b>}
                  {a.explanation}
                </div>
              )}
            </div>
          ))}
        </div>

        <button type="button" className="btn block" onClick={() => setShowPhoto((s) => !s)}>
          <Icon name="image" /> {showPhoto ? 'Hide my worksheet' : 'See my worksheet'}
        </button>
        {showPhoto && (
          <div className="photo-frame">
            <img src={api.myWorkImageUrl(data.id)} alt="Photo of your worksheet" />
          </div>
        )}
      </Page>
    </>
  )
}

export function StudentPractice() {
  const { data, error, reload } = useLoad(() => api.myPractice(), 'practice')

  return (
    <>
      <AppBar title="Practice" subtitle="Made just for you" actions={<SignOutButton />} />
      <Page>
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data ? (
          <Skeleton count={2} />
        ) : data.length === 0 ? (
          <div className="card">
            <EmptyState icon="book" title="No practice yet">
              Your teacher will send practice here after checking your work.
            </EmptyState>
          </div>
        ) : (
          data.map((sheet, index) => (
            <details className="card disclosure" key={sheet.id} open={index === 0}>
              <summary>
                <span className="grow">
                  <span className="strong" style={{ display: 'block' }}>{sheet.title}</span>
                  <span className="tiny muted">{shortDate(sheet.created_at)}</span>
                </span>
                <Icon name="chevron" size={18} className="chev" />
              </summary>
              <div className="stack" style={{ marginTop: 10 }}>
                {sheet.content?.intro && <p className="small" style={{ fontStyle: 'italic' }}>{sheet.content.intro}</p>}
                <ol className="practice-list">
                  {(sheet.content?.questions ?? []).map((q) => (
                    <li key={q.number}>
                      <span>{q.text}</span>
                      {q.type === 'choice' && q.options?.length > 0 && (
                        <span className="small muted" style={{ display: 'block' }}>{q.options.join('   ')}</span>
                      )}
                    </li>
                  ))}
                </ol>
                <p className="tiny muted">Work these out on paper, then show your teacher.</p>
              </div>
            </details>
          ))
        )}
      </Page>
    </>
  )
}

export function StudentProgress() {
  const { user } = useAuth()
  const { data, error, reload } = useLoad(() => api.myProgress(), 'progress')
  const trend = TREND[data?.trend]

  return (
    <>
      <AppBar title="My progress" actions={<SignOutButton />} />
      <Page>
        <div className="card row" style={{ gap: 14 }}>
          <Avatar name={user.display_name} large />
          <div className="grow stack" style={{ gap: 4 }}>
            <b style={{ fontSize: '1.1rem' }}>{user.display_name}</b>
            {trend && <span className={`badge ${trend.tone}`} style={{ width: 'fit-content' }}>{trend.label}</span>}
          </div>
        </div>

        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data ? (
          <Skeleton count={2} />
        ) : data.history.length === 0 ? (
          <div className="card">
            <EmptyState icon="chart" title="No scores yet">
              Your progress shows up here after your teacher checks your work.
            </EmptyState>
          </div>
        ) : (
          <>
            <div className="grid-2">
              <Stat value={percent(data.average)} label="Average score" />
              <Stat value={data.history.length} label="Worksheets" />
            </div>

            <section className="card stack">
              <div className="card-title" style={{ marginBottom: 0 }}><Icon name="sparkle" /> Things to practise</div>
              {data.top_mistakes.length === 0 ? (
                <p className="small muted">Nothing keeps tripping you up. Great job! 🎉</p>
              ) : (
                data.top_mistakes.map((m) => <p className="small" key={m.id}>• {m.description}</p>)
              )}
            </section>

            <h2 className="section-title">Scores</h2>
            <ul className="card flush list">
              {[...data.history].reverse().map((h) => (
                <li key={h.submission_id}>
                  <ListLink
                    to={`/work/${h.submission_id}`}
                    title={h.title}
                    meta={shortDate(h.date)}
                    trailing={<span className="badge">{h.score}</span>}
                  />
                </li>
              ))}
            </ul>
          </>
        )}
      </Page>
    </>
  )
}
