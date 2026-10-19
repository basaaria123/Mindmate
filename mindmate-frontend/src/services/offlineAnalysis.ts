// In-browser offline analysis for mock mode (no VITE_API_BASE_URL): the same rules as the
// backend's app/services/offline_ai.py, so the AI screens work without a server. Results are
// marked mindmate_source: 'offline' and the screens say so; they are never shown as model output.
// Keep BASE_SKILLS and the hint lists in step with offline_ai.py (tests/test_offline_ai.py checks).
import type {
  AIFitAssessment,
  AIFitSkill,
  AIOpportunity,
  AIOpportunitySuggestion,
  AIProfile,
  AISuggestionsResponse,
} from './api'

export const BASE_SKILLS = [
  'Python', 'SQL', 'Git', 'Docker', 'Kubernetes', 'Linux', 'Statistics', 'Machine learning',
  'Deep learning', 'Model evaluation', 'Data structures', 'Algorithms', 'Data visualisation',
  'Data analysis', 'Pandas', 'NumPy', 'scikit-learn', 'PyTorch', 'TensorFlow',
  'Large language models', 'AI agents', 'Natural language processing', 'Computer vision',
  'REST APIs', 'JSON', 'FastAPI', 'Flask', 'Cloud', 'AWS', 'Azure', 'GCP', 'C++', 'Java',
  'JavaScript', 'TypeScript', 'React', 'Node.js', 'HTML', 'CSS', 'Excel', 'Power BI',
  'Tableau', 'Spark', 'MLOps', 'Technical writing', 'Communication', 'Problem solving',
]

const ALIASES: Record<string, string> = {
  llm: 'Large language models', llms: 'Large language models', sklearn: 'scikit-learn',
  nlp: 'Natural language processing', ml: 'Machine learning', dl: 'Deep learning',
  k8s: 'Kubernetes', 'rest api': 'REST APIs', restful: 'REST APIs', apis: 'REST APIs',
  dsa: 'Data structures', 'data visualization': 'Data visualisation',
  'google cloud': 'GCP', 'amazon web services': 'AWS', 'problem-solving': 'Problem solving',
}

export const MANDATORY_HINTS = ['required', 'require', 'must', 'mandatory', 'essential', 'need', 'should have']
export const PREFERRED_HINTS = ['preferred', 'nice to have', 'good to have', 'bonus', 'plus', 'desirable', 'advantage',
  'familiarity', 'optional']
const ROLE_NOUNS = ['Engineer', 'Intern', 'Internship', 'Developer', 'Scientist', 'Analyst', 'Researcher',
  'Designer', 'Manager', 'Fellow', 'Fellowship', 'Associate', 'Architect', 'Consultant',
  'Specialist', 'Hackathon', 'Trainee', 'Apprentice']
const GENERIC_HEADINGS = new Set(['about', 'about the role', 'about us', 'role', 'overview', 'description',
  'job description', 'responsibilities', 'requirements', 'qualifications', 'skills', 'success criteria',
  'educational qualifications', 'who we are', 'what you will do', 'benefits'])

// --- skill matching (port of app/scoring/fit.py skill_matches) -----------------------------
const STOP = new Set(['and', 'or', 'the', 'of', 'with', 'in', 'for', 'a', 'an', 'to', 'basic', 'basics', 'knowledge'])
const GENERIC = new Set(['learning', 'data', 'fundamentals', 'fundamental', 'skills', 'skill', 'experience',
  'engineering', 'development', 'analysis', 'programming', 'advanced', 'intro', 'introduction', 'practice', 'basic'])

const escape = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const containsPhrase = (longer: string, shorter: string) =>
  new RegExp(`(?<![a-z0-9+#])${escape(shorter)}(?![a-z0-9+#])`).test(longer)

function significant(text: string): Set<string> {
  const words = new Set<string>()
  for (const token of text.toLowerCase().split(/[^a-z0-9+#]+/)) {
    if (!token || STOP.has(token) || GENERIC.has(token)) continue
    words.add(token.length > 3 && token.endsWith('s') && !token.endsWith('ss') ? token.slice(0, -1) : token)
  }
  return words
}

export function skillMatches(requirement: string, skillName: string): boolean {
  const req = requirement.toLowerCase().split(/\s+/).filter(Boolean).join(' ')
  const name = skillName.toLowerCase().split(/\s+/).filter(Boolean).join(' ')
  if (!req || !name) return false
  if (req === name || containsPhrase(req, name) || containsPhrase(name, req)) return true
  const a = significant(req)
  const b = significant(name)
  if (!a.size || !b.size) return false
  const [shorter, longer] = a.size <= b.size ? [a, b] : [b, a]
  return [...shorter].every((word) => longer.has(word))
}

// --- extraction -------------------------------------------------------------------------------
export function sentences(text: string): string[] {
  const parts: string[] = []
  for (const raw of text.split('\n')) {
    const line = raw.trim().replace(/^[-*•#\s]+|[-*•#\s]+$/g, '').trim()
    if (line) parts.push(...line.split(/(?<=[.;!?])\s+/).map((p) => p.trim()).filter(Boolean))
  }
  return parts
}

function mentions(name: string, sentence: string): boolean {
  if (skillMatches(name, sentence)) return true
  const lowered = ` ${sentence.toLowerCase()} `
  return Object.entries(ALIASES).some(([alias, target]) =>
    target === name && new RegExp(`(?<![a-z0-9+#])${escape(alias)}(?![a-z0-9+#])`).test(lowered))
}

function vocabulary(extra: string[]): string[] {
  return [...new Set([...BASE_SKILLS, ...extra].filter(Boolean))]
}

function findSkills(text: string, extra: string[] = []): { name: string; mentions: string[] }[] {
  const parts = sentences(text)
  const found: { index: number; name: string; mentions: string[] }[] = []
  for (const name of vocabulary(extra)) {
    const hits = parts.filter((sentence) => mentions(name, sentence))
    if (hits.length && !found.some((other) => skillMatches(name, other.name))) {
      found.push({ index: parts.indexOf(hits[0]), name, mentions: hits })
    }
  }
  const position = (item: { name: string; mentions: string[] }) => {
    const at = item.mentions[0].toLowerCase().indexOf(item.name.toLowerCase())
    return at >= 0 ? at : item.mentions[0].length
  }
  return found.sort((a, b) => a.index - b.index || position(a) - position(b))
}

const has = (hints: string[], sentence: string) => hints.some((hint) => sentence.toLowerCase().includes(hint))

export function guessTitle(text: string): string {
  const lines = text.split('\n')
    .map((line) => line.trim().replace(/^[#*\-•\s]+|[#*\-•\s]+$/g, '').trim())
    .filter((line) => line && !GENERIC_HEADINGS.has(line.toLowerCase().replace(/:$/, '')))
  if (lines.length && lines[0].length <= 80 && !/[.!?]\s/.test(`${lines[0]} `)) return lines[0]
  const match = new RegExp(`((?:[A-Z][\\w/&+.\\-]*\\s+){0,5}(?:${ROLE_NOUNS.join('|')})s?)\\b`).exec(text)
  if (match) {
    const words = match[1].split(/\s+/).filter(Boolean)
    while (words.length && ['a', 'an', 'the', 'we', 'our', 'seeking', 'hiring', 'join'].includes(words[0].toLowerCase())) words.shift()
    if (words.length) return words.join(' ')
  }
  if (lines.length) return lines[0].length <= 80 ? lines[0] : `${lines[0].slice(0, 77).trimEnd()}...`
  return 'Untitled opportunity'
}

function guessType(text: string): string {
  const lowered = text.toLowerCase()
  for (const kind of ['internship', 'hackathon', 'fellowship', 'scholarship', 'competition']) {
    if (lowered.includes(kind) || (kind === 'internship' && /\bintern\b/.test(lowered))) return kind
  }
  return 'job'
}

function guessOrganization(text: string): string | null {
  const labelled = /^\s*(?:company|organi[sz]ation|employer)\s*[:-]\s*(.+)$/im.exec(text)
  if (labelled) return labelled[1].trim().slice(0, 120)
  const at = /\bat[ \t]+([A-Z][\w&.]*(?:[ \t]+[A-Z][\w&.]*){0,3})/.exec(text)
  return at ? at[1].trim() : null
}

function guessExperience(text: string): string {
  const years = /(\d+\s*(?:[–-]|to)\s*\d+|\d+\+?)\s*years?/i.exec(text)
  const lowered = text.toLowerCase()
  if (years) return `${years[1].split(/\s+/).join(' ')} years`
  if (['fresher', 'entry level', 'entry-level', 'junior', 'student', 'graduate'].some((w) => lowered.includes(w))) return 'entry level'
  if (lowered.includes('senior')) return 'experienced'
  return 'not specified'
}

export function analyseOpportunity(text: string, extraVocabulary: string[] = []): AIOpportunity {
  const requirements = findSkills(text, extraVocabulary).map(({ name, mentions: hits }) => {
    const required = hits.filter((s) => has(MANDATORY_HINTS, s) && !has(PREFERRED_HINTS, s))
    const preferred = hits.filter((s) => has(PREFERRED_HINTS, s))
    if (required.length) return { skill_name: name, importance: 'High', is_mandatory: true, description: 'Listed as required (keyword match).' }
    if (preferred.length) return { skill_name: name, importance: 'Low', is_mandatory: false, description: 'Listed as preferred or an advantage (keyword match).' }
    return { skill_name: name, importance: 'Medium', is_mandatory: false, description: 'Mentioned in the posting (keyword match).' }
  })
  const parts = sentences(text)
  return {
    opportunity_title: guessTitle(text),
    organization: guessOrganization(text),
    opportunity_type: guessType(text),
    required_skills: requirements,
    preferred_skills: requirements.filter((r) => r.importance === 'Low').map((r) => r.skill_name),
    experience_level: guessExperience(text),
    summary: parts.slice(0, 2).join(' ').slice(0, 400) || 'No description given.',
  }
}

const PREFERENCES: Record<string, string> = {
  projects: 'Hands-on projects', 'hands-on': 'Hands-on projects', video: 'Videos', videos: 'Videos',
  reading: 'Reading', articles: 'Reading', books: 'Reading', practice: 'Practice questions',
  mentor: 'Mentoring', course: 'Structured courses', courses: 'Structured courses',
}

export function analyseProfile(message: string): AIProfile {
  const parts = sentences(message)
  const lowered = message.toLowerCase()
  const education = parts.find((s) =>
    /\b(b\.?\s?tech|b\.?e\b|bsc|b\.sc|bachelor|master|m\.?tech|msc|phd|degree|student|university|college|year)\b/i.test(s)) ?? ''
  const goals = parts.filter((s) => /\b(want to|goal|aim|become|hoping to|looking for|plan to|would like to|land)\b/i.test(s))
  const interests: string[] = []
  for (const s of parts) {
    const match = /\binterested in\s+(.+)/i.exec(s)
    if (match) interests.push(...match[1].split(/,|\band\b/).map((i) => i.trim().replace(/^[\s.]+|[\s.]+$/g, '')).filter(Boolean))
  }
  let minutes: number | null = null
  const time = /(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?)\b/.exec(lowered)
  if (time) minutes = time[2].startsWith('h') ? Math.trunc(Number(time[1]) * 60) : Math.trunc(Number(time[1]))
  const preferences = [...new Set(Object.entries(PREFERENCES)
    .filter(([word]) => new RegExp(`\\b${escape(word)}\\b`).test(lowered)).map(([, label]) => label))]
  const skillText = parts
    .filter((s) => !goals.includes(s) && !/\b(interested in|want to learn|hope to learn|learn more)\b/i.test(s))
    .join(' ')
  return {
    education: education.slice(0, 200) || 'Not stated',
    goals: goals.slice(0, 5),
    skills: findSkills(skillText).map((item) => item.name),
    interests: interests.slice(0, 8),
    daily_available_minutes: minutes,
    learning_preferences: preferences,
  }
}

function weightOf(importance: string): number {
  const text = importance.trim().toLowerCase()
  return text.startsWith('h') ? 3 : text.startsWith('l') ? 1 : 2
}

export function analyseFit(profile: AIProfile, opportunity: AIOpportunity): AIFitAssessment {
  const matching: AIFitSkill[] = []
  const missing: AIFitSkill[] = []
  let covered = 0
  let total = 0
  for (const req of opportunity.required_skills) {
    const weight = weightOf(req.importance)
    total += weight
    const skill = profile.skills.find((s) => skillMatches(req.skill_name, s))
    const requiredLevel = req.is_mandatory ? 'required' : req.importance.toLowerCase()
    if (skill) {
      covered += weight
      matching.push({ skill_name: req.skill_name, user_level: 'listed in profile', required_level: requiredLevel,
        match_status: 'match',
        explanation: `Your profile lists ${skill}. Add evidence (a project or result) to make this count in the evidence-based fit score.` })
    } else {
      missing.push({ skill_name: req.skill_name, user_level: 'not listed', required_level: requiredLevel,
        match_status: 'missing', explanation: `${req.skill_name} is not in your profile.` })
    }
  }
  const score = total ? Math.round((100 * covered) / total) : 0
  const band = score >= 75 ? 'Strong' : score >= 50 ? 'Moderate' : 'Weak'
  return {
    opportunity_title: opportunity.opportunity_title,
    overall_fit: band,
    matching_skills: matching,
    partial_matches: [],
    missing_skills: missing,
    strengths: matching.slice(0, 5).map((m) => `${m.skill_name} is listed in your profile`),
    improvement_areas: missing.slice(0, 5).map((m) => `Build and show evidence of ${m.skill_name}`),
    summary: opportunity.required_skills.length
      ? `Offline estimate: your profile lists ${matching.length} of ${opportunity.required_skills.length} skills this opportunity asks for (${score}%, ${band.toLowerCase()} by skill weight).`
      : 'No skill requirements were found in this opportunity, so fit could not be estimated.',
  }
}

type CuratedOpportunity = { title: string; org: string | null; type: string; requirements: { name: string }[] }

export function suggest(profile: AIProfile, curated: CuratedOpportunity[]): AISuggestionsResponse {
  const words = new Set([...profile.goals, ...profile.interests, ...profile.skills]
    .flatMap((text) => text.toLowerCase().match(/[a-z+#]+/g) ?? []))
  const haveSkill = (name: string) => profile.skills.some((s) => skillMatches(name, s))
  const overlap = (data: CuratedOpportunity) => {
    const names = data.requirements.map((r) => r.name)
    const titleWords = data.title.toLowerCase().match(/[a-z+#]+/g) ?? []
    return names.filter(haveSkill).length / Math.max(1, names.length) + 0.2 * titleWords.filter((w) => words.has(w)).length
  }
  const ranked = [...curated].sort((a, b) => overlap(b) - overlap(a))
  const explain = (data: CuratedOpportunity) => {
    const names = data.requirements.map((r) => r.name)
    const have = names.filter(haveSkill)
    const lacking = names.filter((n) => !have.includes(n))
    if (have.length) {
      return `Uses skills you listed (${have.slice(0, 3).join(', ')})${lacking.length ? `; you would still need ${lacking.slice(0, 2).join(', ')}.` : '.'}`
    }
    return `Asks for ${names.slice(0, 3).join(', ')}, which would extend your current skills.`
  }
  const jobs = ranked.filter((d) => d.type === 'internship').slice(0, 3)
  const other = ranked.filter((d) => d.type !== 'internship').slice(0, 3)
  other.push(...ranked.filter((d) => !jobs.includes(d) && !other.includes(d)).slice(0, 3 - other.length))
  const fallback = ['Model evaluation', 'Statistics', 'Git', 'SQL', 'Data structures', 'Docker']
  const gaps = ranked.slice(0, 4).flatMap((d) => d.requirements.map((r) => r.name)).filter((n) => !haveSkill(n))
  const focus = [...new Set([...gaps, ...fallback])].filter((n) => !haveSkill(n)).slice(0, 3)
  focus.push(...fallback.filter((n) => !focus.includes(n)).slice(0, 3 - focus.length))
  const strongest = profile.skills[0] ?? 'Python'
  const card = (data: CuratedOpportunity, category: AIOpportunitySuggestion['category']): AIOpportunitySuggestion => ({
    title: data.title, organization: data.org, opportunity_type: data.type, category, explanation: explain(data),
  })
  return {
    suggestions: [
      ...jobs.map((d) => card(d, 'Jobs')),
      ...focus.map((skill): AIOpportunitySuggestion => ({
        title: `Portfolio project: ${skill}`, organization: null, opportunity_type: 'project', category: 'Projects',
        explanation: `A small, finished project would give you evidence of ${skill}${strongest !== skill ? `, combined with ${strongest}` : ''}.`,
      })),
      ...focus.map((skill): AIOpportunitySuggestion => ({
        title: `Study guide: ${skill}`, organization: null, opportunity_type: 'learning resource', category: 'Resources',
        explanation: `${skill} appears in the opportunities that best match your profile.`,
      })),
      ...other.map((d) => card(d, 'Other')),
    ],
  }
}
