import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'
import { RootRouteComponent } from './routes/root'
import { NotFoundComponent } from './routes/not-found'
import { RepositoriesIndexPage } from './routes/repositories/index'
import { RepositoryDetailPage } from './routes/repositories/detail'
import { RepositoryFilesPage } from './routes/repositories/files'
import { RepositoryGraphPage } from './routes/repositories/graph'
import { RepositorySearchPage } from './routes/repositories/search'
import { RepositoryChatPage } from './routes/repositories/chat'
import { SettingsPage } from './routes/settings'
import { KitchenSink } from './components/ui/dev/kitchen-sink'

// 1. Root route
export const rootRoute = createRootRoute({
  component: RootRouteComponent,
  notFoundComponent: NotFoundComponent,
})

// 2. Index route (Repository list)
export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: RepositoriesIndexPage,
})

// 3. Settings route
export const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})

// 4. Repository detail parent route
export const repoDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/repositories/$repoId',
  component: RepositoryDetailPage,
})

// 5. Nested feature tab routes under /repositories/$repoId
export const repoFilesRoute = createRoute({
  getParentRoute: () => repoDetailRoute,
  path: 'files',
  component: RepositoryFilesPage,
})

export const repoGraphRoute = createRoute({
  getParentRoute: () => repoDetailRoute,
  path: 'graph',
  component: RepositoryGraphPage,
})

export const repoSearchRoute = createRoute({
  getParentRoute: () => repoDetailRoute,
  path: 'search',
  component: RepositorySearchPage,
})

export const repoChatRoute = createRoute({
  getParentRoute: () => repoDetailRoute,
  path: 'chat',
  component: RepositoryChatPage,
})

// 6. Dev-only kitchen-sink route
export const kitchenSinkRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dev/kitchen-sink',
  component: KitchenSink,
})

const isDev =
  typeof import.meta !== 'undefined' &&
  (import.meta.env?.DEV || import.meta.env?.MODE === 'test')

const routes = [
  indexRoute,
  settingsRoute,
  repoDetailRoute.addChildren([
    repoFilesRoute,
    repoGraphRoute,
    repoSearchRoute,
    repoChatRoute,
  ]),
  ...(isDev ? [kitchenSinkRoute] : []),
]

export const routeTree = rootRoute.addChildren(routes)

export const router = createRouter({
  routeTree,
  defaultNotFoundComponent: NotFoundComponent,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
