from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.products import router as products_router
from routes.recommend import router as recommend_router
from routes.recommend import router as semantic_router
from routes.search import router as search_router

app = FastAPI(
    title="Trenchy Backend API",
    version="1.0.0",
    description="Backend API for Trenchy E-Commerce Platform",
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routes
app.include_router(products_router)
app.include_router(search_router)
app.include_router(recommend_router)


@app.get("/")
def root():
    return {"message": "Trenchy Backend is running!"}


app.include_router(semantic_router)
