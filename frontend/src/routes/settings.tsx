import { Settings as SettingsIcon, Server, Key, Save } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export function SettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <SettingsIcon className="h-6 w-6 text-indigo-400" /> Connection Settings
        </h1>
        <p className="text-sm text-slate-400">
          Configure backend API endpoint, authentication keys, and mock API mode
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backend Configuration</CardTitle>
          <CardDescription>
            Specify where the CodeGraph v2 backend service is running
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Backend Base URL"
            defaultValue="http://localhost:8000"
            helperText="Default local backend URL is http://localhost:8000"
            leftIcon={<Server className="h-4 w-4" />}
          />
          <Input
            label="API Key (Optional for local dev)"
            placeholder="cg_live_..."
            helperText="Required only when connecting to a hosted or secured backend instance"
            leftIcon={<Key className="h-4 w-4" />}
          />
        </CardContent>
        <CardFooter className="flex justify-between border-t border-slate-800 pt-4">
          <Button variant="secondary" size="sm">
            Test Connection
          </Button>
          <Button variant="primary" size="sm" leftIcon={<Save className="h-4 w-4" />}>
            Save Changes
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
