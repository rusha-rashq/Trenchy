import json
from functools import lru_cache


@lru_cache()
def load_products():
    with open("products.json", "r") as f:
        return json.load(f)
