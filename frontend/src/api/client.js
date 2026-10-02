import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to inject JWT token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401 errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      logger_clear_token()
    }
    return Promise.reject(error)
  }
)

function logger_clear_token() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  // Redirect to login only if not already on the login or register page
  if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
    window.location.href = '/login'
  }
}

export default client
