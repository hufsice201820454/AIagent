import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  const setToken = (newToken) => {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    } else {
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    }
  }

  const login = async (email, password) => {
    // FastAPI OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const body = new URLSearchParams()
    body.append('username', email)
    body.append('password', password)

    const response = await axios.post('/api/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    setToken(response.data.access_token)
    await fetchUser()
    return response.data
  }

  const register = async (userData) => {
    const response = await axios.post('/api/auth/register', userData)
    return response.data
  }

  const logout = () => {
    setToken(null)
    user.value = null
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const response = await axios.get('/api/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  // Initialize axios defaults if token exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    fetchUser()
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser
  }
})
