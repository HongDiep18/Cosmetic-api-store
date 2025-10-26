# Static Images Directory

Thư mục này chứa các tài nguyên ảnh tĩnh được public ra ngoài.

## 📁 Cấu trúc

```
static/
└── images/
    └── products/     # Ảnh sản phẩm
```

## 🔗 Truy cập ảnh

Sau khi upload, ảnh có thể truy cập qua URL:

```
http://localhost:8080/static/images/products/{filename}
```

**Ví dụ:**
```
http://localhost:8080/static/images/products/abc123.jpg
```

## 📤 Upload ảnh

### 1. Upload một ảnh

**Endpoint:** `POST /api/v1/uploads/upload`

**Curl:**
```bash
curl -X POST "http://localhost:8080/api/v1/uploads/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg"
```

**Response:**
```json
{
  "success": true,
  "filename": "abc123-def456.jpg",
  "url": "/static/images/products/abc123-def456.jpg",
  "message": "File uploaded successfully"
}
```

### 2. Upload nhiều ảnh

**Endpoint:** `POST /api/v1/uploads/upload-multiple`

**Curl:**
```bash
curl -X POST "http://localhost:8080/api/v1/uploads/upload-multiple" \
  -F "files=@/path/to/image1.jpg" \
  -F "files=@/path/to/image2.jpg"
```

### 3. Xóa ảnh

**Endpoint:** `DELETE /api/v1/uploads/delete/{filename}`

**Curl:**
```bash
curl -X DELETE "http://localhost:8080/api/v1/uploads/delete/abc123-def456.jpg"
```

## 📝 Quy định

- **Định dạng cho phép:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Kích thước tối đa:** 5MB mỗi file
- **Số lượng tối đa:** 10 files/request (upload multiple)

## 🚀 Sử dụng trong Frontend

```typescript
// Upload ảnh
const uploadImage = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8080/api/v1/uploads/upload', {
    method: 'POST',
    body: formData,
  });
  
  const data = await response.json();
  return data.url; // "/static/images/products/abc123.jpg"
};

// Hiển thị ảnh
<img src={`http://localhost:8080${imageUrl}`} alt="Product" />
```

## 🐳 Docker

Trong Docker, ảnh được lưu trong container tại `/app/static/images/products/`.

Nếu muốn persist data, thêm volume vào `docker-compose.yml`:

```yaml
volumes:
  - ./static:/app/static
```

