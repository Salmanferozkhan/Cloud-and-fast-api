# FastAPI Basics

## Installation

```bash
pip install "fastapi[standard]"
```

## Minimal App

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

Run: `fastapi dev main.py` (development) or `uvicorn main:app --reload`

## Path Parameters

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):  # Auto-validated as int
    return {"user_id": user_id}

# Multiple parameters
@app.get("/posts/{post_id}/comments/{comment_id}")
def get_comment(post_id: int, comment_id: int):
    return {"post_id": post_id, "comment_id": comment_id}

# Enum paths
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"

@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    return {"model": model_name.value}
```

## Query Parameters

```python
@app.get("/items/")
def list_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# Optional parameters
@app.get("/search/")
def search(q: str | None = None):
    return {"query": q}

# Required query param (no default)
@app.get("/find/")
def find(name: str):  # Required
    return {"name": name}
```

## Request Body

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.post("/items/")
def create_item(item: Item):
    return item

# Path + Query + Body combined
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, q: str | None = None):
    return {"item_id": item_id, **item.model_dump(), "q": q}
```

## Response Model

```python
class ItemOut(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=ItemOut)
def create_item(item: Item):
    return item  # Only name, price returned

# Exclude unset values
@app.get("/items/{id}", response_model=Item, response_model_exclude_unset=True)
def get_item(id: int):
    return {"name": "Foo", "price": 10.0}
```

## Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item

@app.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(id: int):
    return None
```

## Form Data

```python
from fastapi import Form

@app.post("/login/")
def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
```

## File Upload

```python
from fastapi import File, UploadFile

@app.post("/upload/")
async def upload(file: UploadFile):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}

# Multiple files
@app.post("/uploads/")
async def upload_many(files: list[UploadFile]):
    return {"filenames": [f.filename for f in files]}
```

## Headers & Cookies

```python
from fastapi import Header, Cookie

@app.get("/headers/")
def read_headers(user_agent: str = Header(None)):
    return {"User-Agent": user_agent}

@app.get("/cookies/")
def read_cookies(session_id: str = Cookie(None)):
    return {"session_id": session_id}
```
