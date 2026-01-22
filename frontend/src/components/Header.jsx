import { useAuth } from '../context/AuthContext'
import { Cloud, RotateCcw, Users, LogOut, User } from 'lucide-react'

function Header({ onReset, onAdminClick }) {
  const { user, logout, isAdmin } = useAuth()

  return (
    <header className="glass border-b border-white/5 sticky top-0 z-50">
      <div className="container mx-auto max-w-4xl px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-azure-500 to-azure-600 flex items-center justify-center shadow-lg shadow-azure-500/25">
              <Cloud className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Azure Assistant</h1>
              <p className="text-xs text-slate-400">Cloud Resource Provisioning</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* New Chat */}
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              title="Start new conversation"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="text-sm hidden sm:inline">New Chat</span>
            </button>

            {/* Admin Button (only for admins) */}
            {isAdmin() && onAdminClick && (
              <button
                onClick={onAdminClick}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                title="User Management"
              >
                <Users className="w-4 h-4" />
                <span className="text-sm hidden sm:inline">Users</span>
              </button>
            )}
            
            {/* Azure Portal Link */}
            <a
              href="https://portal.azure.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              title="Open Azure Portal"
            >
              <svg className="w-4 h-4" viewBox="0 0 96 96" fill="currentColor">
                <path d="M33.33 6.67L61.17 53.5 30.67 89.33h11.5l24.5-35.83L88 89.33H96L55.33 6.67H33.33zM0 89.33h27.33L54 43.5 34.5 6.67H8L40.17 61.5 0 89.33z"/>
              </svg>
              <span className="text-sm hidden sm:inline">Portal</span>
            </a>

            {/* User Menu */}
            <div className="flex items-center gap-2 ml-2 pl-2 border-l border-white/10">
              <div className="flex items-center gap-2 px-2 py-1">
                <div className="w-8 h-8 rounded-lg bg-azure-600/30 flex items-center justify-center">
                  <User className="w-4 h-4 text-azure-400" />
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm text-white font-medium">{user?.username}</p>
                  <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
                </div>
              </div>
              
              <button
                onClick={logout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
