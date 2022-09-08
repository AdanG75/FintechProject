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

multiple_elements_found_exception = NotFoundException(
    code=status.HTTP_409_CONFLICT,
    msg=f"Multiples elements ware found. Only one was expected"
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

bad_email_exception = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Value is not a valid email address"
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

minimum_object_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="At least one element should be exist"
)

type_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Type not found"
)

type_of_value_not_compatible = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Unsupportable data type or not compatible with the operation"
)

option_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Option not found"
)

not_values_sent_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="One or more values have not been passed or are wrong"
)

wrong_data_sent_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Some data values are incorrect or not was sent"
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

not_void_credit_exception = HTTPException(
    status_code=status.HTTP_412_PRECONDITION_FAILED,
    detail="Credits with credit balance cannot be eliminated by the market"
)

movement_in_process_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Movement in process, please wait until it has finished"
)

movement_finish_exception = HTTPException(
    status_code=status.HTTP_423_LOCKED,
    detail="The movement process have been finished"
)

movement_not_authorized_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Movement must first be authorized"
)

account_does_not_belong_to_market_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="The account must be owned by the market providing the credit"
)

not_credit_of_client_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Credit does not belong to the client"
)

global_credit_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Only system can create global credits"
)

compile_exception = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="A compile error occurred during execution of the process"
)

operation_need_a_precondition_exception = HTTPException(
    status_code=status.HTTP_412_PRECONDITION_FAILED,
    detail="To do this operation it is necessary have completed some conditions"
)

not_identified_client_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="A client is required to make this movement"
)

movement_already_linked_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="The movement has already been linked"
)

bad_quality_fingerprint_exception = HTTPException(
    status_code=status.HTTP_406_NOT_ACCEPTABLE,
    detail="All fingerprint samples are of low quality. Please capture new samples"
)

uncreated_fingerprint_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail=f"Fingerprint could not be created"
)

uncreated_bucked_exception = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="System couldn't create bucket"
)
