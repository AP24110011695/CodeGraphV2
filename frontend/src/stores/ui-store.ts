import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export type ThemeMode = 'light' | 'dark' | 'system'

export interface UiState {
  isSidebarCollapsed: boolean
  theme: ThemeMode
  authPromptOpen: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setTheme: (theme: ThemeMode) => void
  setAuthPromptOpen: (open: boolean) => void
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      theme: 'dark',
      authPromptOpen: false,
      toggleSidebar: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      setSidebarCollapsed: (collapsed: boolean) =>
        set({ isSidebarCollapsed: collapsed }),
      setTheme: (theme: ThemeMode) => {
        set({ theme })
        if (typeof document !== 'undefined') {
          const root = document.documentElement
          if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
              .matches
              ? 'dark'
              : 'light'
            root.setAttribute('data-theme', systemTheme)
          } else {
            root.setAttribute('data-theme', theme)
          }
        }
      },
      setAuthPromptOpen: (open: boolean) => set({ authPromptOpen: open }),
    }),
    {
      name: 'codegraph-ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        isSidebarCollapsed: state.isSidebarCollapsed,
        theme: state.theme,
      }),
    }
  )
)
