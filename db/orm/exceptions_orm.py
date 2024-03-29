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

cache_exception = DBException(
    msg="Couldn't connect to Cache",
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

unexpected_error_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="An unexpected error occurred while precessing the request"
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


type_of_authorization_not_compatible_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="The type of authorization requested not is valid to this transaction"
)


type_of_user_not_compatible = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Unsupportable user type. It is not compatible with the operation"
)

type_of_movement_not_compatible_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Type of movement it is not supported by this type of transaction"
)

validation_request_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Error to validate data. Please check the allowed schemas in this entry point"
)

not_authorized_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="You do not have authorization to enter to this entry point"
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

error_while_generating_code_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="An error occurred while code was being generated"
)

error_while_checking_code_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="An error occurred while code was being checked"
)

existing_credit_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Client already has a credit within the market"
)

not_void_credit_exception = HTTPException(
    status_code=status.HTTP_412_PRECONDITION_FAILED,
    detail="Credits with credit balance cannot be eliminated by the market"
)

not_sufficient_funds_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail='Insufficient funds'
)

movement_in_process_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Movement in process, please wait until it has finished"
)

movement_finish_exception = HTTPException(
    status_code=status.HTTP_423_LOCKED,
    detail="The movement process have been finished"
)

movement_already_authorized_exception = HTTPException(
    status_code=status.HTTP_423_LOCKED,
    detail="Movement has already authorized by this method"
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

system_credit_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Only the system can own global credits"
)

circular_transaction_exception = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Circular transactions are not allowed"
)

compile_exception = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="A compile error occurred during execution of the process"
)

operation_need_a_precondition_exception = HTTPException(
    status_code=status.HTTP_412_PRECONDITION_FAILED,
    detail="To do this operation it is necessary have completed some conditions"
)

operation_need_authorization_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='This operation needs a previous authorization'
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
    status_code=status.HTTP_418_IM_A_TEAPOT,
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

email_or_password_are_wrong_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Username or password are wrong"
)

too_early_exception = HTTPException(
    status_code=status.HTTP_425_TOO_EARLY,
    detail="Please, try again later"
)

expired_session_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Session has been finished"
)

expired_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired"
)

expired_ticket_or_is_incorrect_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Ticket is wrong or it has expired"
)

wrong_code_exception = HTTPException(
    status_code=status.HTTP_406_NOT_ACCEPTABLE,
    detail="Code do not match with the code sent"
)

expired_cache_exception = HTTPException(
    status_code=status.HTTP_408_REQUEST_TIMEOUT,
    detail="Cache has expired. Please try again from begin."
)

bad_cipher_data_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="Ensure that the data sent is ciphered by our public key"
)

required_public_pem_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="It is necessary send your public pem to receive a secure response"
)

wrong_public_pem_format_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail="PEM format are wrong, please sent it based on PKCS8"
)

only_available_client_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="This operation is only available to clients"
)

only_available_market_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="This operation is only available to markets"
)

not_longer_available_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Operation expired. Please generate a new one"
)

not_same_currency_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Currency must be the same for all purchase items."
)

first_approve_order_exception = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="You need to approve the order using the approve link within the create order response"
)

paypal_error_exception = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="PayPal is not available in this moment. Please try later."
)

minimum_amount_exception = HTTPException(
    status_code=status.HTTP_418_IM_A_TEAPOT,
    detail='Minimum transaction amount must be reached'
)

not_implemented_exception = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail="Operation has not yet implemented"
)
