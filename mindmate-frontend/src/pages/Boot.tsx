import { ArrowRight, BookOpen, Bot, ChartNoAxesColumn, Circle, ClipboardPlus, UsersRound, Zap } from 'lucide-react'
import { Link } from 'react-router'

const tasks = [
  { label: 'Study – Cardiovascular System', time: '10:00 AM' },
  { label: 'Practice – Anatomy MCQs', time: '4:00 PM' },
]

function Boot() {
  return <div className="home-dashboard mx-auto max-w-[1200px] space-y-[21px]">
    <section className="mm-home-hero relative min-h-[310px] overflow-hidden rounded-[22px] border border-violet-200 bg-[linear-gradient(112deg,#eeebff_0%,#e9e9ff_57%,#ccecf7_100%)] px-6 py-7 sm:px-[27px] sm:pb-[52px] sm:pt-[60px]">
      <div className="pointer-events-none absolute -right-4 top-3 size-72 rounded-full bg-[#9b8cff]/30 blur-3xl"/><span className="absolute right-[26%] top-6 text-2xl text-white">✦</span><span className="absolute right-1 top-[68%] text-xs text-amber-200">•</span>
      <div className="relative z-10">
        <h1 className="text-[28px] font-bold leading-tight tracking-[-.025em] text-[#201d56] sm:text-[32px]">Good Morning, Salma!</h1>
        <p className="mt-4 text-base text-[#5e6799] sm:text-[18px]">Small steps today, big progress tomorrow.</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/pipeline" className="inline-flex h-[46px] items-center gap-2.5 rounded-2xl border border-violet-200 bg-[#e9e3ff] px-4 text-sm font-semibold text-[#211e58] hover:bg-[#dfd6ff]"><ClipboardPlus size={18} className="text-[#7154ff]"/>Continue your plan</Link>
          <Link to="/sim" className="inline-flex h-[46px] items-center gap-2.5 rounded-2xl border border-violet-200 bg-white px-4 text-sm font-semibold text-[#211e58] hover:bg-violet-50"><ClipboardPlus size={18} className="text-[#7154ff]"/>Create a new task</Link>
          <Link to="/console" className="inline-flex h-[46px] items-center gap-2.5 rounded-2xl border border-violet-200 bg-white px-4 text-sm font-semibold text-[#211e58] hover:bg-violet-50"><Bot size={18} className="text-[#7154ff]"/>Ask AI</Link>
        </div>
      </div>
    </section>

    <section className="grid gap-4 xl:grid-cols-[1.1fr_1.2fr_.7fr]">
      <article className="mm-home-card min-h-[290px] rounded-[22px] border border-violet-200 bg-white p-5 shadow-[0_8px_24px_rgba(82,62,163,.07)]">
        <div className="flex items-start justify-between"><h2 className="text-[19px] font-bold text-[#211e58]">Your Progress</h2><ChartNoAxesColumn size={27} className="text-emerald-400"/></div>
        <div className="mt-5 flex items-center justify-center gap-4 sm:justify-start sm:gap-5"><div className="mm-home-progress-ring grid size-[150px] shrink-0 place-items-center rounded-full" style={{background:'conic-gradient(from -5deg,#8f6aff 0 68%,#eee8ff 68% 100%)'}}><div className="mm-home-progress-center grid size-[124px] place-items-center rounded-full bg-white text-[29px] font-bold text-[#211e58]">68%</div></div><div><h3 className="text-[16px] font-bold text-[#211e58]">Weekly Goal</h3><p className="mt-2 text-[13px] text-[#858dbb]">4 of 6 tasks completed</p></div></div>
      </article>

      <article className="mm-home-card min-h-[290px] rounded-[22px] border border-violet-200 bg-white p-5 shadow-[0_8px_24px_rgba(82,62,163,.07)]">
        <div className="flex items-end justify-between"><div><h2 className="text-[19px] font-bold text-[#211e58]">Today’s Tasks</h2><p className="mt-1 text-sm text-[#858dbb]">2 due today</p></div><Link to="/sim" className="mb-1 inline-flex items-center gap-1 text-sm font-semibold text-[#805cff]">View all <ArrowRight size={15}/></Link></div>
        <div className="mt-4">{tasks.map((task)=><Link key={task.label} to="/sim" className="flex min-h-[65px] items-center gap-2.5 border-b border-[#f0edfb] last:border-0"><Circle size={22} strokeWidth={1.8} className="shrink-0 text-[#a28bff]"/><span className="flex-1 text-[13px] font-medium text-[#211e58]">{task.label}</span><span className="whitespace-nowrap text-xs text-[#858dbb]">{task.time}</span></Link>)}</div>
      </article>

      <article className="mm-home-card min-h-[290px] rounded-[22px] border border-violet-200 bg-white p-4 shadow-[0_8px_24px_rgba(82,62,163,.07)]">
        <h2 className="mb-3 text-[19px] font-bold text-[#211e58]">Quick Actions</h2>
        <Link to="/sim" className="flex h-[52px] items-center gap-2.5 rounded-xl px-1 hover:bg-violet-50"><span className="grid size-9 place-items-center rounded-xl bg-[#f0eaff] text-[#7e5aff]"><ClipboardPlus size={18}/></span><span className="text-[13px] font-semibold">Create a new task</span></Link>
        <Link to="/scanner" className="flex h-[52px] items-center gap-2.5 rounded-xl px-1 hover:bg-cyan-50"><span className="grid size-9 place-items-center rounded-xl bg-[#d9f8fa] text-[#19bcd0]"><BookOpen size={18}/></span><span className="text-[13px] font-semibold">Explore resources</span></Link>
        <Link to="/console" className="flex h-[52px] items-center gap-2.5 rounded-xl px-1 hover:bg-orange-50"><span className="grid size-9 place-items-center rounded-xl bg-[#fff0df] text-[#f09938]"><UsersRound size={18}/></span><span className="text-[13px] font-semibold">Get support</span></Link>
      </article>
    </section>

    <section className="mm-home-promise flex min-h-[112px] flex-wrap items-center gap-4 rounded-[22px] border border-violet-100 bg-[linear-gradient(105deg,#e7e0ff_0%,#f1edff_100%)] px-5 py-5 sm:px-7">
      <Zap size={46} fill="#ffbf24" stroke="#ffbf24" className="shrink-0"/><div className="min-w-[220px] flex-1"><h2 className="text-[19px] font-bold text-[#211e58]">Let’s build your future together</h2><p className="mt-2 text-sm text-[#626b9a]">Get personalized guidance, practice and insights — all in one place.</p></div><Link to="/gap-map" className="ml-auto inline-flex h-[47px] items-center rounded-2xl bg-gradient-to-r from-[#956cff] to-[#653bf0] px-5 text-sm font-semibold text-white shadow-[0_7px_15px_rgba(112,70,240,.28)] hover:brightness-105">Explore Now</Link>
    </section>
  </div>
}

export default Boot
