import { useState } from 'react'
import { useMutation } from 'react-query'
import { accountsApi } from '../api/accounts'

export default function AccountForm({ account, groups, onSuccess }) {
  const [formData, setFormData] = useState({
    username: account?.username || '',
    password: '',
    language: account?.language || 'ru',
    group_id: account?.group_id || '',
    proxy_url: account?.proxy_url || '',
    proxy_type: account?.proxy_type || 'http',
  })

  const createMutation = useMutation(
    (data) => accountsApi.create(data),
    { onSuccess }
  )

  const updateMutation = useMutation(
    ({ id, data }) => accountsApi.update(id, data),
    { onSuccess }
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    const data = { ...formData }
    if (!data.password && account) {
      delete data.password
    }
    if (!data.group_id) {
      delete data.group_id
    }
    if (!data.proxy_url) {
      delete data.proxy_url
      delete data.proxy_type
    }

    if (account) {
      await updateMutation.mutateAsync({ id: account.id, data })
    } else {
      await createMutation.mutateAsync(data)
    }
  }

  const isLoading = createMutation.isLoading || updateMutation.isLoading

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Username *
        </label>
        <input
          type="text"
          required
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          className="input"
          placeholder="instagram_username"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Password {!account && '*'}
        </label>
        <input
          type="password"
          required={!account}
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          className="input"
          placeholder="••••••••"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Язык *
        </label>
        <select
          value={formData.language}
          onChange={(e) => setFormData({ ...formData, language: e.target.value })}
          className="input"
        >
          <option value="ru">Русский</option>
          <option value="en">English</option>
          <option value="es">Español</option>
          <option value="fr">Français</option>
          <option value="de">Deutsch</option>
          <option value="it">Italiano</option>
          <option value="pt">Português</option>
          <option value="pl">Polski</option>
          <option value="tr">Türkçe</option>
          <option value="ar">العربية</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Группа
        </label>
        <select
          value={formData.group_id}
          onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
          className="input"
        >
          <option value="">Без группы</option>
          {groups.map((group) => (
            <option key={group.id} value={group.id}>
              {group.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Прокси URL
        </label>
        <input
          type="text"
          value={formData.proxy_url}
          onChange={(e) => setFormData({ ...formData, proxy_url: e.target.value })}
          className="input"
          placeholder="http://user:pass@ip:port"
        />
      </div>

      {formData.proxy_url && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Тип прокси
          </label>
          <select
            value={formData.proxy_type}
            onChange={(e) => setFormData({ ...formData, proxy_type: e.target.value })}
            className="input"
          >
            <option value="http">HTTP</option>
            <option value="socks5">SOCKS5</option>
          </select>
        </div>
      )}

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
          {isLoading ? 'Сохранение...' : account ? 'Сохранить' : 'Создать'}
        </button>
      </div>
    </form>
  )
}

