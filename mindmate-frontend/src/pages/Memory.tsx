import { useEffect, useState } from 'react'
import {
  Brain,
  CheckCircle2,
  Clock3,
  Lightbulb,
  Save,
  Target,
} from 'lucide-react'
import {
  getDemoState,
  saveWeaknessToMemoryApi,
} from '../services/api'
import type { DemoState } from '../services/demoState'

const sampleMemories = [
  {
    title: 'React component composition',
    category: 'Frontend',
    detail: 'You are comfortable splitting interfaces into reusable components.',
    strength: 78,
    icon: CheckCircle2,
    color: 'text-emerald-300',
  },
  {
    title: 'Explaining asynchronous code',
    category: 'JavaScript',
    detail: 'Practice explaining promises and async/await in your own words.',
    strength: 46,
    icon: Lightbulb,
    color: 'text-amber-300',
  },
  {
    title: 'Accessible form controls',
    category: 'Accessibility',
    detail: 'Review labels, keyboard focus, and helpful validation messages.',
    strength: 35,
    icon: Target,
    color: 'text-violet-300',
  },
]

function Memory() {
  const [demoState, setDemoState] = useState<DemoState | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isCurrent = true

    getDemoState()
      .then((state) => {
        if (isCurrent) setDemoState(state)
      })
      .catch(() => {
        if (isCurrent) setErrorMessage('Could not load Memory data.')
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })

    return () => {
      isCurrent = false
    }
  }, [])

  const latestPractice = demoState?.latestPractice ?? null
  const weaknessNote = latestPractice
    ? `Practice focus: ${latestPractice.weakness}`
    : null
  const isSaved =
    weaknessNote !== null &&
    (demoState?.memoryNotes.includes(weaknessNote) ?? false)

  async function handleSaveWeakness() {
    setIsSaving(true)
    setErrorMessage(null)

    try {
      const updatedState = await saveWeaknessToMemoryApi()
      setDemoState(updatedState)
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Could not save the practice area.',
      )
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Learning record
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Memory
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Review learning notes and save practice areas for later. This demo
          stores data in your browser through the mock service.
        </p>
      </div>

      {isLoading && (
        <p className="mb-5 text-sm text-slate-400" role="status">
          Loading Memory…
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

      {latestPractice && (
        <section
          className="mb-6 rounded-2xl border border-amber-300/20 bg-amber-300/5 p-5 sm:p-6"
          aria-live="polite"
        >
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-amber-300/10 p-3 text-amber-300">
              <Lightbulb size={20} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-300">
                New practice insight
              </p>
              <h2 className="mt-2 text-lg font-semibold text-white">
                {latestPractice.weakness}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                {latestPractice.feedback}
              </p>

              <button
                type="button"
                onClick={handleSaveWeakness}
                disabled={isSaved || isSaving || isLoading}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-amber-300 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-amber-200 disabled:cursor-default disabled:opacity-70"
              >
                {isSaved ? <CheckCircle2 size={16} /> : <Save size={16} />}
                {isSaving
                  ? 'Saving…'
                  : isSaved
                    ? 'Saved to Memory'
                    : 'Save weakness to Memory'}
              </button>
            </div>
          </div>
        </section>
      )}

      <section className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3 text-cyan-300">
            <Brain size={19} />
            <p className="text-sm text-slate-400">Memory records</p>
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">
            {sampleMemories.length + (demoState?.memoryNotes.length ?? 0)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Includes sample and saved notes
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3 text-emerald-300">
            <CheckCircle2 size={19} />
            <p className="text-sm text-slate-400">Strong area</p>
          </div>
          <p className="mt-4 text-xl font-semibold text-white">React</p>
          <p className="mt-1 text-xs text-slate-500">Component composition</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3 text-amber-300">
            <Clock3 size={19} />
            <p className="text-sm text-slate-400">Saved practice notes</p>
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">
            {demoState?.memoryNotes.length ?? 0}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            From your practice sessions
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/50">
        <div className="border-b border-slate-800 px-5 py-4">
          <h2 className="font-semibold text-white">Learning notes</h2>
          <p className="mt-1 text-sm text-slate-400">
            Example records and any practice notes you save.
          </p>
        </div>

        <div className="divide-y divide-slate-800">
          {(demoState?.memoryNotes ?? []).map((note) => (
            <article key={note} className="flex items-start gap-4 px-5 py-5">
              <CheckCircle2 size={20} className="mt-0.5 text-emerald-300" />
              <div>
                <p className="font-medium text-white">{note}</p>
                <p className="mt-1 text-sm text-slate-400">
                  Saved from a MINDMATE practice session.
                </p>
              </div>
            </article>
          ))}

          {sampleMemories.map((memory) => {
            const Icon = memory.icon

            return (
              <article key={memory.title} className="px-5 py-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <Icon size={20} className={`mt-0.5 ${memory.color}`} />
                    <div>
                      <p className="font-medium text-white">{memory.title}</p>
                      <p className="mt-1 text-xs font-medium text-cyan-300">
                        {memory.category}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-400">
                        {memory.detail}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-medium text-slate-300">
                    {memory.strength}% strength
                  </span>
                </div>

                <div className="ml-9 mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-300"
                    style={{ width: `${memory.strength}%` }}
                  />
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default Memory