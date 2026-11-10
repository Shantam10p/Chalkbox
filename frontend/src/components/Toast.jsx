import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'

const ToastContext = createContext(() => {})

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null)
  const timer = useRef(null)

  const show = useCallback((message, tone = 'default') => {
    clearTimeout(timer.current)
    setToast({ message, tone, id: Date.now() })
    timer.current = setTimeout(() => setToast(null), 3500)
  }, [])

  const value = useMemo(() => show, [show])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-wrap" aria-live="assertive">
        {toast && (
          <div key={toast.id} className={`toast${toast.tone === 'error' ? ' error' : ''}`}>
            {toast.message}
          </div>
        )}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(ToastContext)
