import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings
from db.database import SessionLocal
from db.orm.users_orm import get_user_by_id


def get_system_email() -> str:
    """
    Get the system's email
    :return: (str) The system's email
    """
    db = SessionLocal()
    system = get_user_by_id(db, settings.get_id_system())
    db.close()

    return system.email


def gmail_send_message():
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = get_system_credential(refresh_mode=True)

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content('This is automated draft mail')

        message['To'] = 'ansg75@hotmail.com'
        message['From'] = get_system_email()
        message['Subject'] = 'Automated draft 5'

        message.set_content(
            'Hi, this is automated mail without attachment.\n'
            'Please do not reply.'
        )

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'raw': encoded_message
        }

        # pylint: disable=E1101
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


def get_system_credential(refresh_mode: bool = False) -> Credentials:
    if refresh_mode:
        credential = Credentials(
            None,
            refresh_token=settings.get_google_refresh_token(),
            token_uri=settings.get_token_uri(),
            client_id=settings.get_google_client_id(),
            client_secret=settings.get_google_client_secret()
        )
    else:
        credential = Credentials(
            token=settings.get_google_token()
        )

    return credential
