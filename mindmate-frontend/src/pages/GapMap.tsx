import { ArrowRight, CheckCircle2, CircleAlert, Target } from 'lucide-react'

const skills = [
  {
    name: 'React components',
    category: 'Frontend',
    current: 78,
    target: 85,
    priority: 'On track',
  },
  {
    name: 'Async JavaScript',
    category: 'JavaScript',
    current: 46,
    target: 80,
    priority: 'Practice next',
  },
  {
    name: 'Accessible forms',
    category: 'Accessibility',
    current: 35,
    target: 75,
    priority: 'High priority',
  },
]

function GapMap() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          Skill analysis
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Gap Map
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Compare example skill strengths with learning targets. These values
          are sample data until MINDMATE connects to your profile.
        </p>
      </div>

      <section className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3 text-cyan-300">
            <Target size={19} />
            <p className="text-sm text-slate-400">Skills mapped</p>
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">3</p>
          <p className="mt-1 text-xs text-slate-500">Sample skill areas</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3 text-emerald-300">
            <CheckCircle2 size={19} />
            <p className="text-sm text-slate-400">On track</p>
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">1</p>
          <p className="mt-1 text-xs text-slate-500">At or near its target</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3 text-amber-300">
            <CircleAlert size={19} />
            <p className="text-sm text-slate-400">Practice areas</p>
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">2</p>
          <p className="mt-1 text-xs text-slate-500">Could use more practice</p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/50">
        <div className="border-b border-slate-800 px-5 py-4">
          <h2 className="font-semibold text-white">Skill strengths and gaps</h2>
          <p className="mt-1 text-sm text-slate-400">
            Current strength compared with the sample learning target.
          </p>
        </div>

        <div className="divide-y divide-slate-800">
          {skills.map((skill) => (
            <article key={skill.name} className="px-5 py-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-white">{skill.name}</p>
                  <p className="mt-1 text-xs text-slate-500">{skill.category}</p>
                </div>

                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    skill.priority === 'On track'
                      ? 'bg-emerald-400/10 text-emerald-300'
                      : skill.priority === 'High priority'
                        ? 'bg-rose-400/10 text-rose-300'
                        : 'bg-amber-400/10 text-amber-300'
                  }`}
                >
                  {skill.priority}
                </span>
              </div>

              <div className="mt-5">
                <div className="mb-2 flex justify-between text-xs">
                  <span className="text-slate-400">
                    Current strength: {skill.current}%
                  </span>
                  <span className="text-slate-500">
                    Target: {skill.target}%
                  </span>
                </div>

                <div className="relative h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-300"
                    style={{ width: `${skill.current}%` }}
                  />
                  <span
                    className="absolute -top-1 h-4 w-0.5 bg-white/70"
                    style={{ left: `${skill.target}%` }}
                    aria-label={`Target ${skill.target}%`}
                  />
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-6 flex flex-col gap-3 rounded-2xl border border-cyan-300/20 bg-cyan-300/5 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-medium text-white">Suggested focus</p>
          <p className="mt-1 text-sm text-slate-400">
            Practice accessible forms, then review async JavaScript.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm font-medium text-cyan-300">
          <span>Based on sample data</span>
          <ArrowRight size={16} />
        </div>
      </section>
    </div>
  )
}

export default GapMap