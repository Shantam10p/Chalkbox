import { QUESTION_TYPE_LABEL } from '../lib/format.js'

// Read-only list of worksheet questions with their answers (used in lesson and practice previews).
export default function QuestionList({ questions = [], showAnswers = true }) {
  return (
    <div className="card flush">
      {questions.map((q) => (
        <div className="q-row" key={q.number}>
          <div className="q-head">
            <span className="q-num">{q.number}</span>
            <div className="grow stack" style={{ gap: 4 }}>
              <span>{q.text}</span>
              {q.type === 'choice' && q.options?.length > 0 && (
                <span className="small muted">{q.options.join('   ')}</span>
              )}
              <div className="row wrap" style={{ gap: 6 }}>
                <span className="badge">{QUESTION_TYPE_LABEL[q.type] ?? q.type}</span>
                {q.verified === true && <span className="badge ok">Answer checked by code</span>}
                {q.verified === false && <span className="badge warn">Please check this answer</span>}
              </div>
            </div>
          </div>
          {showAnswers && (q.answer || q.rubric) && (
            <div className="why">
              {q.answer ? (
                <>
                  Answer: <b>{q.answer}</b>
                </>
              ) : (
                <>Marking guide: {q.rubric}</>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
