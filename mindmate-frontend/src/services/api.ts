import * as mockApi from './mockApi'
import type { DemoEvent, DemoState, PracticeResult } from './demoState'
import type { MemoryEntry, UserProfile } from './mockApi'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim().replace(/\/$/, '')
const useMocks = !apiBaseUrl

let latestPracticeResult: PracticeResult | null = null

async function request<T>(path: string, init?: RequestInit): Promise<T> {
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

export async function submitPracticeAnswer(answer: string): Promise<PracticeResult> {
  if (answer.trim().length < 10) {
    throw new Error('Please write at least 10 characters before submitting.')
  }
  const result = useMocks
    ? await mockApi.evaluatePractice(answer)
    : await request<PracticeResult>('/practice/evaluate', {
        method: 'POST',
        body: jsonBody({ answer: answer.trim() }),
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
