import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { groupsApi } from '../api/groups'
import { Plus, Edit, Trash2, Users } from 'lucide-react'
import Modal from '../components/Modal'
import GroupForm from '../components/GroupForm'

export default function Groups() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState(null)
  const queryClient = useQueryClient()

  const { data: groups, isLoading } = useQuery('groups', () => 
    groupsApi.getAll().then(r => r.data)
  )

  const deleteMutation = useMutation(
    (id) => groupsApi.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('groups')
      },
    }
  )

  const handleEdit = (group) => {
    setEditingGroup(group)
    setIsModalOpen(true)
  }

  const handleAdd = () => {
    setEditingGroup(null)
    setIsModalOpen(true)
  }

  const handleDelete = async (id) => {
    if (confirm('Вы уверены, что хотите удалить эту группу?')) {
      await deleteMutation.mutateAsync(id)
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Загрузка...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Группы</h1>
          <p className="mt-2 text-gray-600">Управление группами аккаунтов</p>
        </div>
        <button onClick={handleAdd} className="btn btn-primary flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Создать группу
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {groups?.map((group) => (
          <div key={group.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{group.name}</h3>
                {group.description && (
                  <p className="mt-1 text-sm text-gray-500">{group.description}</p>
                )}
                <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
                  <Users className="h-4 w-4" />
                  <span>{group.accounts_count} аккаунтов</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleEdit(group)}
                  className="text-gray-600 hover:text-gray-900"
                  title="Редактировать"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(group.id)}
                  className="text-red-600 hover:text-red-900"
                  title="Удалить"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingGroup ? 'Редактировать группу' : 'Создать группу'}>
        <GroupForm
          group={editingGroup}
          onSuccess={() => {
            setIsModalOpen(false)
            queryClient.invalidateQueries('groups')
          }}
        />
      </Modal>
    </div>
  )
}

