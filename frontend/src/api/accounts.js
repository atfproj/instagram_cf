import client from './client'

export const accountsApi = {
  getAll: (params = {}) => client.get('/api/accounts/', { params }),
  getById: (id) => client.get(`/api/accounts/${id}`),
  create: (data) => client.post('/api/accounts/', data),
  update: (id, data) => client.put(`/api/accounts/${id}`, data),
  delete: (id) => client.delete(`/api/accounts/${id}`),
  login: (id) => client.post(`/api/accounts/${id}/login`),
  getStatus: (id) => client.get(`/api/accounts/${id}/status`),
}

