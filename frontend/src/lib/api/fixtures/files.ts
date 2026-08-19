import type { FileDetail, SymbolResponse } from '../types'

export const mockSymbolsAuth: SymbolResponse[] = [
  {
    id: 's1-auth-01',
    name: 'AuthService',
    kind: 'class',
    start_line: 10,
    end_line: 45,
    is_exported: true,
    docstring: 'Provides user authentication and JWT token lifecycle management.',
  },
  {
    id: 's1-auth-02',
    name: 'login',
    kind: 'method',
    start_line: 18,
    end_line: 32,
    is_exported: true,
    docstring: 'Authenticate user credentials and return access token.',
  },
  {
    id: 's1-auth-03',
    name: 'verify_token',
    kind: 'method',
    start_line: 34,
    end_line: 44,
    is_exported: true,
    docstring: 'Verify incoming JWT payload and decode subject.',
  },
]

export const mockSymbolsRouter: SymbolResponse[] = [
  {
    id: 's2-router-01',
    name: 'login_endpoint',
    kind: 'function',
    start_line: 14,
    end_line: 28,
    is_exported: true,
    docstring: 'REST API endpoint for user login.',
  },
  {
    id: 's2-router-02',
    name: 'refresh_endpoint',
    kind: 'function',
    start_line: 30,
    end_line: 42,
    is_exported: true,
    docstring: 'REST API endpoint to refresh expired tokens.',
  },
]

export const mockFileAuthPy: FileDetail = {
  id: 'f1001-auth-py',
  repository_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  path: 'app/services/auth.py',
  language: 'python',
  size_bytes: 1420,
  line_count: 45,
  is_binary: false,
  content: `"""Authentication Service and Token Management."""

from datetime import datetime, timedelta
import jwt
from app.config import get_settings
from app.models.user import User

settings = get_settings()

class AuthService:
    """Provides user authentication and JWT token lifecycle management."""

    def __init__(self, secret_key: str = settings.SECRET_KEY):
        self.secret_key = secret_key
        self.algorithm = "HS256"

    def login(self, username: str, password_hash: str) -> str:
        """Authenticate user credentials and return access token."""
        user = User.find_by_username(username)
        if not user or not user.verify_password(password_hash):
            raise ValueError("Invalid username or password")
        
        payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "username": user.username,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        """Verify incoming JWT payload and decode subject."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.PyJWTError as exc:
            raise ValueError("Token is invalid or expired") from exc
`,
  symbols: mockSymbolsAuth,
}

export const mockFileRouterPy: FileDetail = {
  id: 'f1002-router-py',
  repository_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  path: 'app/api/v1/auth.py',
  language: 'python',
  size_bytes: 1250,
  line_count: 42,
  is_binary: false,
  content: `"""Authentication REST API Endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service() -> AuthService:
    return AuthService()

@router.post("/login", response_model=TokenResponse)
async def login_endpoint(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    """REST API endpoint for user login."""
    try:
        token = auth.login(payload.username, payload.password)
        return TokenResponse(access_token=token, token_type="bearer")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

@router.post("/refresh", response_model=TokenResponse)
async def refresh_endpoint(refresh_token: str, auth: AuthService = Depends(get_auth_service)):
    """REST API endpoint to refresh expired tokens."""
    payload = auth.verify_token(refresh_token)
    return TokenResponse(access_token=refresh_token, token_type="bearer")
`,
  symbols: mockSymbolsRouter,
}

export const mockFileConfigPy: FileDetail = {
  id: 'f1003-config-py',
  repository_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  path: 'app/config.py',
  language: 'python',
  size_bytes: 840,
  line_count: 25,
  is_binary: false,
  content: `"""Global configuration settings."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CodeGraph Backend"
    SECRET_KEY: str = "super-secret-key-123"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codegraph"

def get_settings() -> Settings:
    return Settings()
`,
  symbols: [
    {
      id: 's3-config-01',
      name: 'Settings',
      kind: 'class',
      start_line: 5,
      end_line: 9,
      is_exported: true,
      docstring: 'Global settings class.',
    },
  ],
}

export const mockFilesByRepo: Record<string, FileDetail[]> = {
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11': [
    mockFileAuthPy,
    mockFileRouterPy,
    mockFileConfigPy,
  ],
}
