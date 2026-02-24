const API_BASE = import.meta.env.VITE_API_URL || ''

function getHeaders() {
  const headers = {}
  const token = localStorage.getItem('token')
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  })
  if (res.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res
}

export const api = {
  // Auth
  async register(email, password, name) {
    const res = await request('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    })
    const data = await res.json()
    localStorage.setItem('token', data.access_token)
    return data
  },

  async login(email, password) {
    const res = await request('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    localStorage.setItem('token', data.access_token)
    return data
  },

  async getMe() {
    const res = await request('/api/auth/me')
    return res.json()
  },

  logout() {
    localStorage.removeItem('token')
  },

  // Jobs
  async uploadPDF(file) {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/api/jobs/upload`, {
      method: 'POST',
      headers: getHeaders(),
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(err.detail)
    }
    return res.json()
  },

  async createJob(uploadId, config) {
    const res = await request(`/api/jobs/create/${uploadId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    return res.json()
  },

  async listJobs() {
    const res = await request('/api/jobs/')
    return res.json()
  },

  async getJob(jobId) {
    const res = await request(`/api/jobs/${jobId}`)
    return res.json()
  },

  async clearJobs() {
    const res = await request('/api/jobs/clear', { method: 'DELETE' })
    return res.json()
  },

  getDownloadUrl(jobId) {
    return `${API_BASE}/api/jobs/${jobId}/download`
  },
}
