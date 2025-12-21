import client from './client'

export const authApi = {
  login: async (username, password) => {
    const response = await client.post('/api/auth/login', {
      username,
      password,
    })
    // Сохраняем токен
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }
    return response.data
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  getCurrentUser: async () => {
    const response = await client.get('/api/auth/me')
    return response.data
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token')
  },

  getToken: () => {
    return localStorage.getItem('token')
  },

  getUser: () => {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  },
}




