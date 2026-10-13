import { ArrowRight, HeartPulse, Pill, Wind } from 'lucide-react'
import { Link } from 'react-router'

const skillGaps = [
  { name: 'Cardiovascular System', value: 52, Icon: HeartPulse, iconColor: 'bg-[#2865f2]', barColor: 'bg-[#ff5a86]' },
  { name: 'Respiratory System', value: 46, Icon: Wind, iconColor: 'bg-[#ff9800]', barColor: 'bg-[#ff9800]' },
  { name: 'Pharmacology', value: 53, Icon: Pill, iconColor: 'bg-[#ff9800]', barColor: 'bg-[#ff8538]' },
]

function SkillLevelRing() {
  const radius = 79
  const circumference = 2 * Math.PI * radius
  const progress = circumference * 0.72

  return (
    <div className="flex h-[308px] flex-col items-center justify-center rounded-[17px] border border-[#e3dcff] bg-[#faf9ff]">
      <div className="relative grid size-[190px] place-items-center">
        <svg viewBox="0 0 190 190" className="size-full -rotate-90" aria-hidden="true">
          <circle cx="95" cy="95" r={radius} fill="none" stroke="#d8e2f4" strokeWidth="14" />
          <circle
            cx="95"
            cy="95"
            r={radius}
            fill="none"
            stroke="#ff9900"
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={`${progress} ${circumference}`}
          />
        </svg>
        <span className="absolute text-[38px] font-bold tracking-tight text-[#211e58]">72%</span>
      </div>
      <h2 className="mt-[13px] text-[16px] font-bold text-[#262251]">Overall Skill Level</h2>
    </div>
  )
}

function SkillGapList() {
  return (
    <section className="h-[308px] rounded-[17px] border border-[#e3dcff] bg-white/55 px-5 py-[18px]">
      <h2 className="mb-[17px] text-[18px] font-bold leading-6 text-[#262251]">Top Skill Gaps</h2>
      <div className="space-y-[17px]">
        {skillGaps.map(({ name, value, Icon, iconColor, barColor }) => (
          <article key={name} className="flex items-center gap-[13px]">
            <span className={`grid size-[35px] shrink-0 place-items-center rounded-full text-white ${iconColor}`}>
              <Icon size={19} strokeWidth={1.8} />
            </span>
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-[13px] font-semibold leading-5 text-[#28254f]">{name}</h3>
              <div
                className="mt-[8px] h-[8px] overflow-hidden rounded-full bg-[#ebeaf5]"
                role="progressbar"
                aria-label={`${name} skill gap`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={value}
              >
                <div className={`h-full rounded-full ${barColor}`} style={{ width: `${value}%` }} />
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function GapMap() {
  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div aria-hidden="true" className="pointer-events-none absolute -right-[96px] -top-[278px] -z-10 size-[260px] rounded-full bg-[#dff8f0]" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]" />

      <section className="min-h-[530px] rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div className="grid gap-[19px] lg:grid-cols-[280px_minmax(0,1fr)]">
          <SkillLevelRing />
          <SkillGapList />
        </div>

        <h2 className="mb-[12px] mt-[18px] text-[18px] font-bold leading-6 text-[#262251]">
          Recommended Actions
        </h2>
        <section className="flex min-h-[103px] flex-col justify-between gap-4 rounded-[16px] border border-[#eee0ff] bg-[linear-gradient(100deg,#fff0f2_0%,#f6efff_100%)] px-[18px] py-4 sm:flex-row sm:items-center">
          <div className="flex min-w-0 items-center gap-4">
            <span className="grid size-[47px] shrink-0 place-items-center rounded-[13px] bg-[#ff718a] text-white">
              <HeartPulse size={24} strokeWidth={1.8} />
            </span>
            <span className="min-w-0">
              <strong className="block text-[15px] font-bold leading-5 text-[#262251]">
                Focus on Cardiovascular System
              </strong>
              <span className="mt-[5px] block text-[13px] text-[#737ba6]">
                Try 3 practice quizzes to improve.
              </span>
            </span>
          </div>
          <Link
            to="/sim"
            className="inline-flex h-[38px] shrink-0 items-center justify-center gap-3 rounded-full bg-gradient-to-r from-[#8039ed] to-[#6259ef] px-[18px] text-[13px] font-semibold text-white shadow-[0_5px_12px_rgba(97,69,211,.22)] transition hover:brightness-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500"
          >
            Start Practice <ArrowRight size={16} />
          </Link>
        </section>
      </section>
    </div>
  )
}

export default GapMap
