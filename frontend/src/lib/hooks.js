import { useCallback, useEffect, useRef, useState } from 'react'

// Keeps a ref pointing at the latest value without touching refs during render.
function useLatest(value) {
  const ref = useRef(value)
  useEffect(() => {
    ref.current = value
  })
  return ref
}

// Loads data when the component mounts and again whenever `key` changes.
// Returns { data, error, loading, reload }.
export function useLoad(loader, key) {
  const loaderRef = useLatest(loader)
  const [state, setState] = useState({ data: null, error: null })

  const reload = useCallback(async () => {
    try {
      const data = await loaderRef.current()
      setState({ data, error: null })
      return data
    } catch (error) {
      setState((s) => ({ ...s, error: error.message }))
      return null
    }
  }, [loaderRef])

  useEffect(() => {
    reload()
  }, [key, reload])

  return { ...state, loading: state.data === null && !state.error, reload }
}

// Calls `callback` every `ms` while `active` is true (used while the AI is working).
export function usePolling(callback, active, ms = 4000) {
  const callbackRef = useLatest(callback)
  useEffect(() => {
    if (!active) return undefined
    const id = setInterval(() => callbackRef.current(), ms)
    return () => clearInterval(id)
  }, [active, ms, callbackRef])
}

// Wraps an async action with a busy flag, so buttons can show progress and avoid double taps.
export function useAction(action) {
  const [busy, setBusy] = useState(false)
  const actionRef = useLatest(action)
  const run = useCallback(
    async (...args) => {
      setBusy(true)
      try {
        return await actionRef.current(...args)
      } finally {
        setBusy(false)
      }
    },
    [actionRef],
  )
  return [run, busy]
}
