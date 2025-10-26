from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.init import init_db
from beanie import init_beanie

from app.modules.auth.model import Account
from app.modules.shippers.model import Shipper
from app.modules.shipments.model import Shipment
from app.modules.users.model import User
from app.modules.orders.model import Order
from app.modules.auth.model import Role

from app.modules.auth.routes import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.products.routes import router as products_router
from app.modules.orders.routes import router as orders_router
from app.modules.categories.routes import router as categories_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.shippers.routes import router as shippers_router
from app.modules.admin_accountview.routes import router as admin_accountview_router

# ✅ Tạo app chính
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cosmetic Store API (FastAPI + MongoDB + Beanie)"
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
    allow_origins=origins,          # ✅ Cho phép frontend
    allow_credentials=True,
    allow_methods=["*"],            # ✅ Cho tất cả phương thức (POST, GET, ...)
    allow_headers=["*"],            # ✅ Cho tất cả headers (Authorization, Content-Type,...)
)


# ✅ Gắn các router (API modules)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(reviews_router, prefix="/api/v1/reviews", tags=["Reviews"])
app.include_router(shippers_router, prefix="/api/v1/shippers", tags=["Shippers"])
app.include_router(admin_accountview_router, prefix="/api/v1/admin", tags=["Admin"])

# ✅ Khi app khởi động
@app.on_event("startup")
async def on_startup() -> None:
    await init_db()

    # Khởi tạo các role mặc định
    for role_name in ["User", "Admin"]:
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
