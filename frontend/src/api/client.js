import axios from 'axios'

// Если VITE_API_URL не указан или пустой, используем относительные пути (для nginx proxy)
// Иначе используем указанный URL
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8009')

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor для добавления токена к запросам
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor для обработки ошибок
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // 401 - неавторизован, перенаправляем на логин
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        // Перенаправляем на страницу логина только если мы не на ней
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      // Сервер вернул ошибку
      const message = error.response.data?.detail || error.response.data?.message || 'Произошла ошибка'
      return Promise.reject(new Error(message))
    } else if (error.request) {
      // Запрос был отправлен, но ответа не получено
      return Promise.reject(new Error('Сервер не отвечает'))
    } else {
      // Ошибка при настройке запроса
      return Promise.reject(error)
    }
  }
)

export default client

