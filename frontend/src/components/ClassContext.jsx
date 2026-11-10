import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'

// Keeps track of which class the teacher is working with, across every screen.
const ClassContext = createContext(null)
const STORAGE_KEY = 'chalkbox.classId'

function readStoredId() {
  try {
    return Number(localStorage.getItem(STORAGE_KEY)) || null
  } catch {
    return null
  }
}

export function ClassProvider({ children }) {
  const [classes, setClasses] = useState(null)
  const [classId, setClassIdState] = useState(readStoredId)
  const [current, setCurrent] = useState(null)
  const [error, setError] = useState(null)

  const setClassId = useCallback((id) => {
    setClassIdState(id)
    try {
      localStorage.setItem(STORAGE_KEY, String(id))
    } catch {
      /* storage may be unavailable; the choice just won't be remembered */
    }
  }, [])

  useEffect(() => {
    api
      .classes()
      .then((list) => {
        setClasses(list)
        setError(null)
        if (list.length && !list.some((c) => c.id === classId)) setClassId(list[0].id)
      })
      .catch((e) => setError(e.message))
    // Only on first load; switching classes is handled by setClassId.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refresh = useCallback(async () => {
    if (!classId) return null
    try {
      const detail = await api.class(classId)
      setCurrent(detail)
      setError(null)
      return detail
    } catch (e) {
      setError(e.message)
      return null
    }
  }, [classId])

  useEffect(() => {
    refresh()
  }, [refresh])

  const value = useMemo(
    () => ({ classes, classId, setClassId, current, refresh, error }),
    [classes, classId, setClassId, current, refresh, error],
  )
  return <ClassContext.Provider value={value}>{children}</ClassContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useClass = () => useContext(ClassContext)
