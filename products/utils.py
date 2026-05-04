import cloudinary
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

def upload_image_to_cloudinary(image_data, folder="dates_nuts/products"):
    """
    Uploads an image to Cloudinary.
    image_data can be a Base64 string, a file-like object, or a URL.
    Returns the secure URL of the uploaded image.
    """
    if not image_data:
        return None
    
    # If it's already a Cloudinary URL, just return it
    if isinstance(image_data, str) and 'res.cloudinary.com' in image_data:
        return image_data
        
    try:
        # If it's a data URL (Base64), Cloudinary handles it natively
        upload_result = cloudinary.uploader.upload(
            image_data,
            folder=folder,
            resource_type="auto"
        )
        return upload_result.get('secure_url')
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        # If it's a standard URL that failed to upload, fallback to the original URL if possible
        if isinstance(image_data, str) and image_data.startswith('http'):
            return image_data
        return None
