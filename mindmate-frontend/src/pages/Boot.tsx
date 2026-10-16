import { useEffect, useState } from 'react'
import { ArrowRight, BookOpen, Bot, ChartNoAxesColumn, CheckSquare, Circle, ClipboardPlus, UsersRound, X, Zap } from 'lucide-react'
import { Link } from 'react-router'

const tasks = [
  { label: 'Study – Cardiovascular System', time: '10:00 AM' },
  { label: 'Practice – Anatomy MCQs', time: '4:00 PM' },
]

const dashboardTour = [
  { title: "Today's Tasks", body: "You have 4 tasks pending for today. Stay consistent — you're doing great!", icon: 'tasks' },
  { title: 'Weekly Progress', body: 'See your progress at a glance and keep moving toward your weekly goal.', icon: 'progress' },
  { title: 'Study Streak', body: 'Build a steady routine one focused day at a time.', icon: 'streak' },
  { title: 'Quick Actions', body: 'Jump straight into a task, practice session, learning path, or opportunity.', icon: 'actions' },
  { title: 'Your Dashboard', body: 'Your progress, tasks, and learning journey are all in one place. You’re ready to go!', icon: 'dashboard' },
]

function DashboardTour() {
  const [step, setStep] = useState(0)
  const [open, setOpen] = useState(() => {
    try { return window.sessionStorage.getItem('mindmate-dashboard-tour-dismissed') !== 'true' }
    catch { return true }
  })

  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeTour()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open])

  function closeTour() {
    setOpen(false)
    try { window.sessionStorage.setItem('mindmate-dashboard-tour-dismissed', 'true') } catch { /* session storage may be unavailable */ }
  }

  if (!open) return null
  const current = dashboardTour[step]
  return (
    <div className="mm-dashboard-tour fixed inset-0 z-[100] grid place-items-center overflow-y-auto bg-[#18213a]/60 px-4 py-8 backdrop-blur-[2px]" onMouseDown={(event) => { if (event.target === event.currentTarget) closeTour() }}>
      <div className="mm-dashboard-tour__stack relative w-full max-w-[640px]" role="dialog" aria-modal="true" aria-labelledby="dashboard-tour-title" aria-describedby="dashboard-tour-description">
        <div className="mm-dashboard-tour__back mm-dashboard-tour__back--two" aria-hidden="true" />
        <div className="mm-dashboard-tour__back mm-dashboard-tour__back--one" aria-hidden="true" />
        <article key={step} className="mm-dashboard-tour__card relative grid min-h-[300px] grid-cols-1 overflow-hidden rounded-[24px] border border-[#e9dcff] bg-[#fcf9ff] p-6 shadow-[0_18px_42px_rgba(79,53,139,.2)] sm:grid-cols-[150px_minmax(0,1fr)] sm:gap-4 sm:px-6 sm:py-6">
          <button type="button" aria-label="Close dashboard walkthrough" onClick={closeTour} className="absolute right-5 top-5 z-10 grid size-8 place-items-center rounded-full text-[#b995db] transition hover:bg-[#f1e7ff] hover:text-[#7846d7]"><X size={18}/></button>
          <div className="flex items-center sm:items-center sm:justify-center">
            <div className="mm-dashboard-tour__illustration" aria-hidden="true">
              <span className="mm-dashboard-tour__spark mm-dashboard-tour__spark--left">✦</span>
              <span className="mm-dashboard-tour__spark mm-dashboard-tour__spark--right">✦</span>
              <span className="mm-dashboard-tour__clip" />
              <div className="mm-dashboard-tour__paper">
                <CheckSquare size={17}/><i/><CheckSquare size={17}/><i/><CheckSquare size={17}/><i/>
              </div>
              <span className="mm-dashboard-tour__star">✦</span>
            </div>
          </div>
          <div className="flex min-w-0 flex-col pt-1 sm:pt-0">
            <div className="flex items-center gap-3 pr-8">
              <span className="inline-flex h-[42px] items-center gap-2 rounded-full bg-[#f1e8ff] px-4 text-sm font-semibold text-[#9d70ce]"><CheckSquare size={16}/>{step + 1}/5</span>
              <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-[#a285c7]"><CheckSquare size={13}/>{step + 1}/5</span>
            </div>
            <h2 id="dashboard-tour-title" className="mt-2 text-[21px] font-bold tracking-[-.02em] text-[#29264f] sm:text-[22px]">{current.title}</h2>
            <p id="dashboard-tour-description" className="mt-5 max-w-[390px] text-[15px] leading-[1.8] text-[#777c9f]">{current.body}</p>
            <div className="mt-auto flex justify-end pt-4">
              <button type="button" onClick={() => step === dashboardTour.length - 1 ? closeTour() : setStep((value) => value + 1)} className="inline-flex h-[46px] items-center gap-3 rounded-full bg-gradient-to-r from-[#9b4cf4] to-[#703ff0] px-6 text-sm font-semibold text-white shadow-[0_7px_17px_rgba(114,62,226,.25)] transition hover:brightness-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600">
                {step === dashboardTour.length - 1 ? 'Finish' : 'Next'} <ArrowRight size={17}/>
              </button>
            </div>
          </div>
        </article>
      </div>
    </div>
  )
}

function Boot() {
  return <div className="home-dashboard mx-auto max-w-[1200px] space-y-[21px]">
    <DashboardTour />
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
