import { FolderGit2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Link } from '@tanstack/react-router'
import { mockRepositories } from '@/lib/api'

export function RepositoriesIndexPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <FolderGit2 className="h-6 w-6 text-indigo-400" /> Repositories
          </h1>
          <p className="text-sm text-slate-400">
            Ingest and analyze your codebases with AI-powered code graph intelligence
          </p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Add Repository
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {mockRepositories.map((repo) => (
          <Link
            key={repo.id}
            to="/repositories/$repoId"
            params={{ repoId: repo.id }}
            className="block group focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-xl"
          >
            <Card className="h-full hover:border-slate-700 transition-colors">
              <CardHeader>
                <CardTitle className="group-hover:text-indigo-400 transition-colors">
                  {repo.name}
                </CardTitle>
                <CardDescription>{repo.primary_language || 'Polyglot'} • {repo.file_count} files</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-400">
                  Status: <span className="capitalize text-slate-200">{repo.status}</span>
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
