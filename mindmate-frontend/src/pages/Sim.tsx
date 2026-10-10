import { useEffect, useState, type FormEvent } from 'react'
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Sparkles,
} from 'lucide-react'
import { Link } from 'react-router'
import {
  getDemoState,
  submitPracticeAnswer,
} from '../services/api'
import type { PracticeResult } from '../services/demoState'

function Sim() {
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState<PracticeResult | null>(null)
  const [isLoadingSavedResult, setIsLoadingSavedResult] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isCurrent = true

    getDemoState()
      .then((state) => {
        if (isCurrent) {
          setResult(state.latestPractice)
        }
      })
      .catch(() => {
        if (isCurrent) {
          setErrorMessage('Could not load the saved practice result.')
        }
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoadingSavedResult(false)
        }
      })

    return () => {
      isCurrent = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      const nextResult = await submitPracticeAnswer(answer)
      setResult(nextResult)
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Could not submit the answer.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Practice simulation
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Sim
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Answer a sample frontend question and review the practice feedback.
          This screen uses a mock service, not an AI or backend service.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-7">
        <div className="mb-5 flex items-start gap-4">
          <div className="rounded-xl bg-cyan-300/10 p-3 text-cyan-300">
            <Brain size={21} />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-cyan-300">
              Frontend interview practice
            </p>
            <h2 className="mt-2 text-lg font-semibold text-white">
              How would you investigate a slow React page?
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Describe the steps you would take and how you would check whether
              your changes improved performance.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <label
            htmlFor="practice-answer"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Your answer
          </label>
          <textarea
            id="practice-answer"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="Write your answer here..."
            required
            minLength={10}
            rows={7}
            className="w-full resize-y rounded-xl border border-slate-700 bg-slate-950/70 p-4 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-600 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/20"
          />

          {errorMessage && (
            <p className="mt-3 text-sm text-rose-300" role="alert">
              {errorMessage}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500">
              The mock service uses answer length to choose sample feedback.
            </p>
            <button
              type="submit"
              disabled={answer.trim().length < 10 || isSubmitting}
              className="rounded-lg bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSubmitting ? 'Evaluating…' : 'Submit answer'}
            </button>
          </div>
        </form>
      </section>

      {isLoadingSavedResult && (
        <p className="mt-5 text-sm text-slate-400" role="status">
          Loading saved practice result…
        </p>
      )}

      {result && !isLoadingSavedResult && (
        <section
          className="mt-6 rounded-2xl border border-cyan-300/20 bg-cyan-300/5 p-5 sm:p-7"
          aria-live="polite"
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-300">
                <CheckCircle2 size={18} />
                <span className="text-sm font-medium">Answer recorded</span>
              </div>
              <h2 className="mt-3 text-xl font-semibold text-white">
                Practice feedback
              </h2>
            </div>

            <div className="rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-center">
              <p className="text-xs text-slate-400">Demo score</p>
              <p className="mt-1 text-2xl font-semibold text-cyan-300">
                {result.score}
              </p>
            </div>
          </div>

          <p className="mt-4 text-sm leading-6 text-slate-300">
            {result.feedback}
          </p>

          <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber-300/20 bg-amber-300/5 p-4">
            <Sparkles size={18} className="mt-0.5 shrink-0 text-amber-300" />
            <div>
              <p className="text-sm font-medium text-amber-200">
                Practice area detected
              </p>
              <p className="mt-1 text-sm text-slate-300">{result.weakness}</p>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              to="/memory"
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2.5 text-sm font-medium text-slate-200 hover:bg-slate-800"
            >
              View Memory
              <ArrowRight size={16} />
            </Link>
            <Link
              to="/pipeline"
              className="inline-flex items-center gap-2 rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-200"
            >
              Continue to Pipeline
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      )}
    </div>
  )
}

export default Sim