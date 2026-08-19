import { Link } from '@tanstack/react-router'
import { FileQuestion, ArrowLeft } from 'lucide-react'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'

export function NotFoundComponent() {
  return (
    <div className="flex h-full min-h-[450px] items-center justify-center p-8">
      <EmptyState
        icon={<FileQuestion className="h-10 w-10 text-slate-500" />}
        title="404 — Page Not Found"
        description="The page or resource you are looking for does not exist or has been moved."
        action={
          <Link to="/">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<ArrowLeft className="h-4 w-4" />}
            >
              Back to Repositories
            </Button>
          </Link>
        }
      />
    </div>
  )
}
