import client from './client'

export const proxiesApi = {
  getAll: (params = {}) => client.get('/api/proxies/', { params }),
  getById: (id) => client.get(`/api/proxies/${id}`),
  create: (data) => client.post('/api/proxies/', data),
  update: (id, data) => client.put(`/api/proxies/${id}`, data),
  delete: (id) => client.delete(`/api/proxies/${id}`),
  check: (id) => client.post(`/api/proxies/${id}/check`),
  getAccounts: (id) => client.get(`/api/proxies/${id}/accounts`),
}

