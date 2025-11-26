from fastapi import APIRouter, HTTPException
from utils.embeddings import semantic_answer
from utils.loader import load_products

router = APIRouter(prefix="/recommend", tags=["Recommend"])


@router.get("/{product_id}")
def recommend(product_id: str):
    products = load_products()
    p = next((x for x in products if x["id"] == product_id), None)

    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    related = [
        x for x in products if x["category"] == p["category"] and x["id"] != product_id
    ]

    return {"product": p, "related": related[:6]}


router = APIRouter()


@router.post("/semantic_answer")
def semantic_answer_route(payload: dict):
    question = payload["question"]
    product = payload["product"]
    answer = semantic_answer(question, product)
    return {"answer": answer}
