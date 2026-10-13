import { useState } from 'react'
import { Building2, GraduationCap, Hospital, Sprout } from 'lucide-react'

const categories = ['Jobs', 'Projects', 'Resources', 'Other']

const opportunities = [
  {
    title: 'Junior Anesthesia Technologist',
    organization: 'Apollo Hospitals · Hyderabad',
    type: 'Job',
    Icon: Building2,
    iconColor: 'bg-[#2865f2]',
    tagColor: 'bg-[#baf3f3] text-[#149eab]',
  },
  {
    title: 'Research Intern – Medical AI',
    organization: 'AI Health Labs · Remote',
    type: 'Internship',
    Icon: Sprout,
    iconColor: 'bg-[#1ec6c9]',
    tagColor: 'bg-[#baf3f3] text-[#149eab]',
  },
  {
    title: 'Medical Coding Specialist',
    organization: 'Dr. Reddy’s · Hyderabad',
    type: 'Job',
    Icon: Hospital,
    iconColor: 'bg-[#20cda6]',
    tagColor: 'bg-[#baf3f3] text-[#149eab]',
  },
  {
    title: 'Healthcare Research Project',
    organization: 'IIT Hyderabad',
    type: 'Project',
    Icon: GraduationCap,
    iconColor: 'bg-[#ffc400]',
    tagColor: 'bg-[#c8f8df] text-[#10ac65]',
  },
]

function Scanner() {
  const [activeCategory, setActiveCategory] = useState('Jobs')

  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div aria-hidden="true" className="pointer-events-none absolute -right-[96px] -top-[278px] -z-10 size-[260px] rounded-full bg-[#dff8f0]" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]" />

      <section className="min-h-[530px] rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div role="tablist" aria-label="Opportunity categories" className="flex flex-wrap gap-[10px]">
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              role="tab"
              aria-selected={activeCategory === category}
              onClick={() => setActiveCategory(category)}
              className={`h-[35px] min-w-[70px] rounded-full px-5 text-[12px] font-semibold transition ${activeCategory === category ? 'bg-[#ded6ff] text-[#6332c7]' : 'bg-[#eef0ff] text-[#7079a6] hover:bg-[#e6e5ff]'}`}
            >
              {category}
            </button>
          ))}
        </div>

        <div className="mt-[18px] overflow-hidden rounded-[16px] border border-[#e3dcff] bg-white/50">
          {opportunities.map(({ title, organization, type, Icon, iconColor, tagColor }) => (
            <article
              key={title}
              className="flex min-h-[102px] items-center justify-between gap-4 border-b border-[#e6e0ff] px-[19px] py-4 last:border-b-0"
            >
              <div className="flex min-w-0 items-center gap-[18px]">
                <span className={`grid size-[47px] shrink-0 place-items-center rounded-[10px] text-white ${iconColor}`}>
                  <Icon size={23} strokeWidth={1.8} />
                </span>
                <span className="min-w-0">
                  <strong className="block truncate text-[15px] font-bold leading-5 text-[#262251]">
                    {title}
                  </strong>
                  <span className="mt-[5px] block truncate text-[13px] leading-5 text-[#737ba6]">
                    {organization}
                  </span>
                </span>
              </div>
              <span className={`grid min-w-[90px] shrink-0 place-items-center rounded-full px-4 py-[7px] text-[12px] font-semibold ${tagColor}`}>
                {type}
              </span>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

export default Scanner
