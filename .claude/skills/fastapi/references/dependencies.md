# Dependency Injection

## Basic Dependency

```python
from fastapi import Depends

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
def list_items(db = Depends(get_db)):
    return db.get_items()
```

## Class-Based Dependencies

```python
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit

@app.get("/items/")
def list_items(pagination: Pagination = Depends()):
    return {"skip": pagination.skip, "limit": pagination.limit}
```

## Dependency with Parameters

```python
def get_current_user(token: str = Header(...)):
    user = decode_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

def require_role(role: str):
    def checker(user = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker

@app.get("/admin/")
def admin_panel(user = Depends(require_role("admin"))):
    return {"user": user.name}
```

## Chained Dependencies

```python
def get_db():
    yield Database()

def get_user_repo(db = Depends(get_db)):
    return UserRepository(db)

def get_current_user(
    token: str = Header(...),
    repo = Depends(get_user_repo)
):
    return repo.get_by_token(token)

@app.get("/me")
def get_me(user = Depends(get_current_user)):
    return user
```

## Global Dependencies

```python
# Apply to all routes
app = FastAPI(dependencies=[Depends(verify_api_key)])

# Apply to router
router = APIRouter(dependencies=[Depends(get_current_user)])

# Apply to specific route
@app.get("/items/", dependencies=[Depends(log_request)])
def list_items():
    ...
```

## Annotated Dependencies (Recommended)

```python
from typing import Annotated

DBDep = Annotated[Database, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]

@app.get("/items/")
def list_items(db: DBDep, user: UserDep):
    return db.get_user_items(user.id)
```

## Context Manager Dependencies

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_db():
    db = await AsyncDatabase.connect()
    try:
        yield db
    finally:
        await db.close()

@app.get("/items/")
async def list_items(db = Depends(get_async_db)):
    return await db.get_items()
```

## Common Patterns

```python
# Settings dependency
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str

@lru_cache
def get_settings():
    return Settings()

SettingsDep = Annotated[Settings, Depends(get_settings)]

# Service layer pattern
class ItemService:
    def __init__(self, db: DBDep, user: UserDep):
        self.db = db
        self.user = user

    def list_items(self):
        return self.db.get_items(owner=self.user.id)

@app.get("/items/")
def list_items(service: ItemService = Depends()):
    return service.list_items()
```
