import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
  Outlet,
} from '@tanstack/react-router'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { AppShell, RouteErrorBoundary } from './app-shell'

// Helper: build a minimal router that wraps a component in a router context.
// The root renders an Outlet; the index route renders the passed component.
function makeRouter(Component: () => React.ReactNode) {
  const rootRoute = createRootRoute({
    component: () => <Outlet />,
  })
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: Component,
  })
  return createRouter({
    routeTree: rootRoute.addChildren([indexRoute]),
  })
}

async function renderWithRouter(Component: () => React.ReactNode) {
  const r = makeRouter(Component)
  let result: ReturnType<typeof render> | undefined
  await act(async () => {
    result = render(<RouterProvider router={r} />)
    await r.load()
  })
  return result!
}

describe('Layout Components', () => {
  describe('Sidebar', () => {
    it('renders brand title and main navigation links', async () => {
      await renderWithRouter(() => <Sidebar />)

      expect(screen.getByText('CodeGraph')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /repositories/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument()
    })

    it('toggles collapse on collapse button click', async () => {
      const handleToggle = vi.fn()
      await renderWithRouter(() => (
        <Sidebar collapsed={false} onToggleCollapse={handleToggle} />
      ))

      const toggleBtn = screen.getByLabelText(/collapse sidebar/i)
      await userEvent.click(toggleBtn)
      expect(handleToggle).toHaveBeenCalledTimes(1)
    })
  })

  describe('Header', () => {
    it('renders breadcrumb and theme switcher', async () => {
      await renderWithRouter(() => (
        <Header
          currentRepoName="fastapi-backend"
          currentRepoStatus="ready"
        />
      ))

      expect(screen.getByLabelText('Breadcrumbs')).toBeInTheDocument()
      expect(screen.getByText('Repositories')).toBeInTheDocument()
      expect(screen.getByText('READY')).toBeInTheDocument()
    })
  })

  describe('AppShell', () => {
    it('renders Sidebar, Header, and main content area', async () => {
      await renderWithRouter(() => (
        <AppShell>
          <div data-testid="custom-child">Main Body View</div>
        </AppShell>
      ))

      expect(screen.getByText('CodeGraph')).toBeInTheDocument()
      expect(screen.getByLabelText('Breadcrumbs')).toBeInTheDocument()
      expect(screen.getByTestId('custom-child')).toBeInTheDocument()
    })
  })

  describe('RouteErrorBoundary', () => {
    it('catches render errors and renders ErrorState fallback', () => {
      const originalConsoleError = console.error
      console.error = vi.fn()

      function ThrowingComponent(): React.ReactNode {
        throw new Error('Test boundary crash')
      }

      render(
        <RouteErrorBoundary>
          <ThrowingComponent />
        </RouteErrorBoundary>
      )

      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Application encountered an error')).toBeInTheDocument()
      expect(screen.getByText('Test boundary crash')).toBeInTheDocument()

      console.error = originalConsoleError
    })
  })
})
