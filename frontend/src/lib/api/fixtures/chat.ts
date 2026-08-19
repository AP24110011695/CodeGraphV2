import type {
  ChatSessionResponse,
  ChatMessageResponse,
  SearchResult,
} from '../types'

export const mockChatSessions: ChatSessionResponse[] = [
  {
    id: 'cs-001',
    repository_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    title: 'Authentication & Token Lifecycle',
    created_at: '2026-08-02T11:00:00Z',
    updated_at: '2026-08-02T11:05:00Z',
  },
]

export const mockChatMessages: ChatMessageResponse[] = [
  {
    id: 'msg-001',
    session_id: 'cs-001',
    role: 'user',
    content: 'How does user login work in this codebase?',
    created_at: '2026-08-02T11:00:00Z',
  },
  {
    id: 'msg-002',
    session_id: 'cs-001',
    role: 'assistant',
    content:
      'User login is handled in `app/api/v1/auth.py` via the `login_endpoint` router handler. It delegates credential verification to `AuthService.login()` in `app/services/auth.py`, which checks the user password hash and returns a 24-hour HS256 JWT access token.',
    sources: [
      {
        path: 'app/api/v1/auth.py',
        start_line: 14,
        end_line: 28,
        symbol_name: 'login_endpoint',
      },
      {
        path: 'app/services/auth.py',
        start_line: 18,
        end_line: 32,
        symbol_name: 'AuthService.login',
      },
    ],
    created_at: '2026-08-02T11:00:05Z',
  },
]

export const mockSearchResults: SearchResult[] = [
  {
    chunk_id: 'chk-01',
    file_id: 'f1001-auth-py',
    path: 'app/services/auth.py',
    content: `def login(self, username: str, password_hash: str) -> str:
    user = User.find_by_username(username)
    if not user or not user.verify_password(password_hash):
        raise ValueError("Invalid username or password")
    payload = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "username": user.username,
    }
    return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)`,
    start_line: 18,
    end_line: 32,
    score: 0.94,
    chunk_type: 'symbol',
    symbol_id: 's1-auth-02',
  },
  {
    chunk_id: 'chk-02',
    file_id: 'f1002-router-py',
    path: 'app/api/v1/auth.py',
    content: `@router.post("/login", response_model=TokenResponse)
async def login_endpoint(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    try:
        token = auth.login(payload.username, payload.password)
        return TokenResponse(access_token=token, token_type="bearer")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))`,
    start_line: 14,
    end_line: 28,
    score: 0.89,
    chunk_type: 'symbol',
    symbol_id: 's2-router-01',
  },
]
