import base64
import io
import json
from typing import List, Union

from numpy import ndarray

from PIL import Image

from db.orm.exceptions_orm import not_values_sent_exception, option_not_found_exception, uncreated_fingerprint_exception
from fingerprint_process.utils.utils import raw_fingerprint_construction


def save_fingerprint_in_memory(
        data_fingerprint: Union[str, List, None] = None,
        image_fingerprint: Union[ndarray, list, None] = None,
        return_format: str = 'base64'
) -> bytes:
    """
    Save fingerprint into memory as bytes. If 'data_fingerprint' and 'image_fingerprint' are passed
    the function will take image_fingerprint to be saved.

    :param data_fingerprint: (Union[str, List[int])) - Data of a fingerprint sample
    :param image_fingerprint: (ndarray, list) - Image of the fingerprint
    :param return_format: (str) -   "base64" -> return the image in base64 encode
                                    "bytes" -> return the image in raw bytes (without encode)
    :return: Data image in bytes
    """
    if image_fingerprint is None and data_fingerprint is None:
        raise not_values_sent_exception

    if data_fingerprint is not None and image_fingerprint is None:
        image_fingerprint = raw_fingerprint_construction(data_fingerprint=data_fingerprint)

    if isinstance(image_fingerprint, tuple):
        raise uncreated_fingerprint_exception

    fingerprint_image = Image.fromarray(image_fingerprint)
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
        raise option_not_found_exception


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
