import { useCallback, useState } from 'react'
import { ArrowRight, Target } from 'lucide-react'
import type { Gap } from '../services/backend'
import { Link } from 'react-router'
import { getGaps, getOpportunities, type GapReport } from '../services/backend'
import { useLoad } from '../hooks/useLoad'
import { RefTags } from '../components/RefText'

const BAR_COLORS = ['bg-[#ff5a86]', 'bg-[#ff9800]', 'bg-[#ff8538]', 'bg-[#8c4df3]', 'bg-[#2865f2]']

function SkillLevelRing({ score, label }: { score: number | null; label: string }) {
  const radius = 79
  const circumference = 2 * Math.PI * radius
  const progress = circumference * ((score ?? 0) / 100)

  return (
    <div className="mm-gap-level flex h-[308px] flex-col items-center justify-center rounded-[17px] border border-[#e3dcff] bg-[#faf9ff] px-3">
      <div className="relative grid size-[190px] place-items-center">
        <svg viewBox="0 0 190 190" className="size-full -rotate-90" aria-hidden="true">
          <circle cx="95" cy="95" r={radius} fill="none" stroke="#d8e2f4" strokeWidth="14" />
          <circle cx="95" cy="95" r={radius} fill="none" stroke="#ff9900" strokeWidth="14" strokeLinecap="round" strokeDasharray={`${progress} ${circumference}`} />
        </svg>
        <span className="absolute text-[38px] font-bold tracking-tight text-[#211e58]">{score === null ? '–' : `${score}%`}</span>
      </div>
      <h2 className="mt-[13px] text-center text-[16px] font-bold text-[#262251]">{label}</h2>
    </div>
  )
}

function SkillGapList({ gaps, loading, error }: { gaps: Gap[]; loading: boolean; error: string | null }) {
  return (
    <section className="mm-gap-list min-h-[308px] rounded-[17px] border border-[#e3dcff] bg-white/55 px-5 py-[18px]">
      <h2 className="mb-[17px] text-[18px] font-bold leading-6 text-[#262251]">Top Skill Gaps</h2>
      {loading && <p role="status" className="text-sm text-[#737ba6]">Ranking gaps…</p>}
      {error && <p role="alert" className="text-sm text-rose-600">Could not load gaps: {error}</p>}
      {!loading && !error && gaps.length === 0 && <p className="text-sm text-[#737ba6]">No gaps for this opportunity. Every requirement is demonstrated with evidence.</p>}
      <div className="space-y-[17px]">
        {gaps.slice(0, 5).map((gap, index) => (
          <article key={gap.requirement} className="flex items-center gap-[13px]">
            <span className={`grid size-[35px] shrink-0 place-items-center rounded-full text-white ${BAR_COLORS[index % BAR_COLORS.length]}`}>
              <Target size={19} strokeWidth={1.8} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="truncate text-[13px] font-semibold leading-5 text-[#28254f]">{gap.requirement}</h3>
                <span className="text-[11px] text-[#7a80a7]">{gap.weight}{gap.mandatory ? ' · mandatory' : ''} · {gap.coverage.replace('_', ' ')}</span>
                <RefTags refs={gap.refs} />
              </div>
              <div
                className="mt-[8px] h-[8px] overflow-hidden rounded-full bg-[#ebeaf5]"
                role="progressbar"
                aria-label={`${gap.requirement} impact`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={gap.impact_score}
              >
                <div className={`h-full rounded-full ${BAR_COLORS[index % BAR_COLORS.length]}`} style={{ width: `${gap.impact_score}%` }} />
              </div>
            </div>
            <span className="w-10 shrink-0 text-right text-[12px] font-semibold text-[#4b4f78]">{gap.impact_score}</span>
          </article>
        ))}
      </div>
    </section>
  )
}

function GapMap() {
  const opportunities = useLoad(getOpportunities)
  const [selected, setSelected] = useState<number | null>(null)
  const opportunityId = selected ?? opportunities.data?.find((item) => item.target)?.id ?? opportunities.data?.[0]?.id ?? null
  const loadGaps = useCallback(() => (opportunityId === null ? Promise.resolve<GapReport>({ fit: null, gaps: [] }) : getGaps(opportunityId)), [opportunityId])
  const gaps = useLoad(loadGaps)
  const opportunity = opportunities.data?.find((item) => item.id === opportunityId)
  const top = gaps.data?.gaps[0]
  const fit = gaps.data?.fit ?? opportunity?.fit ?? null

  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div aria-hidden="true" className="pointer-events-none absolute -right-[96px] -top-[278px] -z-10 size-[260px] rounded-full bg-[#dff8f0]" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]" />

      <section className="mm-gap-panel min-h-[530px] rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <label htmlFor="gap-target" className="text-[13px] font-semibold text-[#262251]">Target opportunity</label>
          <select
            id="gap-target"
            value={opportunityId ?? ''}
            onChange={(event) => setSelected(Number(event.target.value))}
            disabled={!opportunities.data?.length}
            className="h-10 min-w-[260px] rounded-xl border border-violet-200 bg-white px-3 text-sm text-[#262251] outline-none focus:border-violet-500"
          >
            {(opportunities.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>{item.target ? '★ ' : ''}{item.title}{item.org ? ` · ${item.org}` : ''}{item.fit ? ` (${item.fit.score}%)` : ''}</option>
            ))}
          </select>
          {opportunities.error && <span role="alert" className="text-sm text-rose-600">{opportunities.error}</span>}
        </div>

        <div className="grid gap-[19px] lg:grid-cols-[280px_minmax(0,1fr)]">
          <SkillLevelRing score={fit?.score ?? null} label={fit ? `${fit.band} fit for this role` : gaps.loading ? 'Scoring…' : 'Fit not assessed yet'} />
          <SkillGapList gaps={gaps.data?.gaps ?? []} loading={gaps.loading} error={gaps.error} />
        </div>

        <h2 className="mb-[12px] mt-[18px] text-[18px] font-bold leading-6 text-[#262251]">Recommended Action</h2>
        <section className="mm-gap-action flex min-h-[103px] flex-col justify-between gap-4 rounded-[16px] border border-[#eee0ff] bg-[linear-gradient(100deg,#fff0f2_0%,#f6efff_100%)] px-[18px] py-4 sm:flex-row sm:items-center">
          <div className="flex min-w-0 items-center gap-4">
            <span className="grid size-[47px] shrink-0 place-items-center rounded-[13px] bg-[#ff718a] text-white">
              <Target size={24} strokeWidth={1.8} />
            </span>
            <span className="min-w-0">
              <strong className="block text-[15px] font-bold leading-5 text-[#262251]">
                {top ? `Focus on ${top.requirement}` : 'No gap to close for this opportunity'}
              </strong>
              <span className="mt-[5px] block text-[13px] text-[#737ba6]">
                {top ? top.recommended_focus : 'Pick another opportunity or keep practising.'}
              </span>
            </span>
          </div>
          {top && (
            <Link
              to={`/sim?practice=${encodeURIComponent(top.requirement)}`}
              className="inline-flex h-[38px] shrink-0 items-center justify-center gap-3 rounded-full bg-gradient-to-r from-[#8039ed] to-[#6259ef] px-[18px] text-[13px] font-semibold text-white shadow-[0_5px_12px_rgba(97,69,211,.22)] transition hover:brightness-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500"
            >
              Start Practice <ArrowRight size={16} />
            </Link>
          )}
        </section>
      </section>
    </div>
  )
}

export default GapMap
