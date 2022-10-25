import base64
from email.message import EmailMessage
from typing import Optional, Union

from fastapi import HTTPException
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from starlette import status

from core.config import settings
from core.logs import write_data_log
from db.database import SessionLocal
from db.orm.users_orm import get_user_by_id


def full_email_exception(func):
    def wrapper(*args, **kwargs):
        try:
            func_result = func(*args, **kwargs)
        except RefreshError as e:
            if settings.is_on_cloud():
                write_data_log(e.__str__(), "ERROR")
            else:
                print(f'Refresh error detected. Detail: {e}')

            raise HTTPException(
                status_code=status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED,
                detail=f'Google credentials are wrong. More details about the error: {e}'
            )
        except HttpError as e:
            if settings.is_on_cloud():
                write_data_log(e.__str__(), "ERROR")
            else:
                print(f'We could not connect with the API. Details: {e}')

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'We could not connect with the email API or some values'
                       f'are wrong. More details: {e}'
            )
        except Exception as e:
            if settings.is_on_cloud():
                write_data_log(e.__str__(), "ERROR")
            else:
                print(f'An unexpected error occurs. Detail: {e}')

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'An unexpected error occurs. Details: {e}'
            )

        return func_result

    return wrapper


def get_system_email() -> str:
    """
    Get the system's email
    :return: (str) The system's email
    """
    db = SessionLocal()
    system = get_user_by_id(db, settings.get_id_system())
    db.close()

    return system.email


@full_email_exception
def gmail_send_message(consignee: str, sender: str, subject: str, content: str):
    """
    Create and send an email message
    :param consignee: (str) The consignee's email
    :param sender (str) The sender's email
    :param subject: (str) The reason of the email
    :param content: (str) The body of the email.
    :return: A dict with the send email information when shipment is successful. In other case, return None.

    Load pre-authorized user credentials from the environment.
    See https://developers.google.com/identity for guides on implementing OAuth2 for the application.
    """
    creds = get_system_credential(refresh_mode=True)

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message['To'] = consignee
        message['From'] = sender
        message['Subject'] = subject
        message.set_content(content)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'raw': encoded_message
        }

        # pylint: disable=E1101
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        # print(F'Message Id: {send_message["id"]}')

    except HttpError as error:
        raise error

    return send_message


def send_email_from_system(consignee: str, subject: str, content: str) -> Optional[dict]:
    """
    Send email from system's email
    :param consignee: (str) The consignee's email
    :param subject: (str) The reason of the email
    :param content: (str) The body of the email.
    :return: A dict with the send email information when shipment is successful. In other case, return None.
    """
    sender = get_system_email()
    email_message = gmail_send_message(consignee, sender, subject, content)

    return email_message


@full_email_exception
def get_system_credential(refresh_mode: bool = False) -> Credentials:
    try:
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
    except RefreshError as e:
        print(e)
        raise e

    return credential


async def send_register_email(email_user: str, id_user: int, name_user: str) -> dict:
    register_message = f'''
    Un gusto saludarle {name_user}.
    
    Su registro fué exitoso con id: {id_user}.
    
    Gracias por formar parte de fintech75.
    
    Saludos.
    '''

    register_subject = 'Registro exitoso'

    message_send = send_email_from_system(email_user, register_subject, register_message)

    return message_send


async def send_movement_email(
        email_user: str,
        user_name: str,
        type_movement: str,
        amount: Union[str, float],
        successful: bool
) -> dict:
    if type_movement == 'payment':
        movement = 'un pago'
    elif type_movement == 'deposit':
        movement = 'un depósito'
    elif type_movement == 'transfer':
        movement = 'una transferencia'
    elif type_movement == 'withdraw':
        movement = 'un retiro'
    else:
        movement = 'un movimiento'

    if successful:
        status_movement = 'Se realizó'
    else:
        status_movement = 'Se rechazó'

    movement_message = f'''
    Saludos {user_name}.
    
    {status_movement} {movement} por un monto de {amount}.
    
    Agradecemos su preferencia.
    '''

    movement_subject = 'Nuevo movimiento en fintech75'

    message_send = send_email_from_system(email_user, movement_subject, movement_message)

    return message_send


async def send_recovery_code(
        email_user: str,
        code: str
) -> dict:
    message = f'''
    Un gusto saludarle de nuevo.
    
        Este es su código para recuperar su contraseña: {code}.
    
    Si no fue usted quien solicitó esta operación, le recomendamos que cancele la operación o en su defecto que proteja
    su cuenta de correo electrónico {email_user} para que no puedan hacer uso de este código.
    
    Sin más que agregar el equipo de fintech75 le desea un excelente día.

    '''

    message_subject = "Cambio de contraseña"

    message_send = send_email_from_system(email_user, message_subject, message)

    return message_send

