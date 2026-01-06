"""API routes."""
from fastapi import APIRouter
from app.schemas import ItemCreate, ItemResponse

router = APIRouter(tags=["items"])

# In-memory storage (replace with database)
items_db: dict[int, dict] = {}
counter = 0


@router.get("/items", response_model=list[ItemResponse])
def list_items():
    """List all items."""
    return list(items_db.values())


@router.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate):
    """Create a new item."""
    global counter
    counter += 1
    db_item = {"id": counter, **item.model_dump()}
    items_db[counter] = db_item
    return db_item


@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    """Get item by ID."""
    from fastapi import HTTPException
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    """Delete item by ID."""
    from fastapi import HTTPException
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return None
