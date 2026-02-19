# Domain: Authentication

**Owner:** TBD
**Status:** Not started
**Language:** Python

## Scope

User authentication and authorization for MeshWiki:
- User accounts and sessions
- Login/logout flows
- Protected routes
- Role-based access control (future)

**Not in scope:** Graph queries, page rendering, infrastructure

## Current State

No authentication exists. The wiki is fully open - anyone can read, create, edit, and delete pages.

## Design Decisions

| Decision | Status | Options |
|----------|--------|---------|
| Auth method | TBD | Sessions, JWT, OAuth |
| User storage | TBD | Database, file-based, LDAP |
| Session store | TBD | Redis, signed cookies, database |

## Requirements

### Must Have (MVP)
- [ ] User registration (username/password)
- [ ] Login/logout
- [ ] Session management
- [ ] Protected edit/delete routes
- [ ] Public read access (configurable)

### Should Have
- [ ] Password reset flow
- [ ] Remember me functionality
- [ ] CSRF protection for forms

### Could Have
- [ ] OAuth providers (GitHub, Google)
- [ ] Role-based permissions (admin, editor, viewer)
- [ ] Per-page access control
- [ ] API token authentication

## Architecture Options

### Option A: Session-based (Recommended for MVP)
```
Browser → Cookie (session_id) → Server → Session Store → User
```
- Simple, well-understood
- Works well with HTMX
- Requires session storage

### Option B: JWT
```
Browser → Bearer Token → Server → Verify signature → Claims
```
- Stateless
- Better for API clients
- More complex refresh logic

### Option C: OAuth-only
```
Browser → OAuth Provider → Callback → Create session
```
- No password management
- Depends on external providers
- Good for internal tools

## Proposed Implementation

### Dependencies
```toml
# Add to pyproject.toml
"passlib[bcrypt]>=1.7",  # Password hashing
"python-jose>=3.3",       # JWT (if needed)
"itsdangerous>=2.0",      # Signed cookies
```

### User Model
```python
class User(BaseModel):
    id: str
    username: str
    email: str | None
    password_hash: str
    created_at: datetime
    is_admin: bool = False
```

### Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/login` | Login form |
| POST | `/login` | Authenticate |
| POST | `/logout` | End session |
| GET | `/register` | Registration form |
| POST | `/register` | Create account |

### Middleware
```python
async def require_auth(request: Request):
    """Dependency that requires authenticated user."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Authentication required")
    return user
```

## Integration Points

| Component | Integration |
|-----------|-------------|
| Routes | Add `Depends(require_auth)` to protected endpoints |
| Templates | Show login/logout in header, user info |
| Storage | Need user storage backend |
| Config | `MESHWIKI_AUTH_ENABLED`, `MESHWIKI_SECRET_KEY` |

## Security Considerations

- Hash passwords with bcrypt (cost factor 12+)
- Use secure, httponly cookies for sessions
- Implement rate limiting on login
- CSRF tokens for state-changing operations
- Secure password reset tokens (time-limited, single-use)

## Testing Strategy

- Unit tests for password hashing, token generation
- Integration tests for login/logout flows
- Security tests for protected routes
- Test session expiration and renewal
