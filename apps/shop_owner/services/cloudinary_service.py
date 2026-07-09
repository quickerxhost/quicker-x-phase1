import cloudinary.uploader

from apps.core.exceptions import ApplicationError


def upload_to_cloudinary(file_obj, folder: str, resource_type: str = "auto") -> dict:
    """
    Uploads a file to Cloudinary and returns only the metadata fields
    that should be persisted in Postgres. The binary itself is never
    stored in our database — only Cloudinary's reference metadata.
    """
    try:
        result = cloudinary.uploader.upload(
            file_obj,
            folder=folder,
            resource_type=resource_type,
            overwrite=False,
            unique_filename=True,
        )
    except Exception as exc:  # cloudinary raises generic Error
        raise ApplicationError(
            "File upload failed. Please try again.", errors={"detail": str(exc)}, status_code=502
        )

    return {
        "public_id": result.get("public_id"),
        "secure_url": result.get("secure_url"),
        "resource_type": result.get("resource_type", "image"),
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
        "folder": result.get("folder", folder),
        "version": str(result.get("version", "")),
        "format": result.get("format", ""),
    }


def delete_from_cloudinary(public_id: str, resource_type: str = "image"):
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception as exc:
        raise ApplicationError(
            "Failed to delete file from storage.", errors={"detail": str(exc)}, status_code=502
        )
