import client from './client'

export const accountsApi = {
  getAll: (params = {}) => client.get('/api/accounts/', { params }),
  getById: (id) => client.get(`/api/accounts/${id}`),
  create: (data) => client.post('/api/accounts/', data),
  update: (id, data) => client.put(`/api/accounts/${id}`, data),
  delete: (id) => client.delete(`/api/accounts/${id}`),
  login: (id, data = {}) => client.post(`/api/accounts/${id}/login`, data),
  getStatus: (id) => client.get(`/api/accounts/${id}/status`),
  getProfile: (id) => client.get(`/api/accounts/${id}/profile`),
  updateProfile: (id, data) => client.put(`/api/accounts/${id}/profile`, data),
  setProfilePrivacy: (id, isPrivate) => client.post(`/api/accounts/${id}/profile/privacy`, {
    is_private: isPrivate
  }),
  importSessionFromText: (data) => client.post('/api/accounts/import-session-from-text', data),
}

