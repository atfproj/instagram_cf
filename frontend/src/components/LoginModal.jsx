import { useState } from 'react'
import { useMutation, useQueryClient } from 'react-query'
import { accountsApi } from '../api/accounts'
import Modal from './Modal'

export default function LoginModal({ account, isOpen, onClose }) {
  const [verificationCode, setVerificationCode] = useState('')
  const queryClient = useQueryClient()

  const loginMutation = useMutation(
    (data) => accountsApi.login(account.id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('accounts')
        onClose()
        alert('Авторизация успешна!')
      },
      onError: (error) => {
        const message = error.response?.data?.detail || error.message
        if (message.includes('двухфакторная')) {
          alert('Требуется 2FA код. Введите код и попробуйте снова.')
        } else {
          alert(`Ошибка авторизации: ${message}`)
        }
      },
    }
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const data = {}
    if (verificationCode.trim()) {
      data.verification_code = verificationCode.trim()
    }
    
    await loginMutation.mutateAsync(data)
  }

  const handleClose = () => {
    setVerificationCode('')
    onClose()
  }

  if (!account) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={`Авторизация: ${account.username}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Если у аккаунта включена двухфакторная аутентификация, введите 2FA код.
            Можно использовать SMS код, код из приложения или backup код.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            2FA код (опционально)
          </label>
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value)}
            className="input"
            placeholder="123456 или 6HTQ 5TWO PONS GAWH LE2A ISG6 D2PN EGS4"
          />
          <p className="text-xs text-gray-500 mt-1">
            Оставьте пустым если 2FA не включен
          </p>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            disabled={loginMutation.isLoading}
          >
            Отмена
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={loginMutation.isLoading}
          >
            {loginMutation.isLoading ? 'Авторизация...' : 'Войти'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
