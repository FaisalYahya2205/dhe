from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "ok"}


@router.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None) -> dict:
    return {"item_id": item_id, "q": q}
