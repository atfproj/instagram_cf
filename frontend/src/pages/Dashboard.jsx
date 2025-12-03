import { useQuery } from 'react-query'
import { accountsApi } from '../api/accounts'
import { groupsApi } from '../api/groups'
import { postsApi } from '../api/posts'
import { proxiesApi } from '../api/proxies'
import { Users, FolderTree, FileImage, Network, CheckCircle, XCircle, Clock } from 'lucide-react'

export default function Dashboard() {
  const { data: accounts } = useQuery('accounts', () => accountsApi.getAll().then(r => r.data))
  const { data: groups } = useQuery('groups', () => groupsApi.getAll().then(r => r.data))
  const { data: posts } = useQuery('posts', () => postsApi.getAll().then(r => r.data))
  const { data: proxies } = useQuery('proxies', () => proxiesApi.getAll().then(r => r.data))

  const activeAccounts = accounts?.filter(acc => acc.status === 'active')?.length || 0
  const totalAccounts = accounts?.length || 0
  
  const stats = [
    {
      name: 'Аккаунты',
      value: totalAccounts,
      active: activeAccounts,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: 'Группы',
      value: groups?.length || 0,
      icon: FolderTree,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      name: 'Посты',
      value: posts?.length || 0,
      icon: FileImage,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      name: 'Прокси',
      value: proxies?.filter(p => p.status === 'active')?.length || 0,
      total: proxies?.length || 0,
      icon: Network,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Дашборд</h1>
        <p className="mt-2 text-gray-600">Обзор системы Instagram Content Factory</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                  {stat.active !== undefined && (
                    <span className="ml-2 text-sm text-gray-500">/ {stat.active} активных</span>
                  )}
                  {stat.total !== undefined && (
                    <span className="ml-2 text-sm text-gray-500">/ {stat.total} всего</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Последние аккаунты</h2>
          <div className="space-y-3">
            {accounts?.slice(0, 5).map((account) => (
              <div key={account.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <p className="font-medium text-gray-900">{account.username}</p>
                  <p className="text-sm text-gray-500">{account.language}</p>
                </div>
                <StatusBadge status={account.status} />
              </div>
            )) || <p className="text-gray-500 text-sm">Нет аккаунтов</p>}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Последние посты</h2>
          <div className="space-y-3">
            {posts?.slice(0, 5).map((post) => (
              <div key={post.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{post.caption_original?.substring(0, 50)}...</p>
                  <p className="text-sm text-gray-500">{new Date(post.created_at).toLocaleDateString('ru-RU')}</p>
                </div>
                <PostStatusBadge status={post.status} />
              </div>
            )) || <p className="text-gray-500 text-sm">Нет постов</p>}
          </div>
        </div>
      </div>
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
    <span className={`badge ${config.className} flex items-center gap-1`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  )
}

function PostStatusBadge({ status }) {
  const statusConfig = {
    draft: { label: 'Черновик', className: 'badge-info' },
    pending: { label: 'В очереди', className: 'badge-warning' },
    posting: { label: 'Публикуется', className: 'badge-warning' },
    completed: { label: 'Завершён', className: 'badge-success' },
    failed: { label: 'Ошибка', className: 'badge-danger' },
  }

  const config = statusConfig[status] || { label: status, className: 'badge-info' }

  return <span className={`badge ${config.className}`}>{config.label}</span>
}

