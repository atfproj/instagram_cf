import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { accountsApi } from '../api/accounts'
import { Loader2, Save, RefreshCw, Lock, Unlock } from 'lucide-react'

export default function ProfileModal({ account, onClose }) {
  const [formData, setFormData] = useState({
    biography: '',
    full_name: '',
    external_url: ''
  })
  const queryClient = useQueryClient()

  // Загружаем информацию о профиле
  const { data: profileData, isLoading, refetch } = useQuery(
    ['account-profile', account?.id],
    () => accountsApi.getProfile(account.id).then(r => r.data),
    {
      enabled: !!account,
      onSuccess: (data) => {
        if (data.profile) {
          setFormData({
            biography: data.profile.biography || '',
            full_name: data.profile.full_name || '',
            external_url: data.profile.external_url || ''
          })
        }
      }
    }
  )

  const updateMutation = useMutation(
    (data) => accountsApi.updateProfile(account.id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['account-profile', account.id])
        alert('Профиль успешно обновлён!')
      },
      onError: (error) => {
        alert(`Ошибка: ${error.message}`)
      }
    }
  )

  const privacyMutation = useMutation(
    (isPrivate) => accountsApi.setProfilePrivacy(account.id, isPrivate),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['account-profile', account.id])
        alert('Приватность профиля успешно изменена!')
      },
      onError: (error) => {
        alert(`Ошибка: ${error.message}`)
      }
    }
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    // Отправляем только заполненные поля (не отправляем phone_number и email)
    const updateData = {
      biography: formData.biography || null,
      full_name: formData.full_name || null,
      external_url: formData.external_url || null,
    }
    // Удаляем null значения
    Object.keys(updateData).forEach(key => {
      if (updateData[key] === null || updateData[key] === '') {
        delete updateData[key]
      }
    })
    await updateMutation.mutateAsync(updateData)
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleTogglePrivacy = async () => {
    const currentIsPrivate = profileData?.profile?.is_private
    const newIsPrivate = !currentIsPrivate
    
    if (confirm(`Вы уверены, что хотите сделать профиль ${newIsPrivate ? 'приватным' : 'публичным'}?`)) {
      await privacyMutation.mutateAsync(newIsPrivate)
    }
  }

  if (!account) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Профиль аккаунта</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={refetch}
              className="btn btn-sm btn-outline flex items-center gap-2"
              title="Обновить информацию"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : profileData?.profile ? (
            <>
              {/* Информация о профиле (только для чтения) */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Подписчиков:</span>
                    <span className="ml-2 font-medium">{profileData.profile.follower_count?.toLocaleString() || '—'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Подписок:</span>
                    <span className="ml-2 font-medium">{profileData.profile.following_count?.toLocaleString() || '—'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Постов:</span>
                    <span className="ml-2 font-medium">{profileData.profile.media_count?.toLocaleString() || '—'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Статус:</span>
                    <span className="font-medium">
                      {profileData.profile.is_private ? '🔒 Приватный' : '🌐 Публичный'}
                      {profileData.profile.is_verified && ' ✓'}
                    </span>
                    <button
                      onClick={handleTogglePrivacy}
                      className="btn btn-xs btn-outline flex items-center gap-1"
                      disabled={privacyMutation.isLoading}
                      title={profileData.profile.is_private ? 'Сделать профиль публичным' : 'Сделать профиль приватным'}
                    >
                      {privacyMutation.isLoading ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : profileData.profile.is_private ? (
                        <>
                          <Unlock className="h-3 w-3" />
                          Открыть
                        </>
                      ) : (
                        <>
                          <Lock className="h-3 w-3" />
                          Закрыть
                        </>
                      )}
                    </button>
                  </div>
                </div>
                {profileData.profile.profile_pic_url && (
                  <div className="mt-4">
                    <img
                      src={profileData.profile.profile_pic_url}
                      alt="Profile"
                      className="w-24 h-24 rounded-full object-cover"
                    />
                  </div>
                )}
              </div>

              {/* Форма редактирования */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Полное имя
                  </label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => handleChange('full_name', e.target.value)}
                    className="input"
                    placeholder="Введите полное имя"
                    maxLength={30}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Описание профиля (Bio)
                  </label>
                  <textarea
                    value={formData.biography}
                    onChange={(e) => handleChange('biography', e.target.value)}
                    className="input"
                    rows={4}
                    placeholder="Введите описание профиля"
                    maxLength={150}
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {formData.biography.length} / 150 символов
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Внешняя ссылка
                  </label>
                  <input
                    type="url"
                    value={formData.external_url}
                    onChange={(e) => handleChange('external_url', e.target.value)}
                    className="input"
                    placeholder="https://example.com"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={onClose}
                    className="btn btn-outline"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary flex items-center gap-2"
                    disabled={updateMutation.isLoading}
                  >
                    {updateMutation.isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Сохранение...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4" />
                        Сохранить
                      </>
                    )}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">Не удалось загрузить информацию о профиле</p>
              {profileData?.message && (
                <p className="text-sm text-red-600 mt-2">{profileData.message}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

