import { useState } from 'react'
import { useMutation } from 'react-query'
import { proxiesApi } from '../api/proxies'

export default function ProxyForm({ proxy, onSuccess }) {
  const [formData, setFormData] = useState({
    url: proxy?.url || '',
    type: proxy?.type || 'http',
    country: proxy?.country || '',
  })

  const createMutation = useMutation(
    (data) => proxiesApi.create(data),
    { onSuccess }
  )

  const updateMutation = useMutation(
    ({ id, data }) => proxiesApi.update(id, data),
    { onSuccess }
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (proxy) {
      await updateMutation.mutateAsync({ id: proxy.id, data: formData })
    } else {
      await createMutation.mutateAsync(formData)
    }
  }

  const isLoading = createMutation.isLoading || updateMutation.isLoading

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          URL прокси *
        </label>
        <input
          type="text"
          required
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          className="input"
          placeholder="http://user:pass@ip:port"
        />
        <p className="mt-1 text-xs text-gray-500">
          Формат: http://user:pass@ip:port или socks5://user:pass@ip:port
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Тип прокси *
        </label>
        <select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value })}
          className="input"
        >
          <option value="http">HTTP</option>
          <option value="socks5">SOCKS5</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Страна
        </label>
        <input
          type="text"
          value={formData.country}
          onChange={(e) => setFormData({ ...formData, country: e.target.value })}
          className="input"
          placeholder="US, RU, DE..."
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onSuccess}
          className="btn btn-secondary"
          disabled={isLoading}
        >
          Отмена
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Сохранение...' : proxy ? 'Сохранить' : 'Создать'}
        </button>
      </div>
    </form>
  )
}

