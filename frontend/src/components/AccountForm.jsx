import { useState } from 'react'
import { useMutation, useQuery } from 'react-query'
import { accountsApi } from '../api/accounts'
import { proxiesApi } from '../api/proxies'

export default function AccountForm({ account, groups, onSuccess }) {
  const [formData, setFormData] = useState({
    username: account?.username || '',
    password: '',
    language: account?.language || 'ru',
    group_id: account?.group_id || '',
    proxy_id: account?.proxy_id || '',
  })

  // Загружаем доступные прокси при создании нового аккаунта
  const { data: availableProxies } = useQuery(
    'availableProxies',
    () => proxiesApi.getAvailable().then(r => r.data),
    { enabled: !account }
  )

  // Загружаем все прокси при редактировании (чтобы можно было выбрать любой или отвязать)
  const { data: allProxies } = useQuery(
    'allProxies',
    () => proxiesApi.getAll().then(r => r.data),
    { enabled: !!account }
  )

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
    // При редактировании, если proxy_id пустой, отправляем null для отвязки
    if (!data.proxy_id) {
      if (account && account.proxy_id) {
        // Если у аккаунта был прокси, а теперь нет - отвязываем
        data.proxy_id = null
      } else {
        delete data.proxy_id
      }
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
          {Array.isArray(groups) && groups.map((group) => (
            <option key={group.id} value={group.id}>
              {group.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Прокси
        </label>
        <select
          value={formData.proxy_id}
          onChange={(e) => setFormData({ ...formData, proxy_id: e.target.value })}
          className="input"
        >
          <option value="">
            {account ? 'Отвязать прокси' : 'Без прокси (будет назначен автоматически)'}
          </option>
          {account ? (
            // При редактировании показываем все прокси
            (allProxies || []).map((proxy) => (
              <option key={proxy.id} value={proxy.id}>
                {proxy.url} ({proxy.type}) {proxy.id === account.proxy_id ? '(текущий)' : ''}
              </option>
            ))
          ) : (
            // При создании показываем только доступные
            (availableProxies || []).map((proxy) => (
              <option key={proxy.id} value={proxy.id}>
                {proxy.url} ({proxy.type})
              </option>
            ))
          )}
        </select>
        {!account && availableProxies && availableProxies.length === 0 && (
          <p className="text-sm text-gray-500 mt-1">
            Нет доступных прокси. Все прокси уже используются.
          </p>
        )}
        {account && account.proxy_id && (
          <p className="text-sm text-blue-600 mt-1">
            Текущий прокси будет отвязан, если выберите "Отвязать прокси"
          </p>
        )}
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
          {isLoading ? 'Сохранение...' : account ? 'Сохранить' : 'Создать'}
        </button>
      </div>
    </form>
  )
}

