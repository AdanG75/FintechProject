import base64
import io
import json
from typing import List

from fastapi import HTTPException
from starlette import status

from PIL import Image

from fingerprint_process.utils.utils import raw_fingerprint_construction


def save_fingerprint_in_memory(
        data_fingerprint: List,
        return_format: str = 'base64'
) -> bytes:
    """
    Save fingerprint into memory as bytes
    :param data_fingerprint: (List[int]) - Data of a fingerprint sample
    :param return_format: (str) -   "base64" -> return the image in base64 encode
                                    "bytes" -> return the image in raw bytes (without encode)
    :return: Data image in bytes
    """
    raw_fingerprint = raw_fingerprint_construction(data_fingerprint=data_fingerprint)

    if isinstance(raw_fingerprint, tuple):
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail=f"Fingerprint could not be created"
        )

    fingerprint_image = Image.fromarray(raw_fingerprint)
    fingerprint_image = fingerprint_image.convert("L")
    buffer = io.BytesIO()
    fingerprint_image.save(buffer, format="BMP")
    fingerprint_image_bytes = buffer.getvalue()

    if return_format == 'base64':
        image_b64: bytes = base64.b64encode(fingerprint_image_bytes)

    fingerprint_image.close()
    buffer.close()

    if return_format == 'base64':
        return image_b64
    elif return_format == 'bytes':
        return fingerprint_image_bytes
    else:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="Format type not available"
        )


def open_fingerprint_data_from_json(
        path: str = './fingerprint_process/data/',
        json_name: str = 'fingerprintRawData.json'
) -> List[int]:

    if not json_name.endswith(".json"):
        json_name = json_name + ".json"

    global fingerprint_data_str

    with open(
        file=path + json_name,
        mode='r',
        encoding='utf-8'
    ) as file:
        fingerprint_json = json.load(file)
        fingerprint_data_str = fingerprint_json["fingerprint"]
        file.close()

    data_fingerprint = []

    for data in fingerprint_data_str:
        data_fingerprint.append(int(data))

    return data_fingerprint



