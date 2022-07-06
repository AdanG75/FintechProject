from fastapi import HTTPException
from starlette import status


db_exception = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Couldn't connect to the Database"
)

element_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Element not found"
)

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

not_main_element_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="At least one element should be the main element"
)

type_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Type not found"
)

not_values_sent_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Values have not been passed"
)