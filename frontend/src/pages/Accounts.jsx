import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { accountsApi } from '../api/accounts'
import { groupsApi } from '../api/groups'
import { Plus, Edit, Trash2, LogIn, RefreshCw, CheckCircle, XCircle, Clock, User, Upload } from 'lucide-react'
import Modal from '../components/Modal'
import AccountForm from '../components/AccountForm'
import ProfileModal from '../components/ProfileModal'
import ImportSessionModal from '../components/ImportSessionModal'
import LoginModal from '../components/LoginModal'

export default function Accounts() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [profileAccount, setProfileAccount] = useState(null)
  const [loginAccount, setLoginAccount] = useState(null)
  const queryClient = useQueryClient()

  const { data: accounts, isLoading } = useQuery('accounts', () => 
    accountsApi.getAll().then(r => r.data)
  )
  const { data: groups } = useQuery('groups', () => 
    groupsApi.getAll().then(r => Array.isArray(r.data) ? r.data : [])
  )

  const deleteMutation = useMutation(
    (id) => accountsApi.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('accounts')
      },
    }
  )

  const handleLogin = (account) => {
    setLoginAccount(account)
    setIsLoginModalOpen(true)
  }

  const statusMutation = useMutation(
    (id) => accountsApi.getStatus(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('accounts')
      },
    }
  )

  const handleEdit = (account) => {
    setEditingAccount(account)
    setIsModalOpen(true)
  }

  const handleAdd = () => {
    setEditingAccount(null)
    setIsModalOpen(true)
  }

  const handleDelete = async (id) => {
    if (confirm('Вы уверены, что хотите удалить этот аккаунт?')) {
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
          <h1 className="text-3xl font-bold text-gray-900">Аккаунты</h1>
          <p className="mt-2 text-gray-600">Управление Instagram аккаунтами</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setIsImportModalOpen(true)} 
            className="btn bg-green-600 hover:bg-green-700 text-white flex items-center gap-2"
          >
            <Upload className="h-5 w-5" />
            Загрузка сессии
          </button>
          <button onClick={handleAdd} className="btn btn-primary flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Добавить аккаунт
          </button>
        </div>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Username
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Группа
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Язык
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Статус
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Постов сегодня
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {accounts?.map((account) => {
                const group = Array.isArray(groups) ? groups.find(g => g.id === account.group_id) : null
                return (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{account.username}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{group?.name || '—'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{account.language}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={account.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {account.posts_count_today} / {account.posts_limit_per_day}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setProfileAccount(account)}
                          className="text-purple-600 hover:text-purple-900"
                          title="Управление профилем"
                        >
                          <User className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleLogin(account)}
                          className="text-primary-600 hover:text-primary-900"
                          title="Авторизация по логин/пароль"
                        >
                          <LogIn className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => statusMutation.mutate(account.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Проверить статус"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(account)}
                          className="text-gray-600 hover:text-gray-900"
                          title="Редактировать"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(account.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Удалить"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingAccount ? 'Редактировать аккаунт' : 'Добавить аккаунт'}>
        <AccountForm
          account={editingAccount}
          groups={groups || []}
          onSuccess={() => {
            setIsModalOpen(false)
            queryClient.invalidateQueries('accounts')
          }}
        />
      </Modal>

      {profileAccount && (
        <ProfileModal
          account={profileAccount}
          onClose={() => setProfileAccount(null)}
        />
      )}

      <ImportSessionModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={(response) => {
          alert(`Аккаунт '${response.account.username}' успешно импортирован!`)
          queryClient.invalidateQueries('accounts')
        }}
      />

      <LoginModal
        account={loginAccount}
        isOpen={isLoginModalOpen}
        onClose={() => {
          setIsLoginModalOpen(false)
          setLoginAccount(null)
        }}
      />
    </div>
  )
}

function StatusBadge({ status }) {
  const statusConfig = {
    active: { label: 'Активен', className: 'badge-success', icon: CheckCircle },
    banned: { label: 'Забанен', className: 'badge-danger', icon: XCircle },
    cooldown: { label: 'Охлаждение', className: 'badge-warning', icon: Clock },
    login_required: { label: 'Требуется вход', className: 'badge-warning', icon: Clock },
    proxy_error: { label: 'Ошибка прокси', className: 'badge-danger', icon: XCircle },
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

