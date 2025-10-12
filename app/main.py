from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init import init_db
from app.modules.products.routes import router as products_router
from app.modules.users.router import router as users_router
from app.modules.auth.routes import router as auth_router
from app.modules.orders.routes import router as orders_router
from app.modules.categories.routes import router as categories_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.shippers.routes import router as shippers_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def on_startup() -> None:  # noqa: D401
        await init_db()

    # Routers (versioned)
    app.include_router(auth_router)
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(products_router, prefix="/api/v1/products", tags=["products"])
    app.include_router(orders_router, prefix="/api/v1/orders", tags=["orders"])
    app.include_router(
        categories_router, prefix="/api/v1/categories", tags=["categories"]
    )
    app.include_router(
        reviews_router, prefix="/api/v1", tags=["reviews"]
    )  # includes /products/{id}/reviews and /reviews/{id}
    app.include_router(shippers_router, tags=["shippers"])

    @app.get("/", tags=["health"])
    async def root():
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION}

    return app
