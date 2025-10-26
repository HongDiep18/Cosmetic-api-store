# Database Seeding Scripts

Scripts để import mock data vào MongoDB cho development.

## 📋 Scripts có sẵn

### 1. `seed_categories.py`
Import categories vào database.

```bash
python -m app.test.seed_categories
```

### 2. `seed_products.py`
Import products vào database.

```bash
python -m app.test.seed_products
```

### 3. `seed_all.py` ⭐ (Khuyến nghị)
Import tất cả data một lần (categories + products).

```bash
python -m app.test.seed_all
```

## 🚀 Cách sử dụng

### Bước 1: Đảm bảo MongoDB đang chạy

```bash
# Nếu dùng Docker
docker-compose up -d mongodb

# Hoặc kiểm tra service
docker ps | grep mongodb
```

### Bước 2: Kiểm tra file .env

Đảm bảo file `.env` có các biến sau:

```env
MONGODB_URI=mongodb://localhost:27018/cosmetic_shop_db
MONGODB_DB=cosmetic_shop_db
SECRET_KEY=your_secret_key_here
```

### Bước 3: Chạy seed script

```bash
cd D:\CNTT\HUIT\NoSQL\Project\Cosmetic-api-store
python -m app.test.seed_all
```

## 📊 Data được import

### Categories (5 items)
- Chăm sóc da
- Trang điểm  
- Chăm sóc tóc
- Chăm sóc cơ thể
- Nước hoa

### Products (10 items)
- Kem chống nắng SPF 50+ Innisfree
- Son môi màu đỏ cam Laneige
- Serum Vitamin C The Ordinary
- Kem dưỡng ẩm Neutrogena
- Phấn nền Fenty Beauty
- Toner cân bằng pH Cosrx
- Mascara làm cong mi Maybelline
- Kem mắt chống lão hóa Olay
- Son dưỡng môi Vaseline
- Kem che khuyết điểm NARS

## ⚠️ Lưu ý

- Scripts này sẽ **XÓA TẤT CẢ DATA CŨ** trước khi import
- Chỉ dùng cho development, KHÔNG chạy trên production
- Đảm bảo MongoDB connection string đúng trong .env

## 🔍 Verify data

### Sử dụng MongoDB Shell

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27018/cosmetic_shop_db

# Check categories
db.categories.find()

# Check products
db.products.find()

# Count documents
db.categories.countDocuments()
db.products.countDocuments()
```

### Sử dụng API

```bash
# Test categories endpoint
curl http://localhost:8080/api/v1/categories

# Test products endpoint
curl http://localhost:8080/api/v1/products
```

## 🐛 Troubleshooting

### Error: "No module named 'app'"

Đảm bảo bạn đang ở root directory và chạy với `-m`:

```bash
cd D:\CNTT\HUIT\NoSQL\Project\Cosmetic-api-store
python -m app.test.seed_all
```

### Error: Connection refused

Kiểm tra MongoDB có đang chạy không:

```bash
docker ps
# hoặc
docker-compose ps
```

### Error: "Motor object has no attribute..."

Kiểm tra các dependencies đã cài đúng phiên bản:

```bash
pip install -r requirements.txt
```

