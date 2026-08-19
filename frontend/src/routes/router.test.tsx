import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import {
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
  Outlet,
} from '@tanstack/react-router'

// Import page components directly rather than navigating a shared singleton router.
import { RepositoriesIndexPage } from './repositories/index'
import { RepositoryFilesPage } from './repositories/files'
import { RepositoryGraphPage } from './repositories/graph'
import { RepositorySearchPage } from './repositories/search'
import { RepositoryChatPage } from './repositories/chat'
import { SettingsPage } from './settings'
import { NotFoundComponent } from './not-found'

const REPO_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'

// Build a minimal router for a given top-level component.
// We use `beforeEach` / per-test router instances to avoid shared state timeouts.
async function renderRoute<P extends Record<string, string> = Record<string, string>>(
  path: string,
  Component: (props: { params: P }) => React.ReactNode,
  params?: P
) {
  const rootRoute = createRootRoute({
    component: () => <Outlet />,
    notFoundComponent: NotFoundComponent,
  })

  const route = createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: Component as () => React.ReactNode,
  })

  const r = createRouter({
    routeTree: rootRoute.addChildren([route]),
    defaultNotFoundComponent: NotFoundComponent,
  })

  await act(async () => {
    // navigate to the test path with any params
    const to = params
      ? path.replace(/\$(\w+)/g, (_, key) => params[key] ?? key)
      : path
    await r.navigate({ to } as Parameters<typeof r.navigate>[0])
    await r.load()
  })

  render(<RouterProvider router={r} />)
}

describe('Router Integration', () => {
  it('renders repository list at /', async () => {
    await renderRoute('/', () => <RepositoriesIndexPage />)

    expect(screen.getByRole('heading', { name: /repositories/i })).toBeInTheDocument()
    expect(screen.getByText('fastapi-backend')).toBeInTheDocument()
  })

  it('navigates to /settings and renders Settings page', async () => {
    await renderRoute('/settings', () => <SettingsPage />)

    expect(screen.getByText('Connection Settings')).toBeInTheDocument()
    expect(screen.getByText('Backend Configuration')).toBeInTheDocument()
  })

  it('navigates to /repositories/$repoId/files and renders file explorer', async () => {
    const path = `/repositories/${REPO_ID}/files`
    const rootRoute = createRootRoute({
      component: () => <Outlet />,
      notFoundComponent: NotFoundComponent,
    })
    const route = createRoute({
      getParentRoute: () => rootRoute,
      path,
      component: RepositoryFilesPage,
    })
    const r = createRouter({ routeTree: rootRoute.addChildren([route]) })
    await act(async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await r.navigate({ to: path } as any)
      await r.load()
    })
    render(<RouterProvider router={r} />)

    expect(screen.getByText('File Explorer & Code Viewer')).toBeInTheDocument()
    // filename appears in both the sidebar file list and the CodeBlock header
    expect(screen.getAllByText('app/services/auth.py').length).toBeGreaterThanOrEqual(1)
  })

  it('navigates to /repositories/$repoId/graph and renders graph placeholder', async () => {
    const path = `/repositories/${REPO_ID}/graph`
    const rootRoute = createRootRoute({ component: () => <Outlet /> })
    const route = createRoute({
      getParentRoute: () => rootRoute,
      path,
      component: RepositoryGraphPage,
    })
    const r = createRouter({ routeTree: rootRoute.addChildren([route]) })
    await act(async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await r.navigate({ to: path } as any)
      await r.load()
    })
    render(<RouterProvider router={r} />)

    expect(screen.getByText('Dependency Graph Visualization')).toBeInTheDocument()
    expect(screen.getByText('Interactive 3D Dependency Graph')).toBeInTheDocument()
  })

  it('navigates to /repositories/$repoId/search and renders search placeholder', async () => {
    const path = `/repositories/${REPO_ID}/search`
    const rootRoute = createRootRoute({ component: () => <Outlet /> })
    const route = createRoute({
      getParentRoute: () => rootRoute,
      path,
      component: RepositorySearchPage,
    })
    const r = createRouter({ routeTree: rootRoute.addChildren([route]) })
    await act(async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await r.navigate({ to: path } as any)
      await r.load()
    })
    render(<RouterProvider router={r} />)

    expect(screen.getByText('Semantic Code Search')).toBeInTheDocument()
  })

  it('navigates to /repositories/$repoId/chat and renders AI chat placeholder', async () => {
    const path = `/repositories/${REPO_ID}/chat`
    const rootRoute = createRootRoute({ component: () => <Outlet /> })
    const route = createRoute({
      getParentRoute: () => rootRoute,
      path,
      component: RepositoryChatPage,
    })
    const r = createRouter({ routeTree: rootRoute.addChildren([route]) })
    await act(async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await r.navigate({ to: path } as any)
      await r.load()
    })
    render(<RouterProvider router={r} />)

    expect(screen.getByText('AI Assistant Chat')).toBeInTheDocument()
  })

  it('renders 404 NotFoundComponent on unmatched route', async () => {
    const rootRoute = createRootRoute({
      component: () => <Outlet />,
      notFoundComponent: NotFoundComponent,
    })
    const r = createRouter({
      routeTree: rootRoute.addChildren([
        createRoute({
          getParentRoute: () => rootRoute,
          path: '/',
          component: () => <div>Home</div>,
        }),
      ]),
      defaultNotFoundComponent: NotFoundComponent,
    })
    await act(async () => {
      await r.navigate({ to: '/definitely-does-not-exist-99999' as '/' })
      await r.load()
    })
    render(<RouterProvider router={r} />)

    expect(screen.getByText('404 — Page Not Found')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to repositories/i })).toBeInTheDocument()
  })
})
