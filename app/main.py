from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.init import init_db

from app.modules.auth.model import Role

from app.modules.auth.routes import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.products.routes import router as products_router
from app.modules.orders.routes import router as orders_router
from app.modules.categories.routes import router as categories_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.shippers.routes import router as shippers_router
from app.modules.account.routes import router as admin_accountview_router
from app.modules.shipments.routes import router as shipments_router

# ✅ Tạo app chính
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cosmetic Store API (FastAPI + MongoDB + Beanie)",
)


# ✅ Cấu hình CORS trước khi include router
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ✅ Cho phép frontend
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Cho tất cả phương thức (POST, GET, ...)
    allow_headers=["*"],  # ✅ Cho tất cả headers (Authorization, Content-Type,...)
)


# ✅ Gắn các router (API modules)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])

app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])

app.include_router(categories_router, prefix="/api/categories", tags=["Categories"])
app.include_router(reviews_router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(shippers_router, prefix="/api/shippers", tags=["Shippers"])
app.include_router(shipments_router, prefix="/api/shipments", tags=["shipments"])
app.include_router(admin_accountview_router, prefix="/api/admin", tags=["Admin"])


# ✅ Khi app khởi động
@app.on_event("startup")
async def on_startup() -> None:
    await init_db()

    # Khởi tạo các role mặc định
    for role_name in ["User", "Admin", "Shipper"]:
        existing_role = await Role.find_one(Role.RoleName == role_name)
        if not existing_role:
            await Role(RoleName=role_name).insert()
            print(f"✅ Role '{role_name}' đã được tạo.")


# ✅ Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "version": settings.APP_VERSION}


# ✅ Debug: In danh sách route ra console
for route in app.routes:
    print(f"✅ Route loaded: {route.path}")
