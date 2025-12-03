import client from './client'

export const postsApi = {
  getAll: (params = {}) => client.get('/api/posts/', { params }),
  getById: (id) => client.get(`/api/posts/${id}`),
  create: (formData) => client.post('/api/posts/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  update: (id, data) => client.put(`/api/posts/${id}`, data),
  delete: (id) => client.delete(`/api/posts/${id}`),
  publish: (id) => client.post(`/api/posts/${id}/publish`),
  getExecutions: (id) => client.get(`/api/posts/${id}/executions`),
  getTranslations: (id) => client.post(`/api/posts/${id}/translate`),
  testPost: (postId, accountId) => client.post(`/api/posts/${postId}/test-post/${accountId}`),
}

