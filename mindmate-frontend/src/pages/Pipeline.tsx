import { useEffect, useState } from 'react'
import {
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  GitCompareArrows,
  RefreshCw,
} from 'lucide-react'
import { Link } from 'react-router'
import {
  getDemoState,
  replanLearningPathApi,
} from '../services/api'
import type { DemoState } from '../services/demoState'

function Pipeline() {
  const [demoState, setDemoState] = useState<DemoState | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isReplanning, setIsReplanning] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isCurrent = true

    getDemoState()
      .then((state) => {
        if (isCurrent) setDemoState(state)
      })
      .catch(() => {
        if (isCurrent) setErrorMessage('Could not load the learning plan.')
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })

    return () => {
      isCurrent = false
    }
  }, [])

  const latestPractice = demoState?.latestPractice ?? null
  const requiredMemoryNote = latestPractice
    ? `Practice focus: ${latestPractice.weakness}`
    : null
  const weaknessSaved =
    requiredMemoryNote !== null &&
    (demoState?.memoryNotes.includes(requiredMemoryNote) ?? false)

  async function handleReplan() {
    setIsReplanning(true)
    setErrorMessage(null)

    try {
      const updatedState = await replanLearningPathApi()
      setDemoState(updatedState)
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Could not replan the path.',
      )
    } finally {
      setIsReplanning(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Learning plan
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Pipeline
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Review your sample plan and replan based on a weakness saved from
          practice.
        </p>
      </div>

      {isLoading && (
        <p className="mb-5 text-sm text-slate-400" role="status">
          Loading learning plan…
        </p>
      )}

      {errorMessage && (
        <p
          className="mb-5 rounded-lg border border-rose-400/20 bg-rose-400/5 p-3 text-sm text-rose-300"
          role="alert"
        >
          {errorMessage}
        </p>
      )}

      <section className="mb-6 flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          {weaknessSaved ? (
            <CheckCircle2 className="mt-0.5 text-emerald-300" size={20} />
          ) : (
            <CircleAlert className="mt-0.5 text-amber-300" size={20} />
          )}
          <div>
            <p className="font-medium text-white">
              {weaknessSaved
                ? 'Practice insight is ready'
                : 'Complete the practice flow first'}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              {weaknessSaved
                ? latestPractice?.weakness
                : 'Submit an answer in Sim, then save its weakness to Memory.'}
            </p>
          </div>
        </div>

        {!weaknessSaved && (
          <Link
            to={latestPractice ? '/memory' : '/sim'}
            className="inline-flex items-center gap-2 text-sm font-medium text-cyan-300 hover:text-cyan-200"
          >
            {latestPractice ? 'Go to Memory' : 'Go to Sim'}
            <ArrowRight size={16} />
          </Link>
        )}
      </section>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-cyan-300/10 p-3 text-cyan-300">
            <GitCompareArrows size={20} />
          </div>
          <div>
            <h2 className="font-semibold text-white">Plan comparison</h2>
            <p className="mt-1 text-sm text-slate-400">
              See how the practice insight changes the plan.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleReplan}
          disabled={!weaknessSaved || isReplanning || isLoading}
          className="inline-flex items-center gap-2 rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RefreshCw size={16} />
          {isReplanning
            ? 'Replanning…'
            : demoState?.updatedPlan
              ? 'Replan again'
              : 'Replan'}
        </button>
      </div>

      {demoState?.replanReason && (
        <section className="mb-5 rounded-xl border border-violet-300/20 bg-violet-300/5 p-4">
          <p className="text-sm font-semibold text-violet-200">
            Why the plan changed
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {demoState.replanReason}
          </p>
        </section>
      )}

      {demoState && (
        <div className="grid gap-4 lg:grid-cols-2">
          <PlanColumn
            title="Before"
            subtitle="Original sample plan"
            items={demoState.originalPlan}
            changed={false}
          />
          <PlanColumn
            title="After"
            subtitle={
              demoState.updatedPlan
                ? 'Revised sample plan'
                : 'Run Replan to update'
            }
            items={demoState.updatedPlan ?? demoState.originalPlan}
            changed={Boolean(demoState.updatedPlan)}
          />
        </div>
      )}
    </div>
  )
}

function PlanColumn({
  title,
  subtitle,
  items,
  changed,
}: {
  title: string
  subtitle: string
  items: string[]
  changed: boolean
}) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
      <div className="mb-5">
        <h3 className="font-semibold text-white">{title}</h3>
        <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
      </div>

      <ol className="space-y-3">
        {items.map((item, index) => (
          <li
            key={`${title}-${item}`}
            className={`flex gap-3 rounded-xl border p-4 ${
              changed
                ? 'border-cyan-300/20 bg-cyan-300/5'
                : 'border-slate-800 bg-slate-950/40'
            }`}
          >
            <span className="grid size-7 shrink-0 place-items-center rounded-full bg-slate-800 text-xs font-semibold text-slate-300">
              {index + 1}
            </span>
            <span className="text-sm leading-6 text-slate-200">{item}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}

export default Pipeline