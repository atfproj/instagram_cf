import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { postsApi } from '../api/posts'
import { groupsApi } from '../api/groups'
import { Plus, Send, Eye, FileImage } from 'lucide-react'
import Modal from '../components/Modal'
import PostForm from '../components/PostForm'

export default function Posts() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedPost, setSelectedPost] = useState(null)
  const queryClient = useQueryClient()

  const { data: posts, isLoading } = useQuery('posts', () => 
    postsApi.getAll().then(r => r.data)
  )
  const { data: groups } = useQuery('groups', () => 
    groupsApi.getAll().then(r => r.data)
  )

  const publishMutation = useMutation(
    (id) => postsApi.publish(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('posts')
        alert('Публикация запущена!')
      },
      onError: (error) => {
        alert(`Ошибка: ${error.message}`)
      },
    }
  )

  const handlePublish = async (id) => {
    if (confirm('Запустить публикацию этого поста на все аккаунты в выбранных группах?')) {
      await publishMutation.mutateAsync(id)
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Загрузка...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Посты</h1>
          <p className="mt-2 text-gray-600">Создание и управление постами</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)} 
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Создать пост
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {posts?.map((post) => (
          <div key={post.id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileImage className="h-5 w-5 text-gray-400" />
                <PostStatusBadge status={post.status} />
              </div>
              <span className="text-xs text-gray-500">
                {new Date(post.created_at).toLocaleDateString('ru-RU')}
              </span>
            </div>
            
            <p className="text-sm text-gray-700 mb-4 line-clamp-3">
              {post.caption_original}
            </p>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <div className="text-xs text-gray-500">
                {post.media_type} • {post.target_groups?.length || 0} групп
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedPost(post)}
                  className="text-blue-600 hover:text-blue-900"
                  title="Просмотр"
                >
                  <Eye className="h-4 w-4" />
                </button>
                {post.status === 'draft' && (
                  <button
                    onClick={() => handlePublish(post.id)}
                    className="text-green-600 hover:text-green-900"
                    title="Опубликовать"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Создать пост">
        <PostForm
          groups={groups || []}
          onSuccess={() => {
            setIsModalOpen(false)
            queryClient.invalidateQueries('posts')
          }}
        />
      </Modal>

      {selectedPost && (
        <PostDetailsModal 
          post={selectedPost} 
          groups={groups || []}
          onClose={() => setSelectedPost(null)} 
        />
      )}
    </div>
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

function PostDetailsModal({ post, groups, onClose }) {
  const { data: executions } = useQuery(
    ['post-executions', post.id],
    () => postsApi.getExecutions(post.id).then(r => r.data),
    { enabled: !!post, refetchInterval: 5000 } // Обновление каждые 5 секунд
  )

  return (
    <Modal isOpen={!!post} onClose={onClose} title="Детали поста">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Текст</label>
          <p className="text-sm text-gray-900">{post.caption_original}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Группы</label>
          <div className="flex flex-wrap gap-2">
            {post.target_groups?.map((groupId) => {
              const group = groups.find(g => g.id === groupId)
              return group ? (
                <span key={groupId} className="badge badge-info">{group.name}</span>
              ) : null
            })}
          </div>
        </div>

        {executions?.statistics && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Статистика публикации</label>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{executions.statistics.success}</div>
                <div className="text-xs text-gray-500">Успешно</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{executions.statistics.failed}</div>
                <div className="text-xs text-gray-500">Ошибок</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{executions.statistics.queued}</div>
                <div className="text-xs text-gray-500">В очереди</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{executions.statistics.total}</div>
                <div className="text-xs text-gray-500">Всего</div>
              </div>
            </div>
          </div>
        )}

        {executions?.executions && executions.executions.length > 0 && (
          <>
            {/* Опубликованные аккаунты */}
            {executions.executions.filter(e => e.status === 'success').length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Опубликовано ({executions.executions.filter(e => e.status === 'success').length})
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {executions.executions
                    .filter(e => e.status === 'success')
                    .map((exec) => (
                      <div key={exec.id} className="flex items-start gap-2 p-2 bg-green-50 rounded border border-green-200">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">
                            @{exec.account_username || 'Неизвестно'}
                          </div>
                          <div 
                            className="text-xs text-gray-600 truncate mt-1"
                            title={exec.caption_translated}
                          >
                            {exec.caption_translated.length > 60 
                              ? `${exec.caption_translated.substring(0, 60)}...` 
                              : exec.caption_translated}
                          </div>
                          {exec.posted_at && (
                            <div className="text-xs text-gray-400 mt-1">
                              {new Date(exec.posted_at).toLocaleString('ru-RU')}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Аккаунты в очереди */}
            {executions.executions.filter(e => e.status === 'queued').length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  В очереди ({executions.executions.filter(e => e.status === 'queued').length})
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {executions.executions
                    .filter(e => e.status === 'queued')
                    .map((exec) => (
                      <div key={exec.id} className="flex items-start gap-2 p-2 bg-yellow-50 rounded border border-yellow-200">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">
                            @{exec.account_username || 'Неизвестно'}
                          </div>
                          <div 
                            className="text-xs text-gray-600 truncate mt-1"
                            title={exec.caption_translated}
                          >
                            {exec.caption_translated.length > 60 
                              ? `${exec.caption_translated.substring(0, 60)}...` 
                              : exec.caption_translated}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Публикуется */}
            {executions.executions.filter(e => e.status === 'posting').length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Публикуется ({executions.executions.filter(e => e.status === 'posting').length})
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {executions.executions
                    .filter(e => e.status === 'posting')
                    .map((exec) => (
                      <div key={exec.id} className="flex items-start gap-2 p-2 bg-blue-50 rounded border border-blue-200">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">
                            @{exec.account_username || 'Неизвестно'}
                          </div>
                          <div 
                            className="text-xs text-gray-600 truncate mt-1"
                            title={exec.caption_translated}
                          >
                            {exec.caption_translated.length > 60 
                              ? `${exec.caption_translated.substring(0, 60)}...` 
                              : exec.caption_translated}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Ошибки */}
            {executions.executions.filter(e => e.status === 'failed').length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ошибки ({executions.executions.filter(e => e.status === 'failed').length})
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {executions.executions
                    .filter(e => e.status === 'failed')
                    .map((exec) => (
                      <div key={exec.id} className="flex items-start gap-2 p-2 bg-red-50 rounded border border-red-200">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">
                            @{exec.account_username || 'Неизвестно'}
                          </div>
                          {exec.error_message && (
                            <div className="text-xs text-red-600 mt-1">
                              {exec.error_message}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  )
}

