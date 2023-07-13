# Import the Secret Manager client library.
from fastapi import HTTPException
from google.cloud import secretmanager
import google_crc32c
from starlette import status


def access_secret_version(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").

    :param project_id: (str) - The project's name where secret are saved
    :param secret_id: (str) - The secret's name
    :param version_id: (str) - The secret's version, by default the function get the latest version of the secret.

    :return: (str) - The payload of the secret.
    """

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    # Verify payload checksum.
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)

    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data corruption detected."
        )

    # Get the secret payload.
    payload = response.payload.data.decode("UTF-8")

    return payload
