import * as mockApi from './mockApi'
import type { DemoEvent, DemoState, PracticeResult } from './demoState'
import type { MemoryEntry, UserProfile } from './mockApi'

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim().replace(/\/$/, '')
export const useMocks = !apiBaseUrl

let latestPracticeResult: PracticeResult | null = null

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!apiBaseUrl) {
    throw new Error('Set VITE_API_BASE_URL to connect to the MindMate API.')
  }

  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
  } catch {
    throw new Error('Could not reach the MindMate API. Check your connection and try again.')
  }

  const body = response.status === 204
    ? null
    : await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : `Request failed (${response.status}). Please try again.`
    throw new Error(detail)
  }

  return body as T
}

function jsonBody(value: unknown): string {
  return JSON.stringify(value)
}

function normalizeMemoryState(value: unknown): DemoState {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    const data = value as Partial<DemoState> & { items?: Array<{ content?: string }> }
    if (Array.isArray(data.memoryNotes)) {
      return {
        latestPractice: latestPracticeResult ?? data.latestPractice ?? null,
        memoryNotes: data.memoryNotes,
        trace: Array.isArray(data.trace) ? data.trace : [],
        originalPlan: Array.isArray(data.originalPlan) ? data.originalPlan : [],
        updatedPlan: Array.isArray(data.updatedPlan) ? data.updatedPlan : null,
        replanReason: data.replanReason ?? null,
      }
    }
    const items = Array.isArray(data.items) ? data.items : []
    return {
      latestPractice: latestPracticeResult,
      memoryNotes: items
        .map((item) => item.content)
        .filter((content): content is string => typeof content === 'string'),
      trace: [],
      originalPlan: [],
      updatedPlan: null,
      replanReason: null,
    }
  }

  if (Array.isArray(value)) {
    return {
      latestPractice: latestPracticeResult,
      memoryNotes: value
        .map((item) => (item && typeof item === 'object' ? (item as { content?: unknown }).content : null))
        .filter((content): content is string => typeof content === 'string'),
      trace: [],
      originalPlan: [],
      updatedPlan: null,
      replanReason: null,
    }
  }

  return {
    latestPractice: latestPracticeResult,
    memoryNotes: [],
    trace: [],
    originalPlan: [],
    updatedPlan: null,
    replanReason: null,
  }
}

/** Uses delayed local mocks by default; set VITE_API_BASE_URL to use FastAPI. */
export async function getProfile(): Promise<UserProfile> {
  return useMocks ? mockApi.getProfile() : request<UserProfile>('/profile')
}

export async function updateProfile(profile: UserProfile): Promise<UserProfile> {
  return useMocks
    ? mockApi.updateProfile(profile)
    : request<UserProfile>('/profile', { method: 'PUT', body: jsonBody(profile) })
}

export async function getMemory(): Promise<DemoState> {
  return useMocks
    ? mockApi.getMemory()
    : normalizeMemoryState(await request<unknown>('/memory'))
}

export async function addMemoryEntry(
  entry: Omit<MemoryEntry, 'id' | 'createdAt'>,
): Promise<MemoryEntry> {
  return useMocks
    ? mockApi.createMemoryEntry(entry)
    : request<MemoryEntry>('/memory', { method: 'POST', body: jsonBody(entry) })
}

export async function submitPracticeAnswer(answer: string, sessionId?: number): Promise<PracticeResult> {
  if (answer.trim().length < 10) {
    throw new Error('Please write at least 10 characters before submitting.')
  }
  const result = useMocks
    ? await mockApi.evaluatePractice(answer)
    : await request<PracticeResult>('/practice/evaluate', {
        method: 'POST',
        // session_id ties the answer to the question the user was shown (POST /practice/start).
        body: jsonBody(sessionId ? { answer: answer.trim(), session_id: sessionId } : { answer: answer.trim() }),
      })
  latestPracticeResult = result
  return result
}

export async function saveWeaknessToMemoryApi(): Promise<DemoState> {
  if (useMocks) return mockApi.saveWeakness()
  if (!latestPracticeResult) {
    throw new Error('Submit a practice answer before saving a weakness to Memory.')
  }

  await request<unknown>('/memory', {
    method: 'POST',
    body: jsonBody({
      type: 'weakness',
      content: `Practice focus: ${latestPracticeResult.weakness}`,
    }),
  })
  return getMemory()
}

export async function replanLearningPathApi(): Promise<DemoState> {
  if (useMocks) return mockApi.replan()
  await request<unknown>('/plans/replan', { method: 'POST', body: jsonBody({}) })
  return getMemory()
}

export async function getTraceEvents(): Promise<DemoEvent[]> {
  if (useMocks) return mockApi.getAgentEvents()
  const response = await request<unknown>('/agent/events')
  const events = Array.isArray(response)
    ? response
    : response && typeof response === 'object' && 'events' in response && Array.isArray(response.events)
      ? response.events
      : []

  return events.map((value, index) => {
    const event = value && typeof value === 'object'
      ? value as Partial<DemoEvent> & { timestamp?: string; message?: string; agent?: string }
      : {}
    const occurredAt = event.occurredAt ?? event.timestamp ?? new Date().toISOString()
    return {
      id: event.id ?? `${occurredAt}-${index}`,
      title: event.title ?? event.agent ?? 'Agent event',
      detail: event.detail ?? event.message ?? '',
      occurredAt,
    }
  })
}

// Kept as a compatibility wrapper for the existing Memory screen.
export async function getDemoState(): Promise<DemoState> {
  return getMemory()
}



// Same configurable base URL as the rest of the API; the local default keeps mock mode working.
// Which engine produced an AI answer: Nemotron, offline analysis (no key, or mock mode), or a
// recorded demo answer. The screens show it so offline results are never passed off as model output.
export type AISource = 'nemotron' | 'offline' | 'recorded'
export type WithSource<T> = T & { mindmate_source?: AISource }


export type AIProfile = {
  education: string | null
  goals: string[]
  skills: string[]
  interests: string[]
  daily_available_minutes: number | null
  learning_preferences: string[]
}

export type AIRequiredSkill = {
  skill_name: string
  importance: string
  is_mandatory: boolean
  description: string
}

export type AIOpportunity = {
  opportunity_title: string
  organization: string | null
  opportunity_type: string | null
  required_skills: AIRequiredSkill[]
  preferred_skills: string[]
  experience_level: string | null
  summary: string
}

export type AIFitSkill = {
  skill_name: string
  user_level: string
  required_level: string
  match_status: string
  explanation: string
}

export type AIFitAssessment = {
  opportunity_title: string
  overall_fit: string
  matching_skills: AIFitSkill[]
  partial_matches: AIFitSkill[]
  missing_skills: AIFitSkill[]
  strengths: string[]
  improvement_areas: string[]
  summary: string
}




async function callMindMateAI<T>(
  path: string,
  body: unknown,
): Promise<WithSource<T>> {
  let response: Response

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error(
      'Could not reach the MindMate API. Check that the backend is running and try again.',
    )
  }

  const responseBody: unknown = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    const detail =
      responseBody &&
      typeof responseBody === 'object' &&
      'detail' in responseBody &&
      typeof responseBody.detail === 'string'
        ? responseBody.detail
        : `AI request failed (${response.status}). Please try again.`

    throw new Error(detail)
  }

  if (responseBody === null || typeof responseBody !== 'object') {
    throw new Error(
      'The MindMate AI server returned an empty or invalid response. Please try again.',
    )
  }

  const source: AISource = response.headers.get('X-MindMate-Cache')
    ? 'recorded'
    : response.headers.get('X-MindMate-Source') === 'offline'
      ? 'offline'
      : 'nemotron'
  return { ...(responseBody as T), mindmate_source: source }
}

// Mock mode has no server: analyse in the browser (services/offlineAnalysis.ts).
async function offline<T>(compute: (module: typeof import('./offlineAnalysis'), curated: CuratedList) => T): Promise<WithSource<T>> {
  const [module, curated] = await Promise.all([import('./offlineAnalysis'), curatedOpportunities()])
  await new Promise((resolve) => window.setTimeout(resolve, 300))
  return { ...compute(module, curated), mindmate_source: 'offline' }
}

type CuratedList = { title: string; org: string | null; type: string; requirements: { name: string }[] }[]

async function curatedOpportunities(): Promise<CuratedList> {
  const snapshot = (await import('./personaSnapshot.json')).default as unknown as { opportunities: CuratedList }
  return snapshot.opportunities
}

export function extractProfile(userMessage: string): Promise<WithSource<AIProfile>> {
  if (useMocks) return offline((m) => m.analyseProfile(userMessage))
  return callMindMateAI<AIProfile>('/profile', {
    user_message: userMessage,
  })
}

export function extractOpportunity(
  opportunityText: string,
): Promise<WithSource<AIOpportunity>> {
  if (useMocks) {
    return offline((m, curated) => m.analyseOpportunity(opportunityText, curated.flatMap((o) => o.requirements.map((r) => r.name))))
  }
  return callMindMateAI<AIOpportunity>('/opportunity', {
    opportunity_text: opportunityText,
  })
}

export function assessFit(
  userProfile: AIProfile,
  opportunity: AIOpportunity,
): Promise<WithSource<AIFitAssessment>> {
  if (useMocks) return offline((m) => m.analyseFit(userProfile, opportunity))
  return callMindMateAI<AIFitAssessment>('/fit', {
    user_profile: userProfile,
    opportunity,
  })
}


export type AIOpportunitySuggestion = {
  title: string
  organization: string | null
  opportunity_type: string
  category: 'Jobs' | 'Projects' | 'Resources' | 'Other'
  explanation: string
}

export type AISuggestionsResponse = {
  suggestions: AIOpportunitySuggestion[]
}

export function getPersonalizedSuggestions(
  userProfile: AIProfile,
): Promise<WithSource<AISuggestionsResponse>> {
  if (useMocks) return offline((m, curated) => m.suggest(userProfile, curated))
  return callMindMateAI<AISuggestionsResponse>(
    '/suggestions',
    { user_profile: userProfile },
  )
}
