import type { RepositoryResponse } from '../types'

export const mockRepositories: RepositoryResponse[] = [
  {
    id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    name: 'fastapi-backend',
    slug: 'fastapi-backend',
    status: 'ready',
    source: 'upload',
    size_bytes: 524288,
    file_count: 18,
    primary_language: 'Python',
    detected_languages: {
      Python: 85,
      SQL: 10,
      Dockerfile: 5,
    },
    frameworks: ['FastAPI', 'SQLAlchemy', 'Pydantic', 'Celery'],
    created_at: '2026-08-01T10:00:00Z',
  },
  {
    id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
    name: 'react-dashboard',
    slug: 'react-dashboard',
    status: 'ready',
    source: 'clone',
    size_bytes: 1048576,
    file_count: 32,
    primary_language: 'TypeScript',
    detected_languages: {
      TypeScript: 80,
      CSS: 15,
      HTML: 5,
    },
    frameworks: ['React', 'TailwindCSS', 'TanStack Router', 'Zustand'],
    created_at: '2026-08-05T14:30:00Z',
  },
  {
    id: 'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    name: 'microservices-gateway',
    slug: 'microservices-gateway',
    status: 'parsing',
    source: 'clone',
    size_bytes: 3145728,
    file_count: 54,
    primary_language: 'TypeScript',
    detected_languages: {
      TypeScript: 70,
      Go: 30,
    },
    frameworks: ['Express', 'Redis', 'gRPC'],
    created_at: '2026-08-10T08:15:00Z',
  },
]
