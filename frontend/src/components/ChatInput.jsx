import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'

function ChatInput({ onSend, disabled, placeholder }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`
    }
  }, [message])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="glass rounded-2xl p-2 flex items-end gap-2 shadow-xl shadow-black/20">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent border-none outline-none resize-none text-white placeholder-slate-500 px-3 py-2 text-sm leading-relaxed max-h-36"
          style={{ minHeight: '44px' }}
        />
        
        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200 flex-shrink-0 ${
            disabled || !message.trim()
              ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
              : 'bg-gradient-to-br from-azure-500 to-azure-600 text-white hover:shadow-lg hover:shadow-azure-500/25 glow-button'
          }`}
        >
          {disabled ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
      
      <p className="text-xs text-slate-500 mt-2 text-center">
        Press Enter to send • Shift+Enter for new line
      </p>
    </form>
  )
}

export default ChatInput

