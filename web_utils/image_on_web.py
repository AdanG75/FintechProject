import base64
import io
from typing import List

from fastapi import HTTPException
from starlette import status

from PIL import Image

from fingerprint_process.utils.utils import raw_fingerprint_construction


def save_fingerprint_in_memory(data_fingerprint: List) -> bytes:
    raw_fingerprint = raw_fingerprint_construction(data_fingerprint=data_fingerprint)

    if isinstance(raw_fingerprint, tuple):
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail=f"Fingerprint could not be created"
        )

    fingerprint_image = Image.fromarray(raw_fingerprint)
    buffer = io.BytesIO()
    fingerprint_image.save(buffer, format="BMP")
    fingerprint_image_bytes = buffer.getvalue()
    image_b64: bytes = base64.b64encode(fingerprint_image_bytes)

    fingerprint_image.close()
    buffer.close()

    return image_b64




