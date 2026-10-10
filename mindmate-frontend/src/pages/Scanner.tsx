import {
  ArrowUpRight,
  BriefcaseBusiness,
  Clock3,
  Search,
  Sparkles,
  Target,
} from 'lucide-react'

const opportunities = [
  {
    title: 'Frontend Engineer Intern',
    organization: 'Northstar Labs',
    type: 'Internship',
    match: 86,
    skills: ['React', 'TypeScript', 'CSS'],
    time: 'Posted recently',
  },
  {
    title: 'Junior UI Developer',
    organization: 'Brightpath Studio',
    type: 'Entry level',
    match: 72,
    skills: ['JavaScript', 'Accessibility', 'Design systems'],
    time: 'Recently updated',
  },
  {
    title: 'Web Developer Fellow',
    organization: 'Open Web Collective',
    type: 'Fellowship',
    match: 64,
    skills: ['HTML', 'React', 'Testing'],
    time: 'Applications open',
  },
]

function Scanner() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Opportunity discovery
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Scanner
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Explore sample opportunities and the skills they ask for. These
          listings are sample data; later, MINDMATE can load real results.
        </p>
      </div>

      <section className="mb-6 flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-cyan-300/10 p-3 text-cyan-300">
            <Sparkles size={20} />
          </div>
          <div>
            <p className="font-medium text-white">Sample matches</p>
            <p className="mt-1 text-sm text-slate-400">
              Based on example frontend skills
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-400">
          <Search size={16} />
          <span>Example results</span>
        </div>
      </section>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold text-white">Opportunities</h2>
        <span className="text-sm text-slate-500">
          {opportunities.length} sample listings
        </span>
      </div>

      <section className="space-y-4">
        {opportunities.map((opportunity) => (
          <article
            key={opportunity.title}
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700"
          >
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex gap-4">
                <div className="hidden rounded-xl bg-slate-800 p-3 text-cyan-300 sm:block">
                  <BriefcaseBusiness size={21} />
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-cyan-300">
                    {opportunity.type}
                  </p>
                  <h3 className="mt-1 text-lg font-semibold text-white">
                    {opportunity.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-400">
                    {opportunity.organization}
                  </p>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {opportunity.skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-full border border-slate-700 bg-slate-800/70 px-2.5 py-1 text-xs text-slate-300"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>

                  <p className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                    <Clock3 size={14} />
                    {opportunity.time}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 sm:flex-col sm:items-end">
                <div className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-sm font-medium text-emerald-300">
                  <Target size={15} />
                  {opportunity.match}% match
                </div>
                <ArrowUpRight size={18} className="text-slate-500" />
              </div>
            </div>
          </article>
        ))}
      </section>
    </div>
  )
}

export default Scanner