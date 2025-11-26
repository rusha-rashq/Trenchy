from fastapi import APIRouter, Query
from utils.loader import load_products

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
def search_products(q: str = Query(..., min_length=2)):
    q = q.lower()
    products = load_products()

    results = [
        p
        for p in products
        if q in p["name"].lower()
        or q in p["description"].lower()
        or q in p["category"].lower()
    ]

    return {"query": q, "results": results}
