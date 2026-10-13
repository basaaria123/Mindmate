import activityEmblemReference from '../assets/activity-emblem-reference.png'

const activitySteps = [
  { title: 'Analyzing your study plan...', time: '2 min ago', done: false },
  { title: 'Generating personalized plan...', time: '2 min ago', done: false },
  { title: 'Fetching relevant resources...', time: '3 min ago', done: false },
  { title: 'Creating your task list...', time: '0 min ago', done: false },
  { title: 'Almost done!', time: 'Done', done: true },
]

function ActivityEmblem() {
  return (
    <div className="relative size-[264px] shrink-0 overflow-hidden rounded-full shadow-[0_0_24px_5px_rgba(185,134,255,0.35)]">
      <img
        src={activityEmblemReference}
        alt=""
        className="absolute left-[-57px] top-[-43px] max-w-none w-[367px]"
      />
    </div>
  )
}

function Console() {
  return (
    <div className="relative isolate mx-auto w-full max-w-[1100px]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-[172px] -z-10 size-[250px] rounded-full bg-[#dff8f0]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]"
      />

      <section className="relative h-[530px] overflow-hidden rounded-[18px] bg-[linear-gradient(115deg,#20284d_0%,#171a3b_52%,#1e103d_100%)] px-6 pb-6 pt-6 text-white shadow-[0_12px_24px_rgba(33,25,81,0.2)] sm:px-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_74%_70%,rgba(99,62,187,0.16),transparent_38%)]" />
        <div className="relative z-10 flex items-center justify-between">
          <h2 className="text-[20px] font-bold leading-7">Live Activity</h2>
          <span className="inline-flex h-[30px] items-center gap-2 rounded-full bg-white/[0.07] px-4 text-[11px] font-medium text-[#e2e2f3]">
            <span className="size-[7px] rounded-full bg-[#38d7a7] shadow-[0_0_9px_rgba(56,215,167,.8)]" />
            Online
          </span>
        </div>

        <div className="relative z-10 mt-[22px] grid h-[365px] grid-cols-1 md:grid-cols-[1.15fr_0.85fr]">
          <ol className="relative">
            <span aria-hidden="true" className="absolute left-[11px] top-[11px] h-[294px] w-px bg-gradient-to-b from-[#9b68ff] via-[#7951e4] to-[#31d7a4]" />
            {activitySteps.map(({ title, time, done }) => (
              <li key={title} className="relative flex min-h-[73px] gap-[18px]">
                <span
                  className={`relative z-10 mt-[6px] grid size-[22px] shrink-0 place-items-center rounded-full ${done ? 'bg-[#153c4c]' : 'bg-[#342558]'}`}
                >
                  <span className={`size-[9px] rounded-full ${done ? 'bg-[#35d8a4] shadow-[0_0_9px_3px_rgba(53,216,164,.65)]' : 'bg-[#a56bff] shadow-[0_0_9px_3px_rgba(165,107,255,.62)]'}`} />
                </span>
                <span className="pt-[2px]">
                  <strong className="block text-[15px] font-semibold leading-5 text-[#f1f1fb]">
                    {title}
                  </strong>
                  <small className={`mt-[4px] block text-[11px] leading-4 ${done ? 'text-[#4fe0b4]' : 'text-[#a8aecb]'}`}>
                    {time}
                  </small>
                </span>
              </li>
            ))}
          </ol>

          <div className="hidden items-center justify-center md:flex">
            <ActivityEmblem />
          </div>
        </div>

        <svg
          aria-hidden="true"
          viewBox="0 0 900 110"
          preserveAspectRatio="none"
          className="pointer-events-none absolute bottom-0 left-0 h-[110px] w-full"
        >
          <path d="M0 96 C90 125 155 102 225 77 S340 48 390 31 S490 29 550 57 S625 81 683 58 S800 24 900 53" fill="none" stroke="#a05bff" strokeWidth="2.2" />
          <path d="M0 88 C105 111 167 100 232 78 S330 42 400 34 S519 37 585 65 S722 100 900 59" fill="none" stroke="#3878eb" strokeOpacity=".75" strokeWidth="1" />
        </svg>
      </section>
    </div>
  )
}

export default Console
