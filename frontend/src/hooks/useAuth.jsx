import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { User, LogIn, UserPlus, LogOut, Settings, Star, History, Heart } from 'lucide-react'
import { authAPI } from './useAuthAPI'

const AuthContext = createContext(undefined)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const userData = await authAPI.getMe(token)
      setUser(userData)
    } catch {
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (email, password) => {
    const data = await authAPI.login(email, password)
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
    setUser(data.user)
  }

  const register = async (email, username, password) => {
    const data = await authAPI.register(email, username, password)
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
    setUser(data.user)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Auth button component for header
export function AuthButton() {
  const { user, isLoading, logout } = useAuth()
  const [showMenu, setShowMenu] = useState(false)

  if (isLoading) {
    return <div className="w-8 h-8 rounded-full bg-bg-hover animate-pulse" />
  }

  if (!user) {
    return (
      <button
        onClick={() => window.dispatchEvent(new CustomEvent('auth:open', { detail: 'login' }))}
        className="btn btn-primary btn-sm gap-1"
      >
        <LogIn className="w-4 h-4" />
        <span className="hidden sm:inline">Sign In</span>
      </button>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="btn btn-ghost btn-sm gap-1"
      >
        <User className="w-4 h-4" />
        <span className="hidden sm:inline">{user.username}</span>
      </button>

      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-48 bg-bg-card border border-border rounded-lg shadow-lg py-2 z-20 animate-slide-up">
            <div className="px-3 py-2 border-b border-border text-sm font-medium">
              {user.username}
            </div>
            <div className="px-3 py-1 text-xs text-secondary">
              {user.email}
            </div>
            <hr className="my-1 border-border" />
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('auth:open', { detail: 'profile' }))
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-bg-hover"
            >
              <User className="w-4 h-4" />
              Profile
            </button>
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('auth:open', { detail: 'favorites' }))
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-bg-hover"
            >
              <Heart className="w-4 h-4" />
              Favorites
            </button>
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('auth:open', { detail: 'history' }))
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-bg-hover"
            >
              <History className="w-4 h-4" />
              History
            </button>
            <hr className="my-1 border-border" />
            <button
              onClick={() => {
                logout()
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-bg-hover text-danger"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </>
      )}
    </div>
  )
}