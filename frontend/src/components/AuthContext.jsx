import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'

// Who is signed in: { id, username, role: 'teacher' | 'student', display_name, ... } or null.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined) // undefined = still checking

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null))
    const onSignedOut = () => setUser(null)
    window.addEventListener('chalkbox:signed-out', onSignedOut)
    return () => window.removeEventListener('chalkbox:signed-out', onSignedOut)
  }, [])

  const login = useCallback(async (username, password) => {
    const signedIn = await api.login(username, password)
    setUser(signedIn)
    return signedIn
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ user, checking: user === undefined, login, logout }), [user, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext)
