# FastAPI Hello World API

A simple REST API built with FastAPI.

## Setup

```bash
pip install "fastapi[standard]"
```

## Run

```bash
fastapi dev main.py
```

## Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Returns Hello World |
| GET | `/hello/{name}` | Returns personalized greeting |
| GET | `/docs` | Swagger UI documentation |

## Example

```bash
curl http://127.0.0.1:8000/
# {"message":"Hello World"}

curl http://127.0.0.1:8000/hello/Salman
# {"message":"Hello Salman!"}
```
