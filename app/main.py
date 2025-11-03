from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
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

from app.modules.account.routes import router as account_router
from app.modules.shipments.routes import router as shipments_router

#  Tạo app chính
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cosmetic Store API (FastAPI + MongoDB + Beanie)",
    redirect_slashes=False,  # Tắt redirect tự động khi thiếu/thừa trailing slash
)


#  Cấu hình CORS trước khi include router
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
    allow_origins=origins,  #  Cho phép frontend
    allow_credentials=True,
    allow_methods=["*"],  #  Cho tất cả phương thức (POST, GET, ...)
    allow_headers=["*"],  #  Cho tất cả headers (Authorization, Content-Type,...)
)

#  Gắn các router (API modules)
try:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    
    # Products router - quan trọng nhất
    app.include_router(products_router, prefix="/api/products", tags=["Products"])
    print(f"✅ Products router registered with {len(products_router.routes)} routes")
    for route in products_router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"   - {' '.join(route.methods)} /api/products{route.path}")
    
    app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
    app.include_router(categories_router, prefix="/api/categories", tags=["Categories"])
    app.include_router(reviews_router, prefix="/api/reviews", tags=["Reviews"])
    app.include_router(shippers_router, prefix="/api/shippers", tags=["Shippers"])
    app.include_router(shipments_router, prefix="/api/shipments", tags=["shipments"])
    app.include_router(account_router, prefix="/api/accounts", tags=["Account"])
except Exception as e:
    print(f"❌ Error registering routers: {e}")
    import traceback
    traceback.print_exc()


#  Khi app khởi động
@app.on_event("startup")
async def on_startup() -> None:
    import traceback

    try:
        await init_db()

        # Khởi tạo các role mặc định
        for role_name in ["User", "Admin"]:
            existing_role = await Role.find_one(Role.RoleName == role_name)
            if not existing_role:
                await Role(RoleName=role_name).insert()
                print(f"✅ Role '{role_name}' đã được tạo.")
    except Exception:
        # Print full traceback to container logs for easier debugging but don't re-raise
        print("Error during startup initialization:")
        traceback.print_exc()
        # Optionally, you may want to re-raise in production. For now we keep server up so requests
        # hit the app and we can see errors in logs. Adjust as needed.


uploads_dir = Path("public/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

#  Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "version": settings.APP_VERSION}


#  Debug: In danh sách route ra console
# print("\n" + "="*60)
# print("📋 ALL REGISTERED ROUTES:")
# print("="*60)
# products_routes = []
# for route in app.routes:
#     if hasattr(route, 'path'):
#         methods = list(getattr(route, 'methods', set()))
#         route_info = f"  {', '.join(methods):<12} {route.path}"
#         print(route_info)
#         if '/api/products' in route.path:
#             products_routes.append(route.path)
# print("="*60)
# print(f"✅ Total routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
# print(f"✅ Products routes found: {len(products_routes)}")
# if products_routes:
#     print("   Products endpoints:")
#     for r in products_routes:
#         print(f"     - {r}")
# else:
#     print("   ⚠️ WARNING: No products routes found!")
# print("="*60 + "\n")





for route in app.routes:
    print(f"✅ Route loaded: {route.path}")