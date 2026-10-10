import { useEffect, useState } from 'react'
import {
  Activity,
  Brain,
  CheckCircle2,
  Clock3,
  RefreshCw,
} from 'lucide-react'
import { Link } from 'react-router'
import { getTraceEvents } from '../services/api'
import type { DemoEvent } from '../services/demoState'

const eventIcons = {
  'Practice answer evaluated': CheckCircle2,
  'Weakness saved to Memory': Brain,
  'Learning plan replanned': RefreshCw,
}

function Trace() {
  const [events, setEvents] = useState<DemoEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isCurrent = true

    getTraceEvents()
      .then((savedEvents) => {
        if (isCurrent) setEvents([...savedEvents].reverse())
      })
      .catch(() => {
        if (isCurrent) setErrorMessage('Could not load Trace activity.')
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })

    return () => {
      isCurrent = false
    }
  }, [])

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Activity history
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Trace
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Follow the practice, Memory, and plan updates recorded in this browser.
        </p>
      </div>

      {isLoading && (
        <p className="mb-5 text-sm text-slate-400" role="status">
          Loading activity…
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

      {!isLoading && events.length === 0 && !errorMessage && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-start gap-4">
            <Activity size={22} className="mt-1 text-cyan-300" />
            <div>
              <h2 className="font-semibold text-white">No activity yet</h2>
              <p className="mt-2 text-sm text-slate-400">
                Submit a practice answer in Sim to start the demo flow.
              </p>
              <Link
                to="/sim"
                className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-cyan-300 hover:text-cyan-200"
              >
                Go to Sim
                <Activity size={15} />
              </Link>
            </div>
          </div>
        </section>
      )}

      {!isLoading && events.length > 0 && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50">
          <div className="border-b border-slate-800 px-5 py-4">
            <h2 className="font-semibold text-white">Demo activity</h2>
            <p className="mt-1 text-sm text-slate-400">
              {events.length} event{events.length === 1 ? '' : 's'} recorded
            </p>
          </div>

          <ol className="divide-y divide-slate-800">
            {events.map((event) => {
              const Icon =
                eventIcons[event.title as keyof typeof eventIcons] ?? Activity
              const date = new Date(event.occurredAt)
              const timeLabel = Number.isNaN(date.getTime())
                ? 'Time unavailable'
                : date.toLocaleString()

              return (
                <li key={event.id} className="flex gap-4 px-5 py-5">
                  <div className="mt-0.5 rounded-lg bg-cyan-300/10 p-2 text-cyan-300">
                    <Icon size={18} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-medium text-white">{event.title}</h3>
                      <span className="flex items-center gap-1.5 text-xs text-slate-500">
                        <Clock3 size={13} />
                        {timeLabel}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-400">
                      {event.detail}
                    </p>
                  </div>
                </li>
              )
            })}
          </ol>
        </section>
      )}
    </div>
  )
}

export default Trace