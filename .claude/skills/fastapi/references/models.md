# Pydantic Models in FastAPI

## Basic Model

```python
from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime = Field(default_factory=datetime.now)
```

## Field Validation

```python
from pydantic import BaseModel, Field, field_validator

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Must be positive")
    quantity: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("name")
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        return v.title()
```

## Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str = "USA"

class Company(BaseModel):
    name: str
    address: Address
    employees: list["Employee"] = []

class Employee(BaseModel):
    name: str
    company: Company | None = None
```

## Model Inheritance

```python
class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None

class UserInDB(UserBase):
    id: int
    hashed_password: str

class UserOut(UserBase):
    id: int

    model_config = {"from_attributes": True}  # For ORM
```

## Common Patterns

```python
# Generic response wrapper
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    data: T
    message: str = "success"

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

# Usage
@app.get("/users/", response_model=PaginatedResponse[UserOut])
def list_users():
    ...
```

## Custom Types

```python
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Annotated
from pydantic.functional_validators import AfterValidator

def validate_username(v: str) -> str:
    if not v.isalnum():
        raise ValueError("must be alphanumeric")
    return v.lower()

Username = Annotated[str, AfterValidator(validate_username)]

class User(BaseModel):
    username: Username
    email: EmailStr
    website: HttpUrl | None = None
```

## Model Config

```python
class User(BaseModel):
    model_config = {
        "from_attributes": True,      # Enable ORM mode
        "str_strip_whitespace": True, # Strip whitespace
        "str_min_length": 1,          # Min string length
        "extra": "forbid",            # No extra fields allowed
        "json_schema_extra": {        # OpenAPI examples
            "examples": [
                {"name": "John", "email": "john@example.com"}
            ]
        }
    }
```

## Serialization

```python
user = User(name="John", email="john@example.com")

# To dict
user.model_dump()
user.model_dump(exclude={"password"})
user.model_dump(include={"name", "email"})
user.model_dump(exclude_unset=True)
user.model_dump(exclude_none=True)

# To JSON
user.model_dump_json()
```
