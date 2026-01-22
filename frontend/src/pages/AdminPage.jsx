import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { 
  Users, Plus, Trash2, Edit2, Key, X, Check, 
  AlertCircle, Loader2, Shield, User, ArrowLeft 
} from 'lucide-react'

const API_BASE = '/api'

function AdminPage({ onBack }) {
  const { getAuthHeader, user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [tempPassword, setTempPassword] = useState(null)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/users`, {
        headers: getAuthHeader()
      })
      
      if (!response.ok) throw new Error('Failed to fetch users')
      
      const data = await response.json()
      setUsers(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const createUser = async (userData) => {
    try {
      const response = await fetch(`${API_BASE}/auth/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(userData)
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to create user')
      }

      await fetchUsers()
      setShowCreateModal(false)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  const updateUser = async (userId, userData) => {
    try {
      const response = await fetch(`${API_BASE}/auth/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(userData)
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to update user')
      }

      await fetchUsers()
      setEditingUser(null)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  const deleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return

    try {
      const response = await fetch(`${API_BASE}/auth/users/${userId}`, {
        method: 'DELETE',
        headers: getAuthHeader()
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to delete user')
      }

      await fetchUsers()
    } catch (err) {
      alert(err.message)
    }
  }

  const resetPassword = async (userId) => {
    try {
      const response = await fetch(`${API_BASE}/auth/users/${userId}/reset-password`, {
        method: 'POST',
        headers: getAuthHeader()
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to reset password')
      }

      const data = await response.json()
      setTempPassword({ userId, password: data.temporary_password })
    } catch (err) {
      alert(err.message)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-azure-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-4xl px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Users className="w-6 h-6 text-azure-500" />
              User Management
            </h1>
            <p className="text-slate-400 text-sm">Manage system users and permissions</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-azure-600 text-white hover:bg-azure-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add User
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 mb-6">
          <AlertCircle className="w-5 h-5" />
          <p>{error}</p>
        </div>
      )}

      {/* Temp Password Alert */}
      {tempPassword && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 mb-6">
          <div>
            <p className="font-semibold">Temporary Password Generated</p>
            <p className="text-sm mt-1 font-mono">{tempPassword.password}</p>
          </div>
          <button onClick={() => setTempPassword(null)} className="p-1">
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Users Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left p-4 text-slate-400 font-medium">User</th>
              <th className="text-left p-4 text-slate-400 font-medium">Role</th>
              <th className="text-left p-4 text-slate-400 font-medium">Status</th>
              <th className="text-right p-4 text-slate-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="border-b border-white/5 hover:bg-white/5">
                <td className="p-4">
                  <div>
                    <p className="text-white font-medium">{user.username}</p>
                    <p className="text-slate-400 text-sm">{user.email}</p>
                  </div>
                </td>
                <td className="p-4">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                    user.role === 'admin' 
                      ? 'bg-amber-500/20 text-amber-400' 
                      : 'bg-azure-500/20 text-azure-400'
                  }`}>
                    {user.role === 'admin' ? <Shield className="w-3 h-3" /> : <User className="w-3 h-3" />}
                    {user.role}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                    user.is_active 
                      ? 'bg-green-500/20 text-green-400' 
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="p-4">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => setEditingUser(user)}
                      className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                      title="Edit user"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => resetPassword(user.id)}
                      className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-amber-400 transition-colors"
                      title="Reset password"
                    >
                      <Key className="w-4 h-4" />
                    </button>
                    {user.id !== currentUser.id && (
                      <button
                        onClick={() => deleteUser(user.id)}
                        className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-red-400 transition-colors"
                        title="Delete user"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <UserModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={createUser}
          title="Create New User"
        />
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <UserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSubmit={(data) => updateUser(editingUser.id, data)}
          title="Edit User"
        />
      )}
    </div>
  )
}

function UserModal({ user, onClose, onSubmit, title }) {
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
    password: '',
    role: user?.role || 'user',
    is_active: user?.is_active ?? true
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // For edit, only send changed fields
    const submitData = user 
      ? Object.fromEntries(
          Object.entries(formData).filter(([key, value]) => {
            if (key === 'password') return value !== ''
            return value !== user[key]
          })
        )
      : formData

    const result = await onSubmit(submitData)
    
    if (!result.success) {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass rounded-2xl p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">{title}</h2>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 mb-4 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Username</label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required={!user}
              className="w-full px-4 py-2 rounded-lg bg-midnight-900/50 border border-white/10 text-white focus:outline-none focus:border-azure-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required={!user}
              className="w-full px-4 py-2 rounded-lg bg-midnight-900/50 border border-white/10 text-white focus:outline-none focus:border-azure-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-4 py-2 rounded-lg bg-midnight-900/50 border border-white/10 text-white focus:outline-none focus:border-azure-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Password {user && <span className="text-slate-500">(leave blank to keep current)</span>}
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required={!user}
              minLength={8}
              className="w-full px-4 py-2 rounded-lg bg-midnight-900/50 border border-white/10 text-white focus:outline-none focus:border-azure-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-4 py-2 rounded-lg bg-midnight-900/50 border border-white/10 text-white focus:outline-none focus:border-azure-500"
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded border-white/10 bg-midnight-900/50 text-azure-500 focus:ring-azure-500"
            />
            <label htmlFor="is_active" className="text-sm text-slate-300">Active</label>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg border border-white/10 text-slate-300 hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg bg-azure-600 text-white hover:bg-azure-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              {user ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AdminPage

