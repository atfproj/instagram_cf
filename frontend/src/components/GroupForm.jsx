import { useState } from 'react'
import { useMutation } from 'react-query'
import { groupsApi } from '../api/groups'

export default function GroupForm({ group, onSuccess }) {
  const [formData, setFormData] = useState({
    name: group?.name || '',
    description: group?.description || '',
  })

  const createMutation = useMutation(
    (data) => groupsApi.create(data),
    { onSuccess }
  )

  const updateMutation = useMutation(
    ({ id, data }) => groupsApi.update(id, data),
    { onSuccess }
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (group) {
      await updateMutation.mutateAsync({ id: group.id, data: formData })
    } else {
      await createMutation.mutateAsync(formData)
    }
  }

  const isLoading = createMutation.isLoading || updateMutation.isLoading

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Название *
        </label>
        <input
          type="text"
          required
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="input"
          placeholder="IT, Финансы, Новости..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Описание
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          className="input"
          rows="3"
          placeholder="Описание группы..."
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
          {isLoading ? 'Сохранение...' : group ? 'Сохранить' : 'Создать'}
        </button>
      </div>
    </form>
  )
}

