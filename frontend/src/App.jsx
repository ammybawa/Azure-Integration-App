import { useState, useEffect, useRef } from 'react'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import ResourceSummary from './components/ResourceSummary'
import Header from './components/Header'
import { Cloud, Sparkles, Server, Database, Network, Box, HardDrive } from 'lucide-react'

const API_BASE = '/api'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [options, setOptions] = useState([])
  const [resourceSummary, setResourceSummary] = useState(null)
  const [costEstimate, setCostEstimate] = useState(null)
  const [terraformCode, setTerraformCode] = useState(null)
  const [createdResource, setCreatedResource] = useState(null)
  const [currentState, setCurrentState] = useState('initial')
  const messagesEndRef = useRef(null)

  // Initialize session on mount
  useEffect(() => {
    initSession()
  }, [])

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/session`, {
        method: 'POST',
      })
      const data = await response.json()
      setSessionId(data.session_id)
      
      // Send initial message to get welcome (only once)
      const chatResponse = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: data.session_id,
          message: '',
        }),
      })
      const chatData = await chatResponse.json()
      
      setMessages([{ role: 'assistant', content: chatData.message }])
      setCurrentState(chatData.state)
      setOptions(chatData.options || [])
      
    } catch (error) {
      console.error('Failed to create session:', error)
      setMessages([{
        role: 'assistant',
        content: '⚠️ Failed to connect to the server. Please make sure the backend is running on http://localhost:8000',
      }])
    }
  }

  const sendMessage = async (message, sid = sessionId) => {
    if (!sid) {
      console.error('No session ID available')
      return
    }

    const trimmedMessage = message.trim()
    
    // Add user message to chat (if not empty)
    if (trimmedMessage) {
      setMessages(prev => [...prev, { role: 'user', content: trimmedMessage }])
    }

    setIsLoading(true)
    setOptions([])

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sid,
          message: trimmedMessage,
        }),
      })

      const data = await response.json()

      // Add assistant response
      setMessages(prev => [...prev, { role: 'assistant', content: data.message }])

      // Update state
      setCurrentState(data.state)
      setOptions(data.options || [])
      setResourceSummary(data.resource_summary || null)
      setCostEstimate(data.cost_estimate || null)
      setTerraformCode(data.terraform_code || null)
      setCreatedResource(data.created_resource || null)

      // If we're in creating state, send another request to execute
      if (data.state === 'creating') {
        setTimeout(() => sendMessage('execute', sid), 500)
      }

    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Failed to send message. Please check your connection and try again.',
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleOptionClick = (option) => {
    sendMessage(option)
  }

  const handleReset = () => {
    setMessages([])
    setOptions([])
    setResourceSummary(null)
    setCostEstimate(null)
    setTerraformCode(null)
    setCreatedResource(null)
    sendMessage('restart')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Background decorations */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-azure-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-azure-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 right-1/4 w-72 h-72 bg-azure-400/10 rounded-full blur-3xl" />
        
        {/* Floating icons */}
        <Cloud className="absolute top-20 left-[10%] w-8 h-8 text-azure-500/20 animate-bounce-subtle" style={{ animationDelay: '0s' }} />
        <Server className="absolute top-40 right-[15%] w-6 h-6 text-azure-400/20 animate-bounce-subtle" style={{ animationDelay: '0.5s' }} />
        <Database className="absolute bottom-32 left-[20%] w-7 h-7 text-azure-500/20 animate-bounce-subtle" style={{ animationDelay: '1s' }} />
        <Network className="absolute bottom-48 right-[25%] w-8 h-8 text-azure-400/20 animate-bounce-subtle" style={{ animationDelay: '1.5s' }} />
        <Box className="absolute top-1/3 left-[5%] w-5 h-5 text-azure-500/20 animate-bounce-subtle" style={{ animationDelay: '2s' }} />
      </div>

      {/* Header */}
      <Header onReset={handleReset} />

      {/* Main chat container */}
      <main className="flex-1 container mx-auto max-w-4xl px-4 py-6 flex flex-col">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4">
          {messages.length === 0 && !isLoading && (
            <div className="text-center py-12 animate-fade-in">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-azure-500 to-azure-600 mb-6 shadow-lg shadow-azure-500/25">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-white mb-3">
                Azure Provisioning Assistant
              </h2>
              <p className="text-slate-400 max-w-md mx-auto">
                I'll help you create Azure resources through a simple conversation.
                Just tell me what you need!
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              role={message.role}
              content={message.content}
              isLatest={index === messages.length - 1}
            />
          ))}

          {isLoading && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-azure-500 to-azure-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-azure-500/25">
                <Cloud className="w-5 h-5 text-white" />
              </div>
              <div className="glass rounded-2xl rounded-tl-sm px-5 py-4">
                <div className="flex gap-1.5">
                  <span className="typing-dot w-2 h-2 bg-azure-400 rounded-full"></span>
                  <span className="typing-dot w-2 h-2 bg-azure-400 rounded-full"></span>
                  <span className="typing-dot w-2 h-2 bg-azure-400 rounded-full"></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Resource Summary Card */}
        {(resourceSummary || costEstimate || createdResource) && (
          <ResourceSummary
            summary={resourceSummary}
            costEstimate={costEstimate}
            createdResource={createdResource}
          />
        )}

        {/* Quick Options */}
        {options.length > 0 && !isLoading && (
          <div className="flex flex-wrap gap-2 mb-4 animate-slide-up">
            {options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleOptionClick(option)}
                className="px-4 py-2 rounded-xl glass text-sm text-slate-300 hover:text-white hover:bg-azure-600/30 transition-all duration-200 border border-transparent hover:border-azure-500/50"
              >
                {option}
              </button>
            ))}
          </div>
        )}

        {/* Chat Input */}
        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder={getPlaceholder(currentState)}
        />
      </main>
    </div>
  )
}

function getPlaceholder(state) {
  switch (state) {
    case 'resource_selection':
      return 'Select a resource type (VM, VNet, Storage, AKS, PostgreSQL, MySQL, SQL, Cosmos)...'
    case 'subscription':
      return 'Enter your Azure Subscription ID or type "default"...'
    case 'resource_group':
      return 'Enter resource group name (or new:name for new)...'
    case 'region':
      return 'Select or enter an Azure region...'
    case 'resource_config':
      return 'Enter your configuration value...'
    case 'confirmation':
      return 'Type yes, terraform, no, or edit...'
    case 'completed':
      return 'Type restart to create another resource...'
    default:
      return 'Type a message...'
  }
}

export default App

