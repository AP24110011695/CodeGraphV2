import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App Component', () => {
  it('renders the application title and description', () => {
    render(<App />)
    expect(screen.getByText('CodeGraph v2')).toBeInTheDocument()
    expect(
      screen.getByText('AI-Powered Codebase Intelligence Platform')
    ).toBeInTheDocument()
  })
})
