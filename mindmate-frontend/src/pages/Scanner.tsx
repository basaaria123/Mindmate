import { useEffect, useState } from 'react'
import {
  assessFit,
  extractOpportunity,
  getPersonalizedSuggestions,
  type AIFitAssessment,
  type AIOpportunity,
  type AIOpportunitySuggestion,
  type AISource,
  type WithSource,
} from '../services/api'
import { Building2, GraduationCap, Hospital, Sprout } from 'lucide-react'
import { assessStoredFit, getAIProfile, getOpportunities, type FitResult, type Opportunity } from '../services/backend'
import { useLoad } from '../hooks/useLoad'
import { RefTags } from '../components/RefText'

const categories = ['Jobs', 'Projects', 'Resources', 'Other']
function getSkillText(skill: unknown): string {
  if (typeof skill === 'string' || typeof skill === 'number') {
    return String(skill)
  }

  if (skill && typeof skill === 'object') {
    const item = skill as Record<string, unknown>

    const name = item.skill_name
    const explanation = item.explanation

    if (typeof name === 'string' && typeof explanation === 'string') {
      return `${name} — ${explanation}`
    }

    if (typeof name === 'string') {
      return name
    }

    if (typeof explanation === 'string') {
      return explanation
    }

    return JSON.stringify(item)
  }

  return ''
}

function categoryFor(type: string) {
  const value = type.toLowerCase()
  if (['internship', 'job', 'fellowship'].includes(value)) return 'Jobs'
  if (value === 'project') return 'Projects'
  if (['course', 'resource', 'learning resource'].includes(value)) return 'Resources'
  return 'Other'
}

const SOURCE_TEXT: Record<AISource, string> = {
  nemotron: 'Analysed by NVIDIA Nemotron.',
  offline: 'Offline analysis: keyword matching and fit rules, no AI model was used. Connect the backend with a Nebius key for the Nemotron analysis.',
  recorded: 'Recorded demo answer (the model was not called).',
}

function SourceNote({ source }: { source?: AISource }) {
  if (!source) return null
  return (
    <p className={`mt-2 rounded-lg px-3 py-2 text-xs leading-5 ${source === 'nemotron' ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-800'}`}>
      {SOURCE_TEXT[source]}
    </p>
  )
}

function bandClass(band: string) {
  return band === 'Strong' ? 'bg-emerald-50 text-emerald-700' : band === 'Moderate' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'
}

type Card = {
  title: string
  organization: string
  type: string
  Icon: typeof Building2
  iconColor: string
  tagColor: string
  category: string
  stored?: Opportunity
}

function storedCard(opportunity: Opportunity): Card {
  const category = categoryFor(opportunity.type)
  return {
    title: opportunity.title,
    organization: [opportunity.org, opportunity.deadline ? `apply by ${opportunity.deadline}` : null].filter(Boolean).join(' · '),
    type: opportunity.type.charAt(0).toUpperCase() + opportunity.type.slice(1),
    Icon: category === 'Jobs' ? Building2 : category === 'Projects' ? Sprout : category === 'Resources' ? GraduationCap : Hospital,
    iconColor: 'bg-[#2865f2]',
    tagColor: 'bg-[#baf3f3] text-[#149eab]',
    category,
    stored: opportunity,
  }
}

function Scanner() {
  const [activeCategory, setActiveCategory] = useState('Jobs')
  const [opportunityText, setOpportunityText] = useState('')
  const [personalizedSuggestions, setPersonalizedSuggestions] = useState<AIOpportunitySuggestion[]>([])
  const [suggestionsSource, setSuggestionsSource] = useState<AISource | undefined>()
  const [, setSuggestionsLoading] = useState(true)
  const [suggestionsError, setSuggestionsError] = useState('')
  const [suggestionsLoaded, setSuggestionsLoaded] = useState(false)
  const [aiOpportunity, setAiOpportunity] = useState<WithSource<AIOpportunity> | null>(null)
  const [isExtracting, setIsExtracting] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)

  const [fitAssessment, setFitAssessment] =
    useState<WithSource<AIFitAssessment> | null>(null)
  const [isAssessingFit, setIsAssessingFit] = useState(false)
  const [fitError, setFitError] = useState<string | null>(null)
  const stored = useLoad(getOpportunities)
  const [storedFits, setStoredFits] = useState<Record<number, FitResult>>({})
  const [checking, setChecking] = useState<number | null>(null)
  const [storedFitError, setStoredFitError] = useState<string | null>(null)

  async function checkStoredFit(opportunityId: number) {
    if (storedFits[opportunityId]) {
      setStoredFits((current) => Object.fromEntries(Object.entries(current).filter(([key]) => Number(key) !== opportunityId)))
      return
    }
    setChecking(opportunityId)
    setStoredFitError(null)
    try {
      const fit = await assessStoredFit(opportunityId)
      setStoredFits((current) => ({ ...current, [opportunityId]: fit }))
    } catch (error) {
      setStoredFitError(error instanceof Error ? error.message : 'Could not check your fit.')
    } finally {
      setChecking(null)
    }
  }

  async function handleExtractOpportunity() {
    if (!opportunityText.trim()) {
      setAiError('Please paste a job or internship description first.')
      return
    }

    setIsExtracting(true)
    setAiError(null)
    setFitAssessment(null)
    setFitError(null)
    setAiOpportunity(null)

    try {
      const result = await extractOpportunity(opportunityText.trim())
      setAiOpportunity(result)
    } catch (error) {
      setAiError(
        error instanceof Error
          ? error.message
          : 'Could not analyze this opportunity.',
      )
    } finally {
      setIsExtracting(false)
    }
  }

  async function handleLoadSuggestions() {
  setSuggestionsLoading(true)
  setSuggestionsError('')
  try {
    const result = await getPersonalizedSuggestions(await getAIProfile())

    setPersonalizedSuggestions(result.suggestions)
    setSuggestionsSource(result.mindmate_source)
  } catch (error) {
    setSuggestionsError(
      error instanceof Error
      ? error.message
      : 'Could not load personalized suggestions.',
    )
  } finally {
    setSuggestionsLoading(false)
    setSuggestionsLoaded(true)
}
}
useEffect(() => {
  // Start loading after the first render so no state is set synchronously inside the effect.
  const timer = window.setTimeout(() => void handleLoadSuggestions(), 0)
  return () => window.clearTimeout(timer)
}, [])

  async function handleAssessFit() {
    if (!aiOpportunity) {
      setFitError('Please analyze an opportunity first.')
      return
    }

    setIsAssessingFit(true)
    setFitError(null)
    setFitAssessment(null)

    try {
      const result = await assessFit(await getAIProfile(), aiOpportunity)
      setFitAssessment(result)
    } catch (error) {
      setFitError(
        error instanceof Error
          ? error.message
          : 'Could not assess your fit for this opportunity.',
      )
    } finally {
      setIsAssessingFit(false)
    }
  }

  // Saved opportunities (with evidence-based fit) first, then suggestions not already saved.
  const storedCards = (stored.data ?? []).map(storedCard)
  const storedTitles = new Set(storedCards.map((card) => card.title.toLowerCase()))
  const suggestionCards: Card[] = personalizedSuggestions
    .filter((suggestion) => !storedTitles.has(suggestion.title.toLowerCase()))
    .map((suggestion) => {
      const category = categories.includes(suggestion.category) ? suggestion.category : 'Other'
      return {
        title: suggestion.title,
        organization: suggestion.organization ? `${suggestion.organization} · ${suggestion.explanation}` : suggestion.explanation,
        type: suggestion.opportunity_type.charAt(0).toUpperCase() + suggestion.opportunity_type.slice(1),
        Icon: category === 'Jobs' ? Building2 : category === 'Projects' ? Sprout : category === 'Resources' ? GraduationCap : Hospital,
        iconColor: 'bg-[#8170e8]',
        tagColor: 'bg-[#eeeaff] text-[#6552c7]',
        category,
      }
    })
  const visibleOpportunities = [...storedCards, ...suggestionCards].filter(
    (opportunity) => opportunity.category === activeCategory,
  )

  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-[96px] -top-[278px] -z-10 size-[260px] rounded-full bg-[#dff8f0]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]"
      />

      <section className="min-h-[530px] rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div
          role="tablist"
          aria-label="Opportunity categories"
          className="flex flex-wrap gap-[10px]"
        >
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              role="tab"
              aria-selected={activeCategory === category}
              onClick={() => setActiveCategory(category)}
              className={`h-[35px] min-w-[70px] rounded-full px-5 text-[12px] font-semibold transition ${
                activeCategory === category
                  ? 'bg-[#ded6ff] text-[#6332c7]'
                  : 'bg-[#eef0ff] text-[#7079a6] hover:bg-[#e6e5ff]'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* AI opportunity analyzer */}
        <div className="mt-5 rounded-2xl border border-[#e3dcff] bg-white/80 p-5">
          <h2 className="text-base font-bold text-[#262251]">
            Analyze an opportunity with AI
          </h2>
          <p className="mt-1 text-sm text-[#737ba6]">
            Paste a job, internship, or project description to identify its
            requirements.
          </p>

          <textarea
          className="mt-4 w-full rounded-xl border border-[#d9d2ff] bg-white p-3 text-sm text-[#262251] placeholder:text-[#8585a5] outline-none focus:border-[#8057ff] focus:ring-2 focus:ring-[#8057ff]/20"
            value={opportunityText}
            onChange={(event) => setOpportunityText(event.target.value)}
            placeholder="Paste the full opportunity description here..."
            rows={5}
            maxLength={10000}
            aria-label="Opportunity description"
          />

          <button
            type="button"
            onClick={handleExtractOpportunity}
            disabled={isExtracting}
            className="mt-3 rounded-full bg-[#7950f2] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#6332c7] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isExtracting ? 'Analyzing...' : 'Analyze with AI'}
          </button>

          {aiError && (
            <p role="alert" className="mt-3 text-sm text-red-600">
              {aiError}
            </p>
          )}

          {aiOpportunity && (
            <div className="mt-5 rounded-xl bg-[#f7f5ff] p-4 text-[#262251]">
              <h3 className="font-bold text-[#262251]">
                {aiOpportunity.opportunity_title}
              </h3>
              <SourceNote source={aiOpportunity.mindmate_source} />

              <p className="mt-1 text-sm text-[#737ba6]">
                {aiOpportunity.organization || 'Organization not specified'}
                {' · '}
                {aiOpportunity.opportunity_type || 'Type not specified'}
              </p>

              <p className="mt-3 text-sm text-[#454166]">
                {aiOpportunity.summary}
              </p>

              <h4 className="mt-4 font-semibold text-[#262251]">
                Required skills
              </h4>

              {aiOpportunity.required_skills.length > 0 ? (
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[#454166]">
                  {aiOpportunity.required_skills.map((skill, index) => (
                    <li key={`${skill.skill_name}-${index}`}>
                      <strong>{skill.skill_name}</strong>
                      {' — '}
                      {skill.description || skill.importance}
                      {skill.is_mandatory ? ' (Mandatory)' : ''}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-[#737ba6]">
                  No required skills were identified.
                </p>
              )}

              {aiOpportunity.preferred_skills.length > 0 && (
                <>
                  <h4 className="mt-4 font-semibold text-[#262251]">
                    Preferred skills
                  </h4>
                  <p className="mt-1 text-sm text-[#454166]">
                    {aiOpportunity.preferred_skills.join(', ')}
                  </p>
                </>
              )}

              {aiOpportunity.experience_level && (
                <p className="mt-3 text-sm text-[#454166]">
                  <strong>Experience level:</strong>{' '}
                  {aiOpportunity.experience_level}
                </p>
              )}
            </div>
          )}
        </div>
        {/* AI fit assessment */}
        {aiOpportunity && (
          <div className="mt-4 rounded-2xl border border-[#e3dcff] bg-white/90 p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#eee8ff] text-[#7950f2]">
                <GraduationCap size={23} />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#262251]">
                  Your Opportunity Fit
                </h3>
                <p className="mt-1 text-sm text-[#737ba6]">
                  Discover your strengths and what to learn next.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleAssessFit}
              disabled={isAssessingFit}
              className="mt-4 w-full rounded-xl bg-[#20bfa6] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#159b87] disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {isAssessingFit
                ? 'Assessing your fit...'
                : fitAssessment
                  ? 'Reassess My Fit'
                  : 'Assess My Fit'}
            </button>

            {fitError && (
              <p
                role="alert"
                className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700"
              >
                {fitError}
              </p>
            )}

            {isAssessingFit && (
              <div
                role="status"
                className="mt-4 rounded-xl bg-[#f7f5ff] p-4 text-sm text-[#6332c7]"
              >
                Comparing your profile with the opportunity requirements...
              </div>
            )}

            {fitAssessment && (() => {
              const fit = String(fitAssessment.overall_fit || '').toLowerCase()
              const isHigh = fit.includes('high') || fit.includes('strong')
              const isModerate = fit.includes('moderate') || fit.includes('medium')
              const fitColor = isHigh
                ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                : isModerate
                  ? 'border-amber-200 bg-amber-50 text-amber-800'
                  : 'border-rose-200 bg-rose-50 text-rose-800'

              const sections = [
                {
                  title: 'Matching skills',
                  description: 'Skills that align with the opportunity.',
                  items: fitAssessment.matching_skills,
                  empty: 'No matching skills identified yet.',
                  color: 'border-emerald-200 bg-emerald-50',
                  dot: 'bg-emerald-500',
                },
                {
                  title: 'Partial matches',
                  description: 'Skills where more practice or evidence may help.',
                  items: fitAssessment.partial_matches,
                  empty: 'No partial matches identified.',
                  color: 'border-amber-200 bg-amber-50',
                  dot: 'bg-amber-500',
                },
                {
                  title: 'Skills to improve',
                  description: 'Potential gaps to work on for this opportunity.',
                  items: fitAssessment.missing_skills,
                  empty: 'No missing skills identified.',
                  color: 'border-rose-200 bg-rose-50',
                  dot: 'bg-rose-500',
                },
                {
                  title: 'Your strengths',
                  description: 'Positive points highlighted by the assessment.',
                  items: fitAssessment.strengths,
                  empty: 'No strengths listed in this assessment.',
                  color: 'border-[#dcd3ff] bg-[#f7f5ff]',
                  dot: 'bg-[#7950f2]',
                },
                {
                  title: 'Improvement areas',
                  description: 'Areas to focus on as you prepare.',
                  items: fitAssessment.improvement_areas,
                  empty: 'No improvement areas listed.',
                  color: 'border-[#dcd3ff] bg-white',
                  dot: 'bg-[#7950f2]',
                },
              ]

              const priorities = [
                ...fitAssessment.missing_skills,
                ...fitAssessment.improvement_areas,
              ]
                .map(getSkillText)
                .filter(Boolean)

              return (
                <div className="mt-5 space-y-4">
                  <div className={`rounded-2xl border p-5 ${fitColor}`}>
                    <p className="text-xs font-bold uppercase tracking-[0.14em] opacity-80">
                      Overall fit
                    </p>
                    <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                      <h4 className="text-2xl font-extrabold">
                        {fitAssessment.overall_fit || 'Not specified'}
                      </h4>
                      <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-semibold">
                        {fitAssessment.mindmate_source === 'offline' ? 'Offline estimate' : fitAssessment.mindmate_source === 'recorded' ? 'Recorded answer' : 'AI assessment'}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6">
                      {fitAssessment.summary ||
                        'Review the skill breakdown below to decide your next steps.'}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {sections.map((section) => (
                      <section
                        key={section.title}
                        className={`rounded-xl border p-4 ${section.color}`}
                      >
                        <h5 className="font-bold text-[#262251]">
                          {section.title}
                        </h5>
                        <p className="mt-1 text-xs leading-5 text-[#737ba6]">
                          {section.description}
                        </p>

                        {section.items.length > 0 ? (
                          <ul className="mt-3 space-y-2">
                            {section.items.map((item, index) => (
                              <li
                                key={`${section.title}-${index}`}
                                className="flex items-start gap-2 text-sm leading-5 text-[#454166]"
                              >
                                <span
                                  className={`mt-1.5 size-2 shrink-0 rounded-full ${section.dot}`}
                                />
                                <span>{getSkillText(item)}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-3 text-sm text-[#737ba6]">
                            {section.empty}
                          </p>
                        )}
                      </section>
                    ))}
                  </div>

                  <div className="rounded-xl border border-[#cdeee7] bg-[#f0fbf8] p-4">
                    <h5 className="font-bold text-[#176b5d]">
                      Your next steps
                    </h5>
                    {priorities.length > 0 ? (
                      <>
                        <p className="mt-1 text-sm leading-5 text-[#39786d]">
                          Consider focusing on these areas first:
                        </p>
                        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-5 text-[#285d54]">
                          {priorities.slice(0, 5).map((item, index) => (
                            <li key={`${index}-${item}`}>{item}</li>
                          ))}
                        </ol>
                      </>
                    ) : (
                      <p className="mt-1 text-sm leading-5 text-[#39786d]">
                        Review the strengths above and keep building projects
                        that demonstrate your skills.
                      </p>
                    )}
                  </div>

                  <SourceNote source={fitAssessment.mindmate_source} />
                  <p className="text-xs leading-5 text-[#737ba6]">
                    This assessment is based on your saved MindMate profile and
                    the opportunity description. It is guidance, not a
                    guarantee of selection.
                  </p>
                </div>
              )
            })()}
          </div>
        )}


        {/* Existing opportunity cards */}
        <div className="mt-[18px] overflow-hidden rounded-[16px] border border-[#e3dcff] bg-white/50">
        {suggestionsError && personalizedSuggestions.length === 0 && (
          <p className="border-b border-[#e6e0ff] px-5 py-3 text-[12px] text-[#737ba6]">
            Personalised suggestions: {suggestionsError} Showing your saved opportunities instead.
            </p>
          )}
        {suggestionsSource && suggestionsSource !== 'nemotron' && suggestionCards.some((card) => card.category === activeCategory) && (
          <p className="border-b border-[#e6e0ff] px-5 py-3 text-[12px] text-[#737ba6]">
            Suggestions below your saved opportunities come from {suggestionsSource === 'offline' ? 'offline matching against your skills, not an AI model' : 'a recorded demo answer'}.
          </p>
        )}
          {stored.error && <p role="alert" className="p-5 text-sm text-rose-600">Could not load opportunities: {stored.error}</p>}
          {storedFitError && <p role="alert" className="px-5 pt-3 text-sm text-rose-600">{storedFitError}</p>}
          {!suggestionsLoaded || stored.loading ? <p role="status" className="p-5 text-sm text-[#737ba6]">Loading opportunities…</p> : visibleOpportunities.length > 0 ? (
            visibleOpportunities.map(
              ({ title, organization, type, Icon, iconColor, tagColor, stored: saved }) => (
                <article
                  key={title}
                  className="border-b border-[#e6e0ff] px-[19px] py-4 last:border-b-0"
                >
                <div className="flex min-h-[70px] items-center justify-between gap-4">
                  <div className="flex min-w-0 items-center gap-[18px]">
                    <span
                      className={`grid size-[47px] shrink-0 place-items-center rounded-[10px] text-white ${iconColor}`}
                    >
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

                  <div className="flex shrink-0 items-center gap-2">
                    {saved?.fit && (
                      <span className={`rounded-full px-3 py-[6px] text-[12px] font-bold ${bandClass(saved.fit.band)}`} title={saved.fit.top_gap ? `Top gap: ${saved.fit.top_gap}` : 'No gaps'}>
                        {saved.fit.score}% {saved.fit.band}
                      </span>
                    )}
                    <span
                      className={`grid min-w-[90px] shrink-0 place-items-center rounded-full px-4 py-[7px] text-[12px] font-semibold ${tagColor}`}
                    >
                      {type}
                    </span>
                    {saved && (
                      <button type="button" onClick={() => void checkStoredFit(saved.id)} disabled={checking === saved.id} className="rounded-full border border-violet-200 bg-white px-3 py-[6px] text-[12px] font-semibold text-[#6332c7] hover:bg-violet-50 disabled:opacity-60">
                        {checking === saved.id ? 'Checking…' : storedFits[saved.id] ? 'Hide fit' : 'Check fit'}
                      </button>
                    )}
                  </div>
                </div>
                {saved?.fit?.top_gap && !storedFits[saved.id] && <p className="mt-1 pl-[65px] text-[12px] text-[#737ba6]">Top gap: {saved.fit.top_gap}</p>}
                {saved && storedFits[saved.id] && (
                  <ul className="mt-3 space-y-1.5 rounded-xl bg-[#f7f5ff] p-3 sm:ml-[65px]">
                    {storedFits[saved.id].per_requirement.map((req) => (
                      <li key={req.requirement} className="flex flex-wrap items-center gap-2 text-[12px] text-[#454166]">
                        <span className={`rounded-md px-1.5 py-[1px] font-semibold ${req.coverage === 'demonstrated' ? 'bg-emerald-100 text-emerald-800' : req.coverage === 'partial' ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'}`}>{req.coverage.replace('_', ' ')}</span>
                        <strong>{req.requirement}</strong>
                        <span className="text-[#737ba6]">{req.weight}{req.mandatory ? ', mandatory' : ''}</span>
                        <RefTags refs={req.evidence_refs} />
                      </li>
                    ))}
                    <li className="pt-1 text-[11px] text-[#737ba6]">Score computed by code from evidence in your memory ({storedFits[saved.id].judged_by}).</li>
                  </ul>
                )}
                </article>
              ),
            )
          ) : (
            <p className="p-5 text-sm text-[#737ba6]">
              No suggestions in this category yet. Try another category or refresh your personalized suggestions.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
export default Scanner
