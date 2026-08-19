import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './button'
import { Input } from './input'
import { Badge } from './badge'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from './card'
import { Spinner } from './spinner'
import { Tooltip } from './tooltip'

describe('Core UI Primitives', () => {
  describe('Button', () => {
    it('renders children and handles onClick', async () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click Me</Button>)

      const btn = screen.getByRole('button', { name: /click me/i })
      expect(btn).toBeInTheDocument()

      await userEvent.click(btn)
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('disables interactions when disabled or loading', async () => {
      const handleClick = vi.fn()
      const { rerender } = render(
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      )

      const btn = screen.getByRole('button')
      expect(btn).toBeDisabled()
      await userEvent.click(btn)
      expect(handleClick).not.toHaveBeenCalled()

      rerender(
        <Button isLoading onClick={handleClick}>
          Loading
        </Button>
      )
      expect(screen.getByRole('button')).toBeDisabled()
      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })

  describe('Input', () => {
    it('renders input with label and helper text', () => {
      render(
        <Input
          label="Repository Name"
          helperText="Unique repo identifier"
          placeholder="my-repo"
        />
      )

      expect(screen.getByLabelText(/repository name/i)).toBeInTheDocument()
      expect(screen.getByText(/unique repo identifier/i)).toBeInTheDocument()
    })

    it('renders error state with role="alert"', () => {
      render(
        <Input
          label="Git URL"
          error="Invalid HTTPS git repository URL"
          defaultValue="ssh://git"
        />
      )

      const errorAlert = screen.getByRole('alert')
      expect(errorAlert).toBeInTheDocument()
      expect(errorAlert).toHaveTextContent('Invalid HTTPS git repository URL')
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
    })
  })

  describe('Badge', () => {
    it('renders all variants and sizes correctly', () => {
      const { rerender } = render(<Badge variant="success">Active</Badge>)
      expect(screen.getByText('Active')).toHaveClass('text-emerald-300')

      rerender(<Badge variant="error">Failed</Badge>)
      expect(screen.getByText('Failed')).toHaveClass('text-rose-300')

      rerender(<Badge variant="warning">Parsing</Badge>)
      expect(screen.getByText('Parsing')).toHaveClass('text-amber-300')
    })
  })

  describe('Card', () => {
    it('renders complete card structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Repo Title</CardTitle>
            <CardDescription>Description text</CardDescription>
          </CardHeader>
          <CardContent>Main Content</CardContent>
          <CardFooter>Footer Action</CardFooter>
        </Card>
      )

      expect(screen.getByText('Repo Title')).toBeInTheDocument()
      expect(screen.getByText('Description text')).toBeInTheDocument()
      expect(screen.getByText('Main Content')).toBeInTheDocument()
      expect(screen.getByText('Footer Action')).toBeInTheDocument()
    })
  })

  describe('Spinner', () => {
    it('renders accessible status role and label', () => {
      render(<Spinner label="Processing files..." />)
      const spinner = screen.getByRole('status')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveAttribute('aria-label', 'Processing files...')
    })
  })

  describe('Tooltip', () => {
    it('shows tooltip content on hover/focus and hides on leave', async () => {
      render(
        <Tooltip content="Tooltip description" delayDuration={0}>
          <button>Hover trigger</button>
        </Tooltip>
      )

      const trigger = screen.getByText('Hover trigger')
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()

      fireEvent.mouseEnter(trigger.parentElement!)
      await waitFor(() => {
        expect(screen.getByRole('tooltip')).toHaveTextContent('Tooltip description')
      })

      fireEvent.mouseLeave(trigger.parentElement!)
      await waitFor(() => {
        expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
      })
    })
  })
})
