from pathlib import Path
import uuid
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import shutil

router = APIRouter()

# Define upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "static" / "images" / "products"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.post("/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...)) -> dict:
    """
    Upload a single product image
    
    Returns:
        dict: Contains the URL path to access the uploaded image
    """
    try:
        # Validate file
        validate_image(file)
        
        # Generate unique filename
        file_ext = Path(file.filename or "").suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL path
        image_url = f"/static/images/products/{unique_filename}"
        
        return {
            "success": True,
            "filename": unique_filename,
            "url": image_url,
            "message": "File uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        file.file.close()


@router.post("/upload-multiple", response_model=dict)
async def upload_multiple_images(files: List[UploadFile] = File(...)) -> dict:
    """
    Upload multiple product images
    
    Returns:
        dict: Contains list of URL paths to access the uploaded images
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            # Validate file
            validate_image(file)
            
            # Generate unique filename
            file_ext = Path(file.filename or "").suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Save file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Add to success list
            image_url = f"/static/images/products/{unique_filename}"
            uploaded_files.append({
                "filename": unique_filename,
                "url": image_url,
                "original_name": file.filename
            })
        
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
        finally:
            file.file.close()
    
    return {
        "success": len(errors) == 0,
        "uploaded": len(uploaded_files),
        "files": uploaded_files,
        "errors": errors
    }


@router.delete("/delete/{filename}")
async def delete_image(filename: str) -> dict:
    """
    Delete a product image
    
    Args:
        filename: The name of the file to delete
    
    Returns:
        dict: Success message
    """
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check: ensure file is within upload directory
        if not str(file_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_path.unlink()
        
        return {
            "success": True,
            "message": f"File {filename} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

