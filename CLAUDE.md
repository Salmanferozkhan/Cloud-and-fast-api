# Claude Global Instructions

## Subagent Usage Rules

### Backend Work → Use `backend-architect` subagent
Use for:
- FastAPI, Django, Flask development
- Database models, migrations, SQLModel/SQLAlchemy
- API endpoints, routers, CRUD operations
- Authentication (JWT, OAuth)
- Business logic, services
- Backend testing (pytest)

### Frontend Work → Use `frontend-developer` subagent
Use for:
- Chainlit UI development
- React, Vue, Angular components
- HTML, CSS, JavaScript/TypeScript
- UI/UX fixes, responsive design
- Frontend state management
- Streaming UI, chat interfaces

## Package Manager
- Always use `uv` instead of `pip`
- Install: `uv sync` or `uv sync --all-groups`
- Run: `uv run <command>`

## Code Style
- Follow TDD approach - write tests first
- Use type hints in Python
- Keep functions small and focused
