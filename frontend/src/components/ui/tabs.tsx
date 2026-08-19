import * as React from 'react'
import { cn } from '@/lib/utils/cn'

interface TabsContextValue {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const context = React.useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs compound components must be rendered within <Tabs>')
  }
  return context
}

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
}

export function Tabs({
  value: controlledValue,
  defaultValue,
  onValueChange,
  className,
  children,
  ...props
}: TabsProps) {
  const [uncontrolledValue, setUncontrolledValue] = React.useState(defaultValue || '')
  const isControlled = controlledValue !== undefined
  const value = isControlled ? controlledValue : uncontrolledValue

  const handleValueChange = React.useCallback(
    (newValue: string) => {
      if (!isControlled) {
        setUncontrolledValue(newValue)
      }
      onValueChange?.(newValue)
    },
    [isControlled, onValueChange]
  )

  return (
    <TabsContext.Provider value={{ value, onValueChange: handleValueChange }}>
      <div className={cn('w-full', className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

export type TabsListProps = React.HTMLAttributes<HTMLDivElement>

export function TabsList({ className, children, ...props }: TabsListProps) {
  const listRef = React.useRef<HTMLDivElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!listRef.current) return
    const tabs = Array.from(
      listRef.current.querySelectorAll<HTMLButtonElement>('[role="tab"]:not([disabled])')
    )
    const activeIndex = tabs.findIndex((t) => t === document.activeElement)
    if (activeIndex === -1) return

    let targetTab: HTMLButtonElement | null = null

    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault()
      targetTab = tabs[(activeIndex + 1) % tabs.length]
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault()
      targetTab = tabs[(activeIndex - 1 + tabs.length) % tabs.length]
    } else if (e.key === 'Home') {
      e.preventDefault()
      targetTab = tabs[0]
    } else if (e.key === 'End') {
      e.preventDefault()
      targetTab = tabs[tabs.length - 1]
    }

    if (targetTab) {
      targetTab.focus()
      targetTab.click()
    }
  }

  return (
    <div
      ref={listRef}
      role="tablist"
      onKeyDown={handleKeyDown}
      className={cn(
        'inline-flex h-10 items-center justify-center rounded-lg bg-slate-800/80 p-1 text-slate-400 border border-slate-700/60',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export interface TabsTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
}

export function TabsTrigger({
  value,
  className,
  children,
  disabled,
  ...props
}: TabsTriggerProps) {
  const { value: activeValue, onValueChange } = useTabsContext()
  const isSelected = activeValue === value

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isSelected}
      aria-controls={`panel-${value}`}
      id={`tab-${value}`}
      tabIndex={isSelected ? 0 : -1}
      disabled={disabled}
      onClick={() => onValueChange(value)}
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:pointer-events-none disabled:opacity-50',
        isSelected
          ? 'bg-slate-900 text-slate-100 shadow-sm'
          : 'hover:bg-slate-700/50 hover:text-slate-200',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export interface TabsContentProps
  extends React.HTMLAttributes<HTMLDivElement> {
  value: string
}

export function TabsContent({
  value,
  className,
  children,
  ...props
}: TabsContentProps) {
  const { value: activeValue } = useTabsContext()
  const isSelected = activeValue === value

  if (!isSelected) return null

  return (
    <div
      role="tabpanel"
      id={`panel-${value}`}
      aria-labelledby={`tab-${value}`}
      tabIndex={0}
      className={cn(
        'mt-3 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
