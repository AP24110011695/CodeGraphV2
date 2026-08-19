import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders application with router, sidebar, and repository list', async () => {
    render(<App />)

    // Wait for async router mounting
    await waitFor(() => {
      expect(screen.getByText('CodeGraph')).toBeInTheDocument()
    }, { timeout: 10000 })

    // Multiple "Repositories" links appear (sidebar + breadcrumb) — verify at least one
    const repoLinks = screen.getAllByRole('link', { name: /repositories/i })
    expect(repoLinks.length).toBeGreaterThanOrEqual(1)
  })
})
