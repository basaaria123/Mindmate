const REF = /\[([a-z_]+#\d+)\]/g

/** A memory reference such as ev#4, shown as a small monospace tag. */
export function RefTag({ value }: { value: string }) {
  return (
    <span className="mx-[2px] inline-flex items-center rounded-md border border-violet-200 bg-violet-50 px-1.5 py-[1px] font-mono text-[11px] font-medium text-violet-700" title={`Memory reference ${value}`}>
      {value}
    </span>
  )
}

/** A list of memory references. */
export function RefTags({ refs }: { refs: string[] }) {
  if (refs.length === 0) return null
  return (
    <span className="inline-flex flex-wrap gap-1">
      {refs.map((ref) => <RefTag key={ref} value={ref} />)}
    </span>
  )
}

/** Text in which every "[ref#1]" becomes a reference tag, so cited memory is visible at a glance. */
export function RefText({ text }: { text: string }) {
  const parts: (string | { ref: string })[] = []
  let last = 0
  for (const match of text.matchAll(REF)) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    parts.push({ ref: match[1] })
    last = match.index + match[0].length
  }
  if (last < text.length) parts.push(text.slice(last))
  return <>{parts.map((part, index) => (typeof part === 'string' ? <span key={index}>{part}</span> : <RefTag key={index} value={part.ref} />))}</>
}
