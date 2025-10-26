"""
Script to download placeholder images for products
Run: python -m app.test.download_placeholder_images
"""
import os
from pathlib import Path
import urllib.request

# Image URLs mapping (using placeholder service)
IMAGES = {
    "innisfree-sunscreen.jpg": "https://via.placeholder.com/400x400/87CEEB/000000?text=Innisfree+Sunscreen",
    "laneige-lipstick.jpg": "https://via.placeholder.com/400x400/FF69B4/FFFFFF?text=Laneige+Lipstick",
    "ordinary-serum.jpg": "https://via.placeholder.com/400x400/F0E68C/000000?text=The+Ordinary+Serum",
    "neutrogena-moisturizer.jpg": "https://via.placeholder.com/400x400/ADD8E6/000000?text=Neutrogena+Cream",
    "fenty-foundation.jpg": "https://via.placeholder.com/400x400/DDA0DD/000000?text=Fenty+Foundation",
    "cosrx-toner.jpg": "https://via.placeholder.com/400x400/98FB98/000000?text=Cosrx+Toner",
    "maybelline-mascara.jpg": "https://via.placeholder.com/400x400/FFB6C1/000000?text=Maybelline+Mascara",
    "olay-eye-cream.jpg": "https://via.placeholder.com/400x400/F5DEB3/000000?text=Olay+Eye+Cream",
    "vaseline-lip-balm.jpg": "https://via.placeholder.com/400x400/FFC0CB/000000?text=Vaseline+Lip+Balm",
    "nars-concealer.jpg": "https://via.placeholder.com/400x400/FFE4B5/000000?text=NARS+Concealer",
}

# Target directory
STATIC_DIR = Path(__file__).parent.parent.parent / "static" / "images" / "products"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def download_images():
    """Download placeholder images"""
    print("=" * 60)
    print("📥 DOWNLOADING PLACEHOLDER IMAGES")
    print("=" * 60)
    print()
    
    for filename, url in IMAGES.items():
        file_path = STATIC_DIR / filename
        
        # Skip if file already exists
        if file_path.exists():
            print(f"⏭️  Skipped: {filename} (already exists)")
            continue
        
        try:
            print(f"⬇️  Downloading: {filename}...")
            urllib.request.urlretrieve(url, file_path)
            print(f"✅ Downloaded: {filename}")
        except Exception as e:
            print(f"❌ Failed: {filename} - {e}")
    
    print()
    print("=" * 60)
    print("✨ DOWNLOAD COMPLETE!")
    print("=" * 60)
    print()
    print(f"📁 Images saved to: {STATIC_DIR}")
    print(f"🌐 Access via: http://localhost:8080/static/images/products/")
    print()


if __name__ == "__main__":
    download_images()

