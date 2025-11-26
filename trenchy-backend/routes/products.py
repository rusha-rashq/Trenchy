from fastapi import APIRouter, HTTPException
from utils.loader import load_products

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
def get_all_products():
    return load_products()


@router.get("/{product_id}")
def get_product(product_id: str):
    products = load_products()
    p = next((x for x in products if x["id"] == product_id), None)

    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    return p
