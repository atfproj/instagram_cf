import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8009'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor для обработки ошибок
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
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

