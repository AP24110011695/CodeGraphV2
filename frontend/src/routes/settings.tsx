import * as React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Settings as SettingsIcon,
  Server,
  Key,
  Save,
  Activity,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Cpu,
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/toast'
import { useConnectionStore } from '@/stores/connection-store'
import { apiClient } from '@/lib/api'

const settingsSchema = z.object({
  apiBaseUrl: z
    .string()
    .min(1, 'Base URL is required')
    .refine(
      (val) =>
        /^https?:\/\/.+/i.test(val) || /^http:\/\/localhost(:\d+)?/i.test(val),
      'Base URL must start with http:// or https://'
    ),
  apiKey: z.string().optional(),
  rememberApiKey: z.boolean(),
  useMockApi: z.boolean(),
})

type SettingsFormData = z.infer<typeof settingsSchema>

export function SettingsPage() {
  const toast = useToast()
  const {
    apiBaseUrl,
    apiKey,
    rememberApiKey,
    useMockApi,
    setApiBaseUrl,
    setApiKey,
    setRememberApiKey,
    setUseMockApi,
    resetSettings,
  } = useConnectionStore()

  const [isTesting, setIsTesting] = React.useState(false)
  const [testResult, setTestResult] = React.useState<{
    success: boolean
    message: string
  } | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      apiBaseUrl,
      apiKey: apiKey || '',
      rememberApiKey,
      useMockApi,
    },
  })

  // Keep form in sync if store changes externally
  React.useEffect(() => {
    reset({
      apiBaseUrl,
      apiKey: apiKey || '',
      rememberApiKey,
      useMockApi,
    })
  }, [apiBaseUrl, apiKey, rememberApiKey, useMockApi, reset])

  const currentUseMock = watch('useMockApi')
  const currentRememberKey = watch('rememberApiKey')

  const onSubmit = (data: SettingsFormData) => {
    setApiBaseUrl(data.apiBaseUrl)
    setApiKey(data.apiKey || null)
    setRememberApiKey(data.rememberApiKey)
    setUseMockApi(data.useMockApi)

    toast.success('Connection settings have been saved.', 'Settings Updated')
  }

  const handleTestConnection = async () => {
    setIsTesting(true)
    setTestResult(null)

    try {
      const res = await apiClient.health()
      const msg = `Status: ${res.status} | Version: ${res.version}`
      setTestResult({ success: true, message: msg })
      toast.success(
        `Backend service is healthy (${res.version || 'v2.0.0'})`,
        'Connection Verified'
      )
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : 'Could not reach backend endpoint'
      setTestResult({ success: false, message: errorMsg })
      toast.error(errorMsg, 'Connection Failed')
    } finally {
      setIsTesting(false)
    }
  }

  const handleResetDefaults = () => {
    resetSettings()
    reset({
      apiBaseUrl: 'http://localhost:8000',
      apiKey: '',
      rememberApiKey: false,
      useMockApi: true,
    })
    setTestResult(null)
    toast.info('Connection settings have been reset to default values.')
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <SettingsIcon className="h-6 w-6 text-indigo-400" /> Connection Settings
          </h1>
          <p className="text-sm text-slate-400">
            Configure backend API connection, credentials, and mock API mode
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={currentUseMock ? 'info' : 'success'}>
            {currentUseMock ? 'Mock API Active' : 'Live API Active'}
          </Badge>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Backend Endpoint Card */}
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>
              Specify where the CodeGraph v2 backend service is running
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Mode Switch: Mock vs Real */}
            <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-4">
              <div className="space-y-0.5">
                <label
                  htmlFor="useMockApi"
                  className="text-sm font-medium text-slate-200 flex items-center gap-2 cursor-pointer"
                >
                  <Cpu className="h-4 w-4 text-indigo-400" />
                  Use In-Memory Mock API
                </label>
                <p className="text-xs text-slate-400">
                  Runs frontend standalone with realistic fixture data without a backend server
                </p>
              </div>
              <input
                id="useMockApi"
                type="checkbox"
                {...register('useMockApi')}
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-950"
              />
            </div>

            {/* Base URL */}
            <div>
              <Input
                label="Backend Base URL"
                id="apiBaseUrl"
                placeholder="http://localhost:8000"
                error={errors.apiBaseUrl?.message}
                helperText="URL of the running FastAPI backend instance (default: http://localhost:8000)"
                leftIcon={<Server className="h-4 w-4" />}
                {...register('apiBaseUrl')}
              />
            </div>

            {/* API Key */}
            <div className="space-y-3">
              <Input
                label="API Key (Optional for local dev)"
                id="apiKey"
                type="password"
                placeholder="cg_live_..."
                error={errors.apiKey?.message}
                helperText="Required only when connecting to a hosted or secured backend instance (REQUIRE_AUTH=true)"
                leftIcon={<Key className="h-4 w-4" />}
                {...register('apiKey')}
              />

              {/* Remember API Key Checkbox & Warning */}
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/30 p-3 space-y-2">
                <label className="flex items-start gap-2.5 cursor-pointer text-xs font-medium text-slate-300">
                  <input
                    type="checkbox"
                    {...register('rememberApiKey')}
                    className="mt-0.5 h-3.5 w-3.5 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Remember this API key on this device across browser sessions</span>
                </label>
                {currentRememberKey && (
                  <div className="flex items-start gap-2 rounded bg-amber-500/10 border border-amber-500/20 p-2 text-[11px] text-amber-300">
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-amber-400" />
                    <span>
                      <strong>Notice:</strong> Your API key will be saved unencrypted in browser localStorage. Do not enable this on shared or public computers.
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Test Connection Status Banner */}
            {testResult && (
              <div
                className={`flex items-center gap-2.5 rounded-lg border p-3 text-xs ${
                  testResult.success
                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                    : 'border-rose-500/30 bg-rose-500/10 text-rose-300'
                }`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}
          </CardContent>
          <CardFooter className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                isLoading={isTesting}
                onClick={handleTestConnection}
                leftIcon={<Activity className="h-4 w-4" />}
              >
                Test Connection
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleResetDefaults}
                leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
              >
                Reset Defaults
              </Button>
            </div>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              leftIcon={<Save className="h-4 w-4" />}
            >
              Save Changes
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
