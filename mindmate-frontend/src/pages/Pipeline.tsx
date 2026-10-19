import { useState } from 'react'
import {
  ArrowRight,
  BookOpen,
  CheckSquare,
  GraduationCap,
  Trophy,
} from 'lucide-react'
import { Link } from 'react-router'
import { getActivePlan, replanPlan, type ReplanResult } from '../services/backend'
import { useLoad } from '../hooks/useLoad'
import { RefTags, RefText } from '../components/RefText'

const stages = [
  {
    name: 'Study',
    description: 'Learn the topic',
    Icon: BookOpen,
    color: 'bg-[#2865e9]',
    halo: 'bg-[#e0f2fc]',
  },
  {
    name: 'Practice',
    description: 'Solve questions',
    Icon: GraduationCap,
    color: 'bg-[#10b981]',
    halo: 'bg-[#dcfce9]',
  },
  {
    name: 'Review',
    description: 'Check your notes',
    Icon: CheckSquare,
    color: 'bg-[#f59e0b]',
    halo: 'bg-[#fff1d7]',
  },
  {
    name: 'Mastery',
    description: 'Be exam-ready',
    Icon: Trophy,
    color: 'bg-[#8039ed]',
    halo: 'bg-[#eee8ff]',
  },
]

function taskStage(title: string) {
  const text = title.toLowerCase()
  if (/(mock interview|practice|drill|questions)/.test(text)) return 'Practice'
  if (/(review|revise|weekly review|summary|resume)/.test(text)) return 'Review'
  return 'Study'
}

function priorityClass(priority: string) {
  return priority === 'High' ? 'bg-rose-50 text-rose-700' : priority === 'Low' ? 'bg-slate-100 text-slate-600' : 'bg-amber-50 text-amber-700'
}

function Pipeline() {
  const plan = useLoad(getActivePlan)
  const [budget, setBudget] = useState(60)
  const [isReplanning, setIsReplanning] = useState(false)
  const [result, setResult] = useState<ReplanResult | null>(null)
  const [replanError, setReplanError] = useState<string | null>(null)

  async function handleReplan() {
    setIsReplanning(true)
    setReplanError(null)
    try {
      const next = await replanPlan(budget, budget < (plan.data?.daily_budget_minutes ?? 60) ? `only ${budget} minutes a day` : undefined)
      setResult(next)
      plan.setData(next.plan)
    } catch (error) {
      setReplanError(error instanceof Error ? error.message : 'Could not update your plan.')
    } finally {
      setIsReplanning(false)
    }
  }

  const tasks = (plan.data?.tasks ?? []).filter((task) => task.status !== 'deferred')
  const deferred = (plan.data?.tasks ?? []).filter((task) => task.status === 'deferred')
  const days = [...new Set(tasks.map((task) => task.day_number))].sort((a, b) => a - b)
  const movedTitles = new Set([...(result?.diff.moved ?? []), ...(result?.diff.added ?? [])].map((entry) => entry.title))
  const nextTask = tasks.find((task) => task.status === 'todo')
  const done = tasks.filter((task) => task.status === 'done').length
  const progress = tasks.length ? Math.round((done / tasks.length) * 100) : 0
  const stageCounts = stages.map((stage) => ({ ...stage, count: tasks.filter((task) => taskStage(task.title) === stage.name).length }))

  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-16 -top-[170px] -z-10 size-[250px] rounded-full bg-[#dff8f0] opacity-80"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff] opacity-80"
      />

      <section className="min-h-[529px] rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-[21px] font-bold leading-7 text-[#211e58]">Your Learning Pipeline</h2>
            {plan.data && (
              <p className="mt-1 text-[13px] text-[#626b9c]">
                Plan v{plan.data.version} · {tasks.length} tasks over 14 days · {plan.data.daily_budget_minutes} min per day
              </p>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label htmlFor="daily-budget" className="text-[13px] font-semibold text-[#211e58]">Time today</label>
            <select
              id="daily-budget"
              value={budget}
              onChange={(event) => setBudget(Number(event.target.value))}
              className="h-10 rounded-xl border border-violet-200 bg-white px-3 text-sm text-[#211e58] outline-none focus:border-violet-500"
            >
              {[60, 45, 30].map((minutes) => <option key={minutes} value={minutes}>{minutes} min / day</option>)}
            </select>
            <button
              type="button"
              onClick={handleReplan}
              disabled={isReplanning || plan.loading}
              className="inline-flex h-10 items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-500 px-4 text-sm font-semibold text-white shadow-sm hover:brightness-105 disabled:cursor-wait disabled:opacity-60"
            >
              {isReplanning ? 'Updating plan…' : 'Update my plan'}
            </button>
          </div>
        </div>

        {replanError && <p role="alert" className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{replanError}</p>}
        {plan.error && <p role="alert" className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">Could not load your plan: {plan.error}</p>}

        {result && (
          <section aria-live="polite" className="mb-4 rounded-xl border border-violet-200 bg-violet-50/70 p-4">
            <h3 className="font-semibold text-violet-900">What changed and why</h3>
            <p className="mt-1 text-sm leading-6 text-violet-900"><RefText text={result.rationale} /></p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-violet-100 bg-white p-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#7a80a7]">Before</h4>
                <ol className="mt-2 space-y-1 text-[13px] text-[#4b4f78]">
                  {result.diff.before.slice(0, 8).map((line) => <li key={`b-${line}`}>{line}</li>)}
                </ol>
              </div>
              <div className="rounded-xl border border-violet-100 bg-white p-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#7a80a7]">After</h4>
                <ol className="mt-2 space-y-1 text-[13px]">
                  {result.diff.after.slice(0, 8).map((line) => {
                    const changed = [...movedTitles].some((title) => line.endsWith(title))
                    return <li key={`a-${line}`} className={changed ? 'rounded-md bg-emerald-50 px-1 font-semibold text-emerald-800' : 'text-[#4b4f78]'}>{line}{changed ? ' ↑' : ''}</li>
                  })}
                </ol>
              </div>
            </div>
            {result.diff.deferred.length > 0 && (
              <p className="mt-3 text-[13px] text-amber-800">Deferred to keep within {result.daily_budget_minutes} min a day: {result.diff.deferred.map((entry) => entry.title).join('; ')}</p>
            )}
          </section>
        )}

        <section className="mb-5 rounded-[16px] border border-[#e3dcff] bg-[#fbfaff] p-4" aria-label="14-day plan">
          <h3 className="text-[16px] font-bold text-[#211e58]">Next 14 days</h3>
          {plan.loading && <p role="status" className="mt-3 text-sm text-[#626b9c]">Loading your plan…</p>}
          {!plan.loading && tasks.length === 0 && !plan.error && <p className="mt-3 text-sm text-[#626b9c]">No plan yet. Complete onboarding to generate one.</p>}
          <div className="mt-3 space-y-3">
            {days.map((day) => (
              <div key={day} className="grid gap-2 md:grid-cols-[86px_minmax(0,1fr)]">
                <div className="pt-2 text-[13px] font-bold text-[#211e58]">
                  Day {day}
                  <span className="block text-[11px] font-medium text-[#7a80a7]">{plan.data?.minutes_by_day[String(day)] ?? 0} / {plan.data?.daily_budget_minutes} min</span>
                </div>
                <ul className="space-y-2">
                  {tasks.filter((task) => task.day_number === day).map((task) => (
                    <li key={task.id} className={`rounded-xl border bg-white px-3 py-2 ${movedTitles.has(task.title) ? 'border-emerald-300' : 'border-[#ece8ff]'}`}>
                      <div className="flex flex-wrap items-center gap-2">
                        <strong className={`text-[13px] ${task.status === 'done' ? 'text-slate-400 line-through' : 'text-[#211e58]'}`}>{task.title}</strong>
                        <span className={`rounded-md px-1.5 py-[1px] text-[11px] font-semibold ${priorityClass(task.priority)}`}>{task.priority}</span>
                        <span className="text-[11px] text-[#7a80a7]">{task.minutes} min</span>
                        {task.must_keep && <span className="rounded-md bg-amber-100 px-1.5 py-[1px] text-[11px] font-semibold text-amber-800" title="Kept regardless of budget: tied to an active weakness or a hard deadline">must keep</span>}
                        <RefTags refs={task.refs} />
                      </div>
                      {task.why && <p className="mt-1 text-[12px] leading-5 text-[#626b9c]"><RefText text={task.why} /></p>}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          {deferred.length > 0 && <p className="mt-3 text-[12px] text-[#7a80a7]">Deferred beyond 14 days: {deferred.map((task) => task.title).join('; ')}</p>}
        </section>

        <div className="grid min-h-[233px] grid-cols-2 items-center gap-y-5 rounded-[16px] border border-[#cfe2ff] bg-[#f7fbff] px-3 py-5 sm:grid-cols-4 sm:gap-0 sm:px-5">
          {stageCounts.map(({ name, description, Icon, color, halo, count }, index) => (
            <div key={name} className="relative flex flex-col items-center text-center">
              {index > 0 && (
                <ArrowRight
                  aria-hidden="true"
                  className="absolute -left-1 top-[49px] hidden -translate-x-1/2 text-[#929bd1] sm:block"
                  size={20}
                  strokeWidth={1.8}
                />
              )}
              <div className={`grid size-[112px] place-items-center rounded-full ${halo}`}>
                <div className={`grid size-[64px] place-items-center rounded-[18px] ${color} text-white shadow-[0_5px_12px_rgba(58,66,130,0.14)]`}>
                  <Icon size={31} strokeWidth={1.8} />
                </div>
              </div>
              <h3 className="mt-3 text-[18px] font-bold leading-6 text-[#211e58]">
                {name}
              </h3>
              <p className="mt-1 text-[13px] leading-5 text-[#626b9c]">
                {description}
              </p>
              <p className="mt-1 text-[12px] font-semibold text-[#7154ff]">{count} task{count === 1 ? '' : 's'}</p>
            </div>
          ))}
        </div>

        <div className="mt-[19px] grid gap-4 md:grid-cols-[0.8fr_1.2fr]">
          <section className="min-h-[191px] rounded-[16px] border border-[#cfe2ff] bg-[#f1f8ff] p-5">
            <p className="text-[13px] font-semibold text-[#211e58]">Plan progress</p>
            <h3 className="mt-3 text-[20px] font-bold leading-6 text-[#211e58]">
              {nextTask ? taskStage(nextTask.title) : 'Mastery'}
            </h3>
            <p className="mt-3 text-[13px] text-[#626b9c]">{done} of {tasks.length} tasks done</p>
            <div className="mt-3 flex items-center gap-3">
              <div
                className="h-[11px] flex-1 overflow-hidden rounded-full bg-[#dce7ff]"
                role="progressbar"
                aria-label="Plan progress"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={progress}
              >
                <div className="h-full rounded-full bg-[#2865e9]" style={{ width: `${progress}%` }} />
              </div>
              <span className="text-[14px] font-semibold text-[#211e58]">{progress}%</span>
            </div>
          </section>

          <section className="min-h-[191px] rounded-[16px] border border-[#cfe2ff] bg-[#faf9ff] p-5">
            <p className="text-[13px] font-semibold text-[#211e58]">Next Step</p>
            <h3 className="mt-4 text-[18px] font-bold leading-6 text-[#211e58]">
              {nextTask ? nextTask.title : 'All planned tasks are done'}
            </h3>
            {nextTask && <p className="mt-1 text-[12px] text-[#626b9c]">Day {nextTask.day_number} · {nextTask.minutes} min</p>}
            <Link
              to="/sim"
              className="mt-4 inline-flex h-[38px] items-center gap-2 rounded-full bg-gradient-to-r from-[#8138ef] to-[#6260ef] px-5 text-[13px] font-semibold text-white shadow-[0_5px_10px_rgba(104,74,222,0.2)] transition hover:brightness-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500"
            >
              Go to Task <ArrowRight size={16} />
            </Link>
          </section>
        </div>
      </section>
    </div>
  )
}

export default Pipeline
