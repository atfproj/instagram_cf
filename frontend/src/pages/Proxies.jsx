import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { proxiesApi } from '../api/proxies'
import { Plus, Edit, Trash2, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react'
import Modal from '../components/Modal'
import ProxyForm from '../components/ProxyForm'

export default function Proxies() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProxy, setEditingProxy] = useState(null)
  const queryClient = useQueryClient()

  const { data: proxies, isLoading } = useQuery('proxies', () => 
    proxiesApi.getAll().then(r => r.data)
  )

  const deleteMutation = useMutation(
    (id) => proxiesApi.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('proxies')
      },
    }
  )

  const checkMutation = useMutation(
    (id) => proxiesApi.check(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('proxies')
        alert('Проверка прокси завершена')
      },
      onError: (error) => {
        alert(`Ошибка проверки: ${error.message}`)
      },
    }
  )

  const handleEdit = (proxy) => {
    setEditingProxy(proxy)
    setIsModalOpen(true)
  }

  const handleAdd = () => {
    setEditingProxy(null)
    setIsModalOpen(true)
  }

  const handleDelete = async (id) => {
    if (confirm('Вы уверены, что хотите удалить этот прокси?')) {
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
          <h1 className="text-3xl font-bold text-gray-900">Прокси</h1>
          <p className="mt-2 text-gray-600">Управление прокси серверами</p>
        </div>
        <button onClick={handleAdd} className="btn btn-primary flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Добавить прокси
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  URL
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Тип
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Страна
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Статус
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Аккаунтов
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {proxies?.map((proxy) => (
                <tr key={proxy.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-mono text-gray-900">{proxy.url}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500 uppercase">{proxy.type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{proxy.country || '—'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <ProxyStatusBadge status={proxy.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {(proxy.success_rate * 100).toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {proxy.assigned_accounts?.length || 0}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => checkMutation.mutate(proxy.id)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Проверить"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(proxy)}
                        className="text-gray-600 hover:text-gray-900"
                        title="Редактировать"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(proxy.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Удалить"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingProxy ? 'Редактировать прокси' : 'Добавить прокси'}>
        <ProxyForm
          proxy={editingProxy}
          onSuccess={() => {
            setIsModalOpen(false)
            queryClient.invalidateQueries('proxies')
          }}
        />
      </Modal>
    </div>
  )
}

function ProxyStatusBadge({ status }) {
  const statusConfig = {
    active: { label: 'Активен', className: 'badge-success', icon: CheckCircle },
    failed: { label: 'Не работает', className: 'badge-danger', icon: XCircle },
    checking: { label: 'Проверка', className: 'badge-warning', icon: Clock },
  }

  const config = statusConfig[status] || { label: status, className: 'badge-info', icon: Clock }
  const Icon = config.icon

  return (
    <span className={`badge ${config.className} flex items-center gap-1 w-fit`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  )
}

