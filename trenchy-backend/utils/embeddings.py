import json

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_products():
    with open("products.json") as f:
        return json.load(f)


PRODUCTS = load_products()


def get_product(product_id):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def semantic_answer(question, product):
    context = f"""
    Name: {product['name']}
    Description: {product['description']}
    Price: ₹{product['price']}
    Stock: {product['stock_level']}
    Category: {product['category']}
    """

    # Encode both
    embeddings = model.encode([question, context])

    similarity = util.cos_sim(embeddings[0], embeddings[1])

    if similarity >= 0.3:
        return f"Here's what I know: {product['description']}"
    else:
        return "I'm not fully sure, but this product is quite popular based on past customers!"
