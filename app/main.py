# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.db.init import init_db

# Role model removed - roles are now embedded as strings in Account

from app.modules.auth.routes import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.products.routes import router as products_router
from app.modules.orders.routes import router as orders_router
from app.modules.categories.routes import router as categories_router
from app.modules.brands.routes import router as brands_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.shippers.routes import router as shippers_router

from app.modules.account.routes import router as account_router
from app.modules.shipments.routes import router as shipments_router
from app.modules.payments.routes import router as payments_router
from app.modules.chat.routes import router as chat_router

# Create main app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cosmetic Store API (FastAPI + MongoDB + Beanie)",
    redirect_slashes=False,
)


# Configure CORS before including routers
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # Vite alternate port
    "http://127.0.0.1:5174",
    "http://localhost",
    "http://127.0.0.1",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (API modules)
try:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(products_router, prefix="/api/products", tags=["Products"])
    app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
    app.include_router(categories_router, prefix="/api/categories", tags=["Categories"])
    app.include_router(reviews_router, prefix="/api/reviews", tags=["Reviews"])
    app.include_router(shippers_router, prefix="/api/shippers", tags=["Shippers"])
    app.include_router(shipments_router, prefix="/api/shipments", tags=["shipments"])
    app.include_router(account_router, prefix="/api/accounts", tags=["Account"])
    app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
    app.include_router(chat_router, prefix="/api", tags=["Chat"])
    app.include_router(brands_router, prefix="/api/brands", tags=["Brands"])

except Exception as e:
    print("Error registering routers: {}".format(e))
    import traceback

    traceback.print_exc()


# Startup event
@app.on_event("startup")
async def on_startup() -> None:
    import traceback

    try:
        await init_db()

        # Roles are now embedded as strings in Account model
        # No need to initialize roles collection
    except Exception:
        # Print full traceback to container logs for easier debugging but don't re-raise
        print("Error during startup initialization:")
        traceback.print_exc()
        # Optionally, you may want to re-raise in production. For now we keep server up so requests
        # hit the app and we can see errors in logs. Adjust as needed.


uploads_dir = Path("public/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "version": settings.APP_VERSION}
