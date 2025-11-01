import os
import uuid
from pathlib import Path
from fastapi import UploadFile


async def save_upload_file(
    file: UploadFile, base_url: str = "http://localhost:8000"
) -> str:
    # Create uploads directory if it doesn't exist
    upload_dir = Path("public/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename with safe characters
    original_name = file.filename or "unnamed"
    file_extension = os.path.splitext(original_name)[1].lower()
    if not file_extension:
        content_type = file.content_type or "image/jpeg"
        if "png" in content_type:
            file_extension = ".png"
        elif "gif" in content_type:
            file_extension = ".gif"
        else:
            file_extension = ".jpg"

    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Save file
    file_path = upload_dir / unique_filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Return full URL for the image
    return f"{base_url}/uploads/{unique_filename}"
