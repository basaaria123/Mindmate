import {
  loadDemoState,
  runReplan,
  savePracticeResult,
  saveWeaknessToMemory,
  type DemoState,
  type PracticeResult,
} from './demoState'

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

export async function getDemoState(): Promise<DemoState> {
  await wait(150)
  return loadDemoState()
}

export async function submitPracticeAnswer(
  answer: string,
): Promise<PracticeResult> {
  const cleanAnswer = answer.trim()

  if (cleanAnswer.length < 10) {
    throw new Error('Please write at least 10 characters before submitting.')
  }

  await wait(400)

  const wordCount = cleanAnswer.split(/\s+/).length
  const hasEnoughDetail = wordCount >= 30

  const result: PracticeResult = {
    answer: cleanAnswer,
    score: hasEnoughDetail ? 72 : 48,
    weakness: 'Performance profiling and validating improvements',
    feedback: hasEnoughDetail
      ? 'Good detail. For this demo, MINDMATE suggests adding how you would profile the page and compare results before and after a change.'
      : 'Try adding more steps. For this demo, MINDMATE suggests describing how you would profile the page and validate a change.',
    submittedAt: new Date().toISOString(),
  }

  savePracticeResult(result)
  return result
}

export async function saveWeaknessToMemoryApi(): Promise<DemoState> {
  await wait(250)

  const saved = saveWeaknessToMemory()
  if (!saved) {
    throw new Error('Submit a practice answer before saving a weakness.')
  }

  return loadDemoState()
}

export async function replanLearningPathApi(): Promise<DemoState> {
  await wait(400)

  const replanned = runReplan()
  if (!replanned) {
    throw new Error('Submit a practice answer and save its weakness to Memory first.')
  }

  return loadDemoState()
}

export async function getTraceEvents() {
  const state = await getDemoState()
  return state.trace
}