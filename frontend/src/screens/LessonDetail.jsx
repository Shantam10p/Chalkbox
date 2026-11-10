import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import QuestionList from '../components/Questions.jsx'
import { useToast } from '../components/Toast.jsx'
import { ActionBar, AppBar, ErrorState, Loading, Notice, Page, Spinner, StatusBadge } from '../components/ui.jsx'
import { asList, isBusy } from '../lib/format.js'
import { useAction, useLoad, usePolling } from '../lib/hooks.js'

function Part({ number, title, minutes, fix = false, children }) {
  return (
    <section className={`lesson-part${fix ? ' fix' : ''}`}>
      <h3>
        <span className="q-num">{number}</span>
        <span className="grow">{title}</span>
        {minutes > 0 && <span className="badge">{minutes} min</span>}
      </h3>
      {children}
    </section>
  )
}

function Bullets({ items, ordered = false }) {
  const list = asList(items)
  if (!list.length) return null
  const Tag = ordered ? 'ol' : 'ul'
  return <Tag>{list.map((item, i) => <li key={i}>{String(item)}</li>)}</Tag>
}

function LessonPlan({ lesson }) {
  const timing = lesson.timing ?? {}
  const teach = lesson.teach ?? {}
  const notes = lesson.teacher_notes ?? {}
  const fix = lesson.fix_yesterday
  return (
    <div className="card stack" style={{ gap: 18 }}>
      <Part number={1} title="Goal">
        <p>{lesson.goal}</p>
      </Part>
      {fix && (
        <Part number={2} title="Fix yesterday" minutes={timing.fix_yesterday} fix>
          {fix.mistake && <p className="small"><b>Mistake:</b> {fix.mistake}</p>}
          <Bullets items={fix.steps} ordered />
        </Part>
      )}
      <Part number={fix ? 3 : 2} title="Teach (I do)" minutes={timing.teach}>
        {teach.explanation && <p>{teach.explanation}</p>}
        {asList(teach.examples).length > 0 && <p className="small strong">Examples</p>}
        <Bullets items={teach.examples} />
        {asList(teach.watch_for).length > 0 && <p className="small strong">Watch for</p>}
        <Bullets items={teach.watch_for} />
      </Part>
      <Part number={fix ? 4 : 3} title="Practice together (we do)" minutes={timing.practice_together}>
        <Bullets items={lesson.practice_together} />
      </Part>
      <Part number={fix ? 5 : 4} title="Practice alone (you do)" minutes={timing.practice_alone}>
        <p>{lesson.practice_alone || 'Students complete the worksheet below.'}</p>
      </Part>
      <Part number={fix ? 6 : 5} title="Teacher notes">
        {asList(notes.materials).length > 0 && <p className="small"><b>Materials:</b> {asList(notes.materials).join(', ')}</p>}
        {asList(notes.local_language_words).length > 0 && (
          <p className="small"><b>Local words:</b> {asList(notes.local_language_words).join(', ')}</p>
        )}
        <Bullets items={notes.tips} />
      </Part>
    </div>
  )
}

export default function LessonDetail() {
  const { lessonId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { refresh } = useClass()
  const { data: lesson, error, reload } = useLoad(() => api.lesson(lessonId), lessonId)
  usePolling(reload, isBusy(lesson?.status), 4000)

  const [approve, approving] = useAction(async () => {
    try {
      const result = await api.approveLesson(lessonId)
      toast('Lesson approved. The worksheet is ready to print.')
      await Promise.all([reload(), refresh()])
      return result
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  const [retry, retrying] = useAction(async () => {
    try {
      await api.retryLesson(lessonId)
      await reload()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  if (error) return (<><AppBar title="Lesson" back="/plan" /><Page><ErrorState message={error} onRetry={reload} /></Page></>)
  if (!lesson) return (<><AppBar title="Lesson" back="/plan" /><Loading /></>)

  const content = lesson.content
  const problems = content?.problems ?? []

  return (
    <>
      <AppBar title={lesson.topic} subtitle={lesson.subject} back="/plan" actions={<StatusBadge status={lesson.status} />} />
      <Page hasAction={lesson.status === 'ready' || lesson.status === 'approved'}>
        {isBusy(lesson.status) && (
          <div className="card stack" style={{ justifyItems: 'center', textAlign: 'center', padding: 28 }}>
            <div className="spinner lg" />
            <h2 style={{ fontSize: '1.1rem' }}>Writing your lesson…</h2>
            <p className="muted small">
              ChalkBox is writing the lesson plan and worksheet, then checking every answer. This can take a few minutes. You can leave this page.
            </p>
          </div>
        )}

        {lesson.status === 'error' && (
          <ErrorState message={lesson.error || 'Something went wrong while writing the lesson.'} onRetry={retrying ? undefined : retry} />
        )}

        {content?.lesson && (
          <>
            <h2 className="section-title">Lesson plan</h2>
            <LessonPlan lesson={content.lesson} />

            <div className="spread">
              <h2 className="section-title">Worksheet · {content.worksheet.questions.length} questions</h2>
            </div>
            {problems.length > 0 && (
              <Notice tone="warn" icon="check">
                <div className="stack" style={{ gap: 4 }}>
                  <b>Code checked the answers</b>
                  {problems.map((p, i) => <span key={i} className="small">{p}</span>)}
                </div>
              </Notice>
            )}
            <QuestionList questions={content.worksheet.questions} />
          </>
        )}
      </Page>

      {lesson.status === 'ready' && (
        <ActionBar>
          <button type="button" className="btn primary" onClick={approve} disabled={approving}>
            {approving ? <Spinner /> : <Icon name="check" />} Approve lesson
          </button>
        </ActionBar>
      )}
      {lesson.status === 'approved' && lesson.worksheet_id && (
        <ActionBar>
          <Link className="btn" to={`/print/worksheet/${lesson.worksheet_id}`}>
            <Icon name="print" /> Print
          </Link>
          <button type="button" className="btn primary" onClick={() => navigate(`/check/${lesson.worksheet_id}`)}>
            <Icon name="camera" /> Check work
          </button>
        </ActionBar>
      )}
    </>
  )
}
