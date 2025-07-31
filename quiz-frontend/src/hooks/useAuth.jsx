import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

const API_BASE_URL = 'http://localhost:5001/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  // API helper function
  const apiCall = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error?.message || 'Request failed')
      }

      return data
    } catch (error) {
      console.error('API call failed:', error)
      throw error
    }
  }

  // Load user from token on app start
  useEffect(() => {
    const loadUser = async () => {
      if (!token) {
        setLoading(false)
        return
      }

      try {
        const response = await apiCall('/auth/me')
        setUser(response.data)
      } catch (error) {
        console.error('Failed to load user:', error)
        // Clear invalid token
        localStorage.removeItem('token')
        setToken(null)
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [token])

  const login = async (username, password) => {
    try {
      const response = await apiCall('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })

      const { user: userData, token: userToken } = response.data
      
      localStorage.setItem('token', userToken)
      setToken(userToken)
      setUser(userData)
      
      return { success: true, user: userData }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const register = async (username, email, password, role = 'user') => {
    try {
      const response = await apiCall('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password, role }),
      })

      return { success: true, user: response.data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    loading,
    token,
    login,
    register,
    logout,
    apiCall,
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

export default useAuth

