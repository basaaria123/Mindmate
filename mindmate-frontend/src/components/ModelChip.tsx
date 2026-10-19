import { getBackendStatus } from '../services/backend'
import { useLoad } from '../hooks/useLoad'

/** Footer-style chip showing what is actually answering: Nemotron, deterministic code, or offline mocks. */
export function ModelChip() {
  const status = useLoad(getBackendStatus)
  const label = status.error
    ? 'backend offline'
    : !status.data
      ? 'connecting…'
      : status.data.source === 'mock'
        ? 'offline mocks'
        : status.data.llm_available
          ? 'nemotron | nebius token factory'
          : 'deterministic mode | no model key'
  const live = Boolean(status.data?.llm_available)
  return (
    <span
      className="hidden h-[30px] items-center gap-2 rounded-full border border-violet-200 bg-white/80 px-3 font-mono text-[11px] text-[#5b5f8f] lg:inline-flex"
      title="Which engine is answering right now"
    >
      <span className={`size-[7px] rounded-full ${live ? 'bg-[#76b900]' : status.error ? 'bg-rose-400' : 'bg-amber-400'}`} />
      {label}
    </span>
  )
}
