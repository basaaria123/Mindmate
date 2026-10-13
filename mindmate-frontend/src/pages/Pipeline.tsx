import { useState } from 'react'
import {
  ArrowRight,
  BookOpen,
  CheckSquare,
  GraduationCap,
  Trophy,
} from 'lucide-react'
import { Link } from 'react-router'
import { replanLearningPathApi } from '../services/api'
import type { DemoState } from '../services/demoState'

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

function Pipeline() {
  const [isReplanning, setIsReplanning] = useState(false)
  const [replanState, setReplanState] = useState<DemoState | null>(null)
  const [replanError, setReplanError] = useState<string | null>(null)

  async function handleReplan() {
    setIsReplanning(true)
    setReplanError(null)
    try {
      setReplanState(await replanLearningPathApi())
    } catch (error) {
      setReplanError(error instanceof Error ? error.message : 'Could not update your plan.')
    } finally {
      setIsReplanning(false)
    }
  }

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
          <h2 className="text-[21px] font-bold leading-7 text-[#211e58]">
            Your Learning Pipeline
          </h2>
          <button
            type="button"
            onClick={handleReplan}
            disabled={isReplanning}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-500 px-4 text-sm font-semibold text-white shadow-sm hover:brightness-105 disabled:cursor-wait disabled:opacity-60"
          >
            {isReplanning ? 'Updating plan…' : 'Update my plan'}
          </button>
        </div>
        {replanError && <p role="alert" className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{replanError}</p>}
        {replanState && !replanState.replanReason && (
          <p role="status" className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            Plan update request completed.
          </p>
        )}
        {replanState?.replanReason && (
          <section aria-live="polite" className="mb-4 rounded-xl border border-violet-200 bg-violet-50/70 p-4">
            <h3 className="font-semibold text-violet-900">Your plan was updated</h3>
            <p className="mt-1 text-sm text-violet-800">{replanState.replanReason}</p>
            {replanState.updatedPlan && (
              <ol className="mt-3 list-inside list-decimal space-y-1 text-sm text-violet-900">
                {replanState.updatedPlan.map((task) => <li key={task}>{task}</li>)}
              </ol>
            )}
          </section>
        )}

        <div className="grid min-h-[233px] grid-cols-2 items-center gap-y-5 rounded-[16px] border border-[#cfe2ff] bg-[#f7fbff] px-3 py-5 sm:grid-cols-4 sm:gap-0 sm:px-5">
          {stages.map(({ name, description, Icon, color, halo }, index) => (
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
            </div>
          ))}
        </div>

        <div className="mt-[19px] grid gap-4 md:grid-cols-[0.8fr_1.2fr]">
          <section className="min-h-[191px] rounded-[16px] border border-[#cfe2ff] bg-[#f1f8ff] p-5">
            <p className="text-[13px] font-semibold text-[#211e58]">Current Stage</p>
            <h3 className="mt-3 text-[20px] font-bold leading-6 text-[#211e58]">
              Practice
            </h3>
            <p className="mt-3 text-[13px] text-[#626b9c]">2 tasks in this stage</p>
            <div className="mt-3 flex items-center gap-3">
              <div
                className="h-[11px] flex-1 overflow-hidden rounded-full bg-[#dce7ff]"
                role="progressbar"
                aria-label="Practice stage progress"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={70}
              >
                <div className="h-full w-[70%] rounded-full bg-[#2865e9]" />
              </div>
              <span className="text-[14px] font-semibold text-[#211e58]">70%</span>
            </div>
          </section>

          <section className="min-h-[191px] rounded-[16px] border border-[#cfe2ff] bg-[#faf9ff] p-5">
            <p className="text-[13px] font-semibold text-[#211e58]">Next Step</p>
            <h3 className="mt-4 text-[18px] font-bold leading-6 text-[#211e58]">
              Revise – Liver &amp; Biliary System
            </h3>
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
