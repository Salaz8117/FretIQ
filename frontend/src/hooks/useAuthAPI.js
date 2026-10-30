import axios from 'axios'

const API_BASE = '/api'

export const authAPI = {
  async register(email, username, password) {
    const response = await axios.post(`${API_BASE}/auth/register`, { email, username, password })
    return response.data
  },

  async login(email, password) {
    const response = await axios.post(`${API_BASE}/auth/login`, { email, password })
    return response.data
  },

  async getMe(token) {
    const response = await axios.get(`${API_BASE}/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async getProfile(token) {
    const response = await axios.get(`${API_BASE}/profile`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async getHistory(token, limit = 50) {
    const response = await axios.get(`${API_BASE}/history?limit=${limit}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async getFavorites(token) {
    const response = await axios.get(`${API_BASE}/favorites`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async addFavorite(token, favorite) {
    const response = await axios.post(`${API_BASE}/favorites`, favorite, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async removeFavorite(token, favoriteId) {
    const response = await axios.delete(`${API_BASE}/favorites/${favoriteId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async submitFeedback(token, feedback) {
    const headers = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const response = await axios.post(`${API_BASE}/feedback`, feedback, { headers })
    return response.data
  },

  async getFeedbackStats(token) {
    const response = await axios.get(`${API_BASE}/feedback/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  }
}