import React, { useState } from 'react'
import { useMutation, useQueryClient, useQuery } from 'react-query'
import { accountsApi } from '../api/accounts'
import { groupsApi } from '../api/groups'
import { proxiesApi } from '../api/proxies'

export default function ImportSessionModal({ isOpen, onClose, onSuccess }) {
  const queryClient = useQueryClient()
  const [sessionText, setSessionText] = useState('')
  const [selectedGroupId, setSelectedGroupId] = useState('')
  const [selectedProxyId, setSelectedProxyId] = useState('')
  const [validate, setValidate] = useState(false)
  const [error, setError] = useState(null)

  // Загрузка групп
  const { data: groupsData } = useQuery('groups', groupsApi.getAll)

  // Загрузка доступных прокси
  const { data: proxiesData } = useQuery('proxies-available', () => proxiesApi.getAvailable())

  const importMutation = useMutation(
    (data) => accountsApi.importSessionFromText(data),
    {
      onSuccess: (response) => {
        queryClient.invalidateQueries('accounts')
        onSuccess?.(response.data)
        handleClose()
      },
      onError: (err) => {
        setError(err.response?.data?.detail || 'Ошибка импорта сессии')
      }
    }
  )

  const handleClose = () => {
    setSessionText('')
    setSelectedGroupId('')
    setSelectedProxyId('')
    setValidate(false)
    setError(null)
    onClose()
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)

    if (!sessionText.trim()) {
      setError('Введите данные сессии')
      return
    }

    importMutation.mutate({
      session_text: sessionText.trim(),
      group_id: selectedGroupId || null,
      proxy_id: selectedProxyId || null,
      validate_session: validate
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Загрузка сессии</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Текстовое поле для сессии */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Данные сессии
                <span className="text-xs text-gray-500 ml-2">
                  (Формат: username:password|User-Agent|device_ids|cookies||email)
                </span>
              </label>
              <textarea
                value={sessionText}
                onChange={(e) => setSessionText(e.target.value)}
                placeholder="Вставьте строку с данными аккаунта..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows="6"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                Пример: lerchek___:password|Instagram 359.2.0.64.89 Android...|android-xxx;uuid1;uuid2;uuid3|Authorization=...||
              </p>
            </div>

            {/* Группа */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Группа (опционально)
              </label>
              <select
                value={selectedGroupId}
                onChange={(e) => setSelectedGroupId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Без группы</option>
                {groupsData?.data?.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Прокси */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Прокси (опционально)
              </label>
              <select
                value={selectedProxyId}
                onChange={(e) => setSelectedProxyId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Без прокси</option>
                {proxiesData?.data?.map((proxy) => (
                  <option key={proxy.id} value={proxy.id}>
                    {proxy.url.split('@')[1] || proxy.url} ({proxy.type})
                  </option>
                ))}
              </select>
            </div>

            {/* Валидация */}
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={validate}
                  onChange={(e) => setValidate(e.target.checked)}
                  className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  Валидировать сессию после импорта
                  <span className="text-xs text-gray-500 ml-1">(может быть медленно)</span>
                </span>
              </label>
            </div>

            {/* Информация */}
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>💡 Преимущества:</strong> Обходит все проверки Instagram (email, SMS), 
                т.к. использует готовую сессию вместо логина.
              </p>
            </div>

            {/* Ошибка */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Кнопки */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                disabled={importMutation.isPending}
              >
                Отмена
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
                disabled={importMutation.isPending}
              >
                {importMutation.isPending ? 'Импорт...' : 'Импортировать'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

