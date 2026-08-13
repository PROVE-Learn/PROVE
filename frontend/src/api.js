import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''
const api = axios.create({ baseURL: `${API_BASE}/api/v1` })

// attach token from localStorage if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('prove_token')
  if (token) config.headers = { ...(config.headers || {}), Authorization: `Bearer ${token}` }
  return config
})

export async function getMentorSummary() {
  const r = await api.get('/learning/mentor-summary')
  return r.data
}

export async function login(email, password) {
  const r = await api.post('/auth/login', { email, password })
  const token = r.data.access_token
  if (token) localStorage.setItem('prove_token', token)
  return r.data
}

export function logout() {
  localStorage.removeItem('prove_token')
}

export default api

export async function saveWeeklyPlan(plan) {
  const r = await api.post('/learning/plan/weekly', plan)
  return r.data
}

export async function getWeeklyPlan() {
  const r = await api.get('/learning/plan/weekly')
  return r.data
}

export async function deleteWeeklyPlan() {
  const r = await api.delete('/learning/plan/weekly')
  return r.data
}

export async function completeMilestone(dayIndex) {
  const r = await api.post(`/learning/plan/weekly/milestones/${dayIndex}/complete`)
  return r.data
}

// Admin APIs
export async function adminListWeeklyPlans() {
  const r = await api.get('/admin/learning/plans')
  return r.data
}

export async function adminDeleteUserPlan(userId){
  const r = await api.delete(`/admin/learning/plan/${userId}`)
  return r.data
}
