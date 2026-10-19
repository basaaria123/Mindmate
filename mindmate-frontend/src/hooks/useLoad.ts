import { useCallback, useEffect, useState } from 'react'

type LoadState<T> = { data: T | null; error: string | null; loading: boolean }

/** Load data once (and again on reload()). Pass a stable function: a module function or useCallback. */
export function useLoad<T>(load: () => Promise<T>) {
  const [state, setState] = useState<LoadState<T>>({ data: null, error: null, loading: true })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let current = true
    load()
      .then((data) => {
        if (current) setState({ data, error: null, loading: false })
      })
      .catch((error: unknown) => {
        if (current) setState({ data: null, error: error instanceof Error ? error.message : 'Could not load data.', loading: false })
      })
    return () => {
      current = false
    }
  }, [load, version])

  const reload = useCallback(() => setVersion((value) => value + 1), [])
  const setData = useCallback((data: T) => setState({ data, error: null, loading: false }), [])
  return { ...state, reload, setData }
}
