import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const API_BASE = '/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if we have a stored token and validate it
    if (token) {
      validateToken()
    } else {
      setLoading(false)
    }
  }, [])

  const validateToken = async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token invalid, clear it
        logout()
      }
    } catch (error) {
      console.error('Token validation failed:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }

      const data = await response.json()
      setToken(data.access_token)
      setUser(data.user)
      localStorage.setItem('token', data.access_token)
      
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
  }

  const isAdmin = () => {
    return user?.role === 'admin'
  }

  const getAuthHeader = () => {
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAdmin,
    isAuthenticated: !!user,
    getAuthHeader
  }

  return (
    <AuthContext.Provider value={value}>
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

export default AuthContext

