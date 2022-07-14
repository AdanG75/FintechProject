from fastapi import HTTPException
from starlette import status


class DBException(Exception):
    def __init__(self, msg, code):
        self.message = msg
        self.code = code
        super().__init__(self.message)


db_exception = DBException(
    msg="Couldn't connect to the Database",
    code=status.HTTP_503_SERVICE_UNAVAILABLE
)


class NotFoundException(Exception):
    def __init__(self, msg, code):
        self.message = msg
        self.code = code
        super().__init__(self.message)


element_not_found_exception = NotFoundException(
    code=status.HTTP_404_NOT_FOUND,
    msg=f"Element not found"
)

# HTTPExceptions
credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Couldn't validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

email_exception = HTTPException(
    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    detail="Email is too large, maximum length: 79 characters or it is null"
)

phone_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Phone number not valid"
)

not_unique_email_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Email not available, please write another one"
)


not_unique_username_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Username not available, please write another one"
)

not_unique_branch_name_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Branch name not available, please write another one"
)

not_unique_email_or_username_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Email or Username not available, please write another one"
)

not_unique_alias_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Alias of element would be unique"
)

not_unique_value = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Relation between entities is not one to one"
)

not_main_element_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="At least one element should be the main element"
)

type_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Type not found"
)

option_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Option not found"
)

not_values_sent_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="One or more values have not been passed"
)

too_many_attempts_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Actual operation is expired. Please generate other one."
)

not_valid_operation_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Operation is not longer available"
)

inactive_password_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Current password was disabled, please generate a new one"
)

existing_credit_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Client already has a credit within the market"
)

