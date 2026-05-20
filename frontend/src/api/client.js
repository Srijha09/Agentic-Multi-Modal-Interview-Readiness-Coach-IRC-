import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  // Onboarding runs many LLM calls (gaps + plan); default timeout is too short
  timeout: 600000, // 10 minutes
})

api.interceptors.request.use((config) => {
  const storedKey = localStorage.getItem('irc_openai_key')
  if (storedKey) {
    config.headers.Authorization = `Bearer ${storedKey}`
  }
  return config
})

export default api

