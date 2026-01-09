import { Cloud, User, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

function ChatMessage({ role, content, isLatest }) {
  const [copied, setCopied] = useState(false)
  const isAssistant = role === 'assistant'

  // Check if content contains code blocks
  const hasCode = content.includes('```')

  const copyToClipboard = async () => {
    // Extract code from markdown code blocks
    const codeMatch = content.match(/```[\s\S]*?\n([\s\S]*?)```/)
    const textToCopy = codeMatch ? codeMatch[1].trim() : content
    
    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className={`flex items-start gap-3 ${isLatest ? 'animate-slide-up' : ''} ${isAssistant ? '' : 'flex-row-reverse'}`}>
      {/* Avatar */}
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg ${
        isAssistant 
          ? 'bg-gradient-to-br from-azure-500 to-azure-600 shadow-azure-500/25' 
          : 'bg-gradient-to-br from-slate-600 to-slate-700 shadow-slate-500/25'
      }`}>
        {isAssistant ? (
          <Cloud className="w-5 h-5 text-white" />
        ) : (
          <User className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Bubble */}
      <div className={`relative group max-w-[80%] ${isAssistant ? '' : 'text-right'}`}>
        <div className={`rounded-2xl px-5 py-3 ${
          isAssistant 
            ? 'glass rounded-tl-sm text-slate-200' 
            : 'bg-azure-600 rounded-tr-sm text-white'
        }`}>
          <div className="chat-content text-sm leading-relaxed">
            <ReactMarkdown
              components={{
                // Custom code block rendering
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const language = match ? match[1] : ''
                  
                  if (!inline && (language || String(children).includes('\n'))) {
                    return (
                      <div className="relative group/code my-3">
                        {language && (
                          <div className="absolute top-0 left-0 px-3 py-1 text-xs text-slate-400 bg-slate-800/50 rounded-tl-lg rounded-br-lg">
                            {language}
                          </div>
                        )}
                        <pre className={`bg-midnight-900 rounded-lg p-4 ${language ? 'pt-8' : ''} overflow-x-auto`}>
                          <code className="text-sm font-mono text-slate-300" {...props}>
                            {children}
                          </code>
                        </pre>
                      </div>
                    )
                  }
                  
                  return (
                    <code className="bg-azure-500/20 px-1.5 py-0.5 rounded text-azure-300 font-mono text-sm" {...props}>
                      {children}
                    </code>
                  )
                },
                // Custom paragraph
                p({ children }) {
                  return <p className="mb-2 last:mb-0">{children}</p>
                },
                // Custom lists
                ul({ children }) {
                  return <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
                },
                ol({ children }) {
                  return <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
                },
                // Custom headings
                h1({ children }) {
                  return <h1 className="text-lg font-semibold text-azure-400 mb-2">{children}</h1>
                },
                h2({ children }) {
                  return <h2 className="text-base font-semibold text-azure-400 mb-2">{children}</h2>
                },
                h3({ children }) {
                  return <h3 className="text-sm font-semibold text-azure-400 mb-1">{children}</h3>
                },
                // Custom strong
                strong({ children }) {
                  return <strong className="font-semibold text-azure-300">{children}</strong>
                },
                // Custom links
                a({ href, children }) {
                  return (
                    <a 
                      href={href} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-azure-400 hover:text-azure-300 underline underline-offset-2"
                    >
                      {children}
                    </a>
                  )
                }
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Copy button for messages with code */}
        {isAssistant && hasCode && (
          <button
            onClick={copyToClipboard}
            className="absolute -right-2 -top-2 opacity-0 group-hover:opacity-100 transition-opacity p-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white shadow-lg"
            title="Copy code"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
    </div>
  )
}

export default ChatMessage

