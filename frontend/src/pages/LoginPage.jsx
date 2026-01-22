import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Cloud, Lock, User, AlertCircle, Loader2 } from 'lucide-react'

function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(username, password)
    
    if (!result.success) {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background decorations */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-azure-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-azure-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 right-1/4 w-72 h-72 bg-azure-400/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-azure-500 to-azure-600 mb-6 shadow-lg shadow-azure-500/25">
            <Cloud className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Azure Assistant</h1>
          <p className="text-slate-400">Sign in to manage Azure resources</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="glass rounded-2xl p-8 space-y-6">
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">
              Username
            </label>
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                className="w-full pl-12 pr-4 py-3 rounded-xl bg-midnight-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-azure-500 focus:ring-1 focus:ring-azure-500 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="w-full pl-12 pr-4 py-3 rounded-xl bg-midnight-900/50 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-azure-500 focus:ring-1 focus:ring-azure-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-azure-500 to-azure-600 text-white font-semibold hover:from-azure-600 hover:to-azure-700 focus:outline-none focus:ring-2 focus:ring-azure-500 focus:ring-offset-2 focus:ring-offset-midnight-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-6">
          Default admin: admin / Admin@123456
        </p>
      </div>
    </div>
  )
}

export default LoginPage

