import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatLayout } from './components/chat-layout'
import { MessageBubble } from './components/message-bubble'
import { MessageList } from './components/message-list'
import { ChatInput } from './components/chat-input'
import type { ChatMessageResponse } from '@/lib/api/types'

const mockMessages: ChatMessageResponse[] = [
  {
    id: 'm1',
    session_id: 's1',
    role: 'user',
    content: 'How does authentication work in this repo?',
    created_at: '2026-08-20T10:00:00Z',
  },
  {
    id: 'm2',
    session_id: 's1',
    role: 'assistant',
    content: 'Authentication is handled via JWT tokens.\n\n```python\ndef verify_token(token: str):\n    return jwt.decode(token)\n```\n\n- Verifies secret key\n- Checks token expiration',
    created_at: '2026-08-20T10:00:05Z',
  },
]

describe('Chat Feature Components', () => {
  describe('MessageBubble', () => {
    it('renders user message with user role styling and content', () => {
      render(<MessageBubble message={mockMessages[0]} />)

      expect(screen.getByText('How does authentication work in this repo?')).toBeInTheDocument()
      expect(screen.getByTestId('message-bubble')).toHaveClass('ml-auto')
    })

    it('renders assistant message with markdown, lists, and syntax-highlighted code block', async () => {
      render(<MessageBubble message={mockMessages[1]} />)

      expect(screen.getByText(/Authentication is handled via JWT tokens/i)).toBeInTheDocument()
      expect(screen.getByText('Verifies secret key')).toBeInTheDocument()
      expect(screen.getByText('Checks token expiration')).toBeInTheDocument()
      await waitFor(() => {
        expect(screen.getByText(/def verify_token/i)).toBeInTheDocument()
      })
    })
  })

  describe('MessageList', () => {
    it('renders empty state when message list is empty', () => {
      render(<MessageList messages={[]} />)

      expect(screen.getByText('CodeGraph AI Assistant')).toBeInTheDocument()
      expect(
        screen.getByText(/Ask questions grounded in the repository's source code/i)
      ).toBeInTheDocument()
    })

    it('renders all messages in the conversation', () => {
      render(<MessageList messages={mockMessages} />)

      expect(screen.getAllByTestId('message-bubble')).toHaveLength(2)
      expect(screen.getByText('How does authentication work in this repo?')).toBeInTheDocument()
    })
  })

  describe('ChatInput', () => {
    it('submits on Enter and clears the textarea', async () => {
      const user = userEvent.setup()
      const onSend = vi.fn()

      render(<ChatInput onSend={onSend} />)

      const textarea = screen.getByRole('textbox', { name: /chat message input/i })
      await user.type(textarea, 'Explain the architecture{Enter}')

      expect(onSend).toHaveBeenCalledWith('Explain the architecture')
      expect(textarea).toHaveValue('')
    })

    it('inserts a newline on Shift+Enter without sending', async () => {
      const user = userEvent.setup()
      const onSend = vi.fn()

      render(<ChatInput onSend={onSend} />)

      const textarea = screen.getByRole('textbox', { name: /chat message input/i })
      await user.type(textarea, 'Line 1{Shift>}{Enter}{/Shift}Line 2')

      expect(onSend).not.toHaveBeenCalled()
      expect(textarea).toHaveValue('Line 1\nLine 2')
    })

    it('disables input and submit button when disabled prop is true', () => {
      render(<ChatInput onSend={vi.fn()} disabled />)

      const textarea = screen.getByRole('textbox', { name: /chat message input/i })
      const sendButton = screen.getByRole('button', { name: /send message/i })

      expect(textarea).toBeDisabled()
      expect(sendButton).toBeDisabled()
    })
  })

  describe('ChatLayout', () => {
    it('renders header, session controls, and new chat button', async () => {
      const user = userEvent.setup()
      const onNewSession = vi.fn()

      render(
        <ChatLayout
          repoId="test-repo"
          sessions={[{ id: 's1', repository_id: 'test-repo', title: 'Main Chat', created_at: '', updated_at: '' }]}
          activeSessionId="s1"
          messages={mockMessages}
          isLoadingHistory={false}
          isHistoryError={false}
          onSelectSession={vi.fn()}
          onNewSession={onNewSession}
          onSendMessage={vi.fn()}
        />
      )

      expect(screen.getByText('CodeGraph Chat')).toBeInTheDocument()
      expect(screen.getByText('New Chat')).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /new chat/i }))
      expect(onNewSession).toHaveBeenCalled()
    })
  })
})
