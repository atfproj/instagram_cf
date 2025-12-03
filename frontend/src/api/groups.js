import client from './client'

export const groupsApi = {
  getAll: () => client.get('/api/groups/'),
  getById: (id) => client.get(`/api/groups/${id}`),
  create: (data) => client.post('/api/groups/', data),
  update: (id, data) => client.put(`/api/groups/${id}`, data),
  delete: (id) => client.delete(`/api/groups/${id}`),
  getAccounts: (id) => client.get(`/api/groups/${id}/accounts`),
}

