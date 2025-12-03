import { useState } from 'react'
import { useMutation } from 'react-query'
import { postsApi } from '../api/posts'
import { Upload } from 'lucide-react'

export default function PostForm({ groups, onSuccess }) {
  const [formData, setFormData] = useState({
    caption: '',
    original_language: 'ru',
    target_groups: [],
    media_type: 'photo',
  })
  const [files, setFiles] = useState([])

  const createMutation = useMutation(
    (formDataToSend) => postsApi.create(formDataToSend),
    { onSuccess }
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (files.length === 0) {
      alert('Выберите хотя бы один файл')
      return
    }

    const formDataToSend = new FormData()
    
    // Добавляем файлы
    files.forEach((file) => {
      formDataToSend.append('files', file)
    })
    
    // Добавляем остальные данные
    formDataToSend.append('caption', formData.caption)
    formDataToSend.append('original_language', formData.original_language)
    formDataToSend.append('media_type', formData.media_type)
    formDataToSend.append('target_groups', JSON.stringify(formData.target_groups))

    await createMutation.mutateAsync(formDataToSend)
  }

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files)
    setFiles(selectedFiles)
  }

  const toggleGroup = (groupId) => {
    setFormData({
      ...formData,
      target_groups: formData.target_groups.includes(groupId)
        ? formData.target_groups.filter(id => id !== groupId)
        : [...formData.target_groups, groupId]
    })
  }

  const isLoading = createMutation.isLoading

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Медиа файлы *
        </label>
        <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-gray-400">
          <div className="space-y-1 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <div className="flex text-sm text-gray-600">
              <label htmlFor="file-upload" className="relative cursor-pointer rounded-md font-medium text-primary-600 hover:text-primary-500">
                <span>Загрузить файлы</span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  multiple
                  accept="image/*,video/*"
                  onChange={handleFileChange}
                  className="sr-only"
                />
              </label>
              <p className="pl-1">или перетащите сюда</p>
            </div>
            <p className="text-xs text-gray-500">PNG, JPG, MP4 до 10MB</p>
            {files.length > 0 && (
              <p className="text-xs text-primary-600 mt-2">
                Выбрано файлов: {files.length}
              </p>
            )}
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Тип медиа *
        </label>
        <select
          value={formData.media_type}
          onChange={(e) => setFormData({ ...formData, media_type: e.target.value })}
          className="input"
        >
          <option value="photo">Фото</option>
          <option value="video">Видео</option>
          <option value="carousel">Карусель</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Текст под постом *
        </label>
        <textarea
          required
          value={formData.caption}
          onChange={(e) => setFormData({ ...formData, caption: e.target.value })}
          className="input"
          rows="4"
          placeholder="Введите текст для поста..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Язык текста *
        </label>
        <select
          value={formData.original_language}
          onChange={(e) => setFormData({ ...formData, original_language: e.target.value })}
          className="input"
        >
          <option value="ru">Русский</option>
          <option value="en">English</option>
          <option value="es">Español</option>
          <option value="fr">Français</option>
          <option value="de">Deutsch</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Группы для публикации *
        </label>
        <div className="space-y-2 max-h-40 overflow-y-auto border border-gray-200 rounded-lg p-3">
          {groups.length === 0 ? (
            <p className="text-sm text-gray-500">Нет доступных групп</p>
          ) : (
            groups.map((group) => (
              <label key={group.id} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.target_groups.includes(group.id)}
                  onChange={() => toggleGroup(group.id)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{group.name}</span>
                <span className="text-xs text-gray-500">({group.accounts_count} аккаунтов)</span>
              </label>
            ))
          )}
        </div>
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
          disabled={isLoading || files.length === 0}
        >
          {isLoading ? 'Создание...' : 'Создать пост'}
        </button>
      </div>
    </form>
  )
}

