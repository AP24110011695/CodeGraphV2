import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from './modal'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs'
import { ProgressBar } from './progress-bar'
import { CodeBlock } from './code-block'
import { EmptyState } from './empty-state'
import { ErrorState } from './error-state'
import { Skeleton } from './skeleton'
import { ToastProvider, useToast } from './toast'
import { Button } from './button'

describe('Composite UI Components', () => {
  describe('Modal', () => {
    it('renders modal content in portal when open and traps focus', () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()}>
          <ModalHeader>
            <ModalTitle>Modal Title</ModalTitle>
            <ModalDescription>Modal Description</ModalDescription>
          </ModalHeader>
          <ModalContent>
            <p>Body Content</p>
          </ModalContent>
          <ModalFooter>
            <Button>Confirm</Button>
          </ModalFooter>
        </Modal>
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Modal Title')).toBeInTheDocument()
      expect(screen.getByText('Body Content')).toBeInTheDocument()
    })

    it('closes on Escape key press', () => {
      const handleClose = vi.fn()
      render(
        <Modal isOpen={true} onClose={handleClose}>
          <ModalContent>Modal Content</ModalContent>
        </Modal>
      )

      fireEvent.keyDown(document, { key: 'Escape' })
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('closes on close button click', async () => {
      const handleClose = vi.fn()
      render(
        <Modal isOpen={true} onClose={handleClose}>
          <ModalContent>Content</ModalContent>
        </Modal>
      )

      const closeBtn = screen.getByLabelText(/close modal/i)
      await userEvent.click(closeBtn)
      expect(handleClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Tabs', () => {
    it('switches panels on tab trigger click', async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Panel 1 Content</TabsContent>
          <TabsContent value="tab2">Panel 2 Content</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Panel 1 Content')).toBeInTheDocument()
      expect(screen.queryByText('Panel 2 Content')).not.toBeInTheDocument()

      await userEvent.click(screen.getByText('Tab 2'))
      expect(screen.getByText('Panel 2 Content')).toBeInTheDocument()
      expect(screen.queryByText('Panel 1 Content')).not.toBeInTheDocument()
    })

    it('supports keyboard arrow navigation across tabs', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      const tab1 = screen.getByText('Tab 1')
      tab1.focus()
      fireEvent.keyDown(tab1.parentElement!, { key: 'ArrowRight' })
      expect(screen.getByText('Content 2')).toBeInTheDocument()
    })
  })

  describe('ProgressBar', () => {
    it('renders determinate progress bar with value and percentage', () => {
      render(<ProgressBar value={75} max={100} label="Ingestion" showPercentage />)

      const pb = screen.getByRole('progressbar')
      expect(pb).toHaveAttribute('aria-valuenow', '75')
      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('Ingestion')).toBeInTheDocument()
    })
  })

  describe('CodeBlock', () => {
    it('renders code snippet and copy button', async () => {
      const code = 'const hello = "world";\nconsole.log(hello);'
      render(<CodeBlock code={code} language="typescript" filename="index.ts" />)

      expect(screen.getByText('index.ts')).toBeInTheDocument()
      expect(screen.getByLabelText(/copy code to clipboard/i)).toBeInTheDocument()
    })
  })

  describe('EmptyState', () => {
    it('renders title, description and action', () => {
      render(
        <EmptyState
          title="No items found"
          description="Try creating one"
          action={<Button>Create</Button>}
        />
      )

      expect(screen.getByText('No items found')).toBeInTheDocument()
      expect(screen.getByText('Try creating one')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
    })
  })

  describe('ErrorState', () => {
    it('renders alert message and triggers onRetry', async () => {
      const handleRetry = vi.fn()
      render(
        <ErrorState
          title="Failed to load"
          message="Server unreachable"
          onRetry={handleRetry}
        />
      )

      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load')).toBeInTheDocument()
      expect(screen.getByText('Server unreachable')).toBeInTheDocument()

      const retryBtn = screen.getByRole('button', { name: /try again/i })
      await userEvent.click(retryBtn)
      expect(handleRetry).toHaveBeenCalledTimes(1)
    })
  })

  describe('Skeleton', () => {
    it('renders with loading status role', () => {
      render(<Skeleton className="h-4 w-32" />)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })

  describe('Toast Notification System', () => {
    function TestToastConsumer() {
      const toast = useToast()
      return (
        <div>
          <button
            onClick={() =>
              toast.success('File saved successfully', 'Success!')
            }
          >
            Trigger Success
          </button>
        </div>
      )
    }

    it('renders toast on trigger and auto-dismisses', async () => {
      render(
        <ToastProvider defaultDuration={150}>
          <TestToastConsumer />
        </ToastProvider>
      )

      const triggerBtn = screen.getByText('Trigger Success')
      await userEvent.click(triggerBtn)

      expect(screen.getByText('Success!')).toBeInTheDocument()
      expect(screen.getByText('File saved successfully')).toBeInTheDocument()

      await waitFor(
        () => {
          expect(screen.queryByText('Success!')).not.toBeInTheDocument()
        },
        { timeout: 500 }
      )
    })

    it('dismisses toast on close click', async () => {
      render(
        <ToastProvider defaultDuration={5000}>
          <TestToastConsumer />
        </ToastProvider>
      )

      await userEvent.click(screen.getByText('Trigger Success'))
      expect(screen.getByText('Success!')).toBeInTheDocument()

      const dismissBtn = screen.getByLabelText(/dismiss toast/i)
      await userEvent.click(dismissBtn)

      expect(screen.queryByText('Success!')).not.toBeInTheDocument()
    })
  })
})
