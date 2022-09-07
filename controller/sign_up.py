from typing import Union, Tuple, Optional, List

from sqlalchemy.orm import Session

from core.config import settings
from db.models.users_db import DbUser
from db.orm.accounts_orm import create_account
from db.orm.addresses_orm import create_address
from db.orm.admins_orm import create_admin
from db.orm.branches_orm import create_branch
from db.orm.clients_orm import create_client
from db.orm.credits_orm import create_credit
from db.orm.functions_orm import full_database_exceptions
from db.orm.markets_orm import create_market
from db.orm.outstanding_payments_orm import create_outstanding_payment
from db.orm.users_orm import create_user
from db.orm.exceptions_orm import type_of_value_not_compatible, wrong_data_sent_exception, option_not_found_exception
from core.utils import check_email
from fingerprint_process.utils.error_message import ErrorMessage
from fingerprint_process.utils.utils import get_quality_of_fingerprint, get_description_fingerprint
from schemas.admin_complex import AdminFullRequest, AdminFullDisplay
from schemas.client_complex import ClientFullRequest, ClientFullDisplay
from schemas.credit_base import CreditRequest
from schemas.fingerprint_model import FingerprintSamples
from schemas.market_complex import MarketFullRequest, MarketFullDisplay
from schemas.outstanding_base import OutstandingPaymentRequest
from schemas.system_complex import SystemFullRequest, SystemFullDisplay
from schemas.type_user import TypeUser


@full_database_exceptions
def sign_up_admin(
        db: Session,
        admin: AdminFullRequest
) -> AdminFullDisplay:
    if not isinstance(admin, AdminFullRequest):
        raise type_of_value_not_compatible

    try:
        # Save user
        new_user: DbUser = create_user(db, admin.user, execute='wait')
        nested = db.begin_nested()
        db.refresh(new_user)

        # Save admin
        admin.admin.id_user = new_user.id_user
        new_admin = create_admin(db, admin.admin, execute='wait')
        nested.commit()

        # Save all register
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return AdminFullDisplay(
        user=new_user,
        admin=new_admin
    )


@full_database_exceptions
def sign_up_client(
        db: Session,
        client: ClientFullRequest
) -> ClientFullDisplay:
    if not isinstance(client, ClientFullRequest):
        raise type_of_value_not_compatible

    try:
        # Save user
        new_user = create_user(db, client.user, execute='wait')
        nested = db.begin_nested()
        db.refresh(new_user)

        # Save client
        client.client.id_user = new_user.id_user
        new_client = create_client(db, client.client, execute='wait')
        nested.commit()

        # Save address
        client.address.id_client = new_client.id_client
        new_address = create_address(db, client.address, execute='wait')

        # Create global credit
        global_credit_request = CreditRequest(
            id_client=new_client.id_client,
            id_market=settings.get_market_system(),
            id_account=None,
            alias_credit="Crédito global",
            type_credit="global",
            amount=0
        )
        new_global_credit = create_credit(db, global_credit_request, 'system', execute='wait')

        # Save all objects
        db.commit()
        db.refresh(new_client)
        db.refresh(new_address)
        db.refresh(new_global_credit)
    except Exception as e:
        db.rollback()
        raise e

    return ClientFullDisplay(
        user=new_user,
        client=new_client,
        address=new_address,
        global_credit=new_global_credit
    )


@full_database_exceptions
def sign_up_market(
        db: Session,
        market: MarketFullRequest,
        test_mode: bool = False
) -> MarketFullDisplay:
    if not isinstance(market, MarketFullRequest):
        raise type_of_value_not_compatible

    check_email(market.account.paypal_email, check=not test_mode, mode='exception')

    try:
        # Save user
        new_user = create_user(db, market.user, execute='wait')
        nested = db.begin_nested()
        db.refresh(new_user)

        # Save market
        market.market.id_user = new_user.id_user
        new_market = create_market(db, market.market, execute='wait')

        # Save branch
        market.branch.id_market = new_market.id_market
        new_branch = create_branch(db, market.branch, execute='wait')
        nested.commit()

        # Save address
        market.address.id_branch = new_branch.id_branch
        new_address = create_address(db, market.address, execute='wait')

        # Save account
        market.account.id_user = new_user.id_user
        new_account = create_account(db, market.account, execute='wait')

        # Save outstanding payment
        outstanding_request = OutstandingPaymentRequest(
            id_market=new_market.id_market,
            amount=0
        )
        create_outstanding_payment(db, outstanding_request, execute='wait')

        # Save all register
        db.commit()
        db.refresh(new_address)
        db.refresh(new_account)
    except Exception as e:
        db.rollback()
        raise e

    return MarketFullDisplay(
        user=new_user,
        market=new_market,
        branch=new_branch,
        address=new_address,
        account=new_account
    )


@full_database_exceptions
def sign_up_system(
        db: Session,
        system: SystemFullRequest
) -> SystemFullDisplay:
    if not isinstance(system, SystemFullRequest):
        raise type_of_value_not_compatible

    try:
        # Save user
        new_user = create_user(db, system.user, execute='wait')
        nested = db.begin_nested()
        db.refresh(new_user)

        # Save market
        system.market.id_user = new_user.id_user
        new_market = create_market(db, system.market, execute='wait')
        nested.commit()

        # Save all objects
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return SystemFullDisplay(
        user=new_user,
        market=new_market
    )


def get_user_type(
        data: Union[dict, AdminFullRequest]
) -> TypeUser:
    if isinstance(data, dict):
        type_user = data['user']['type_user']
        try:
            type_user_object = TypeUser(type_user)
            return type_user_object
        except ValueError:
            raise wrong_data_sent_exception
    else:
        try:
            return data.user.type_user
        except AttributeError:
            raise type_of_value_not_compatible


async def route_user_to_sign_up(
        db: Session,
        request: Union[dict, AdminFullRequest, MarketFullRequest],
        type_user: TypeUser,
        test_mode: bool = False
) -> Union[AdminFullDisplay]:
    if type_user.value == 'admin':
        admin_request = AdminFullRequest.parse_obj(request) if isinstance(request, dict) else request
        response = sign_up_admin(db, admin_request)
    elif type_user.value == 'client':
        client_request = ClientFullRequest.parse_obj(request) if isinstance(request, dict) else request
        response = sign_up_client(db, client_request)
    elif type_user.value == 'market':
        market_request = MarketFullRequest.parse_obj(request) if isinstance(request, dict) else request
        response = sign_up_market(db, market_request, test_mode)
    elif type_user.value == 'system':
        system_request = SystemFullRequest.parse_obj(request) if isinstance(request, dict) else request
        response = sign_up_system(db, system_request)
    else:
        raise option_not_found_exception

    return response


@full_database_exceptions
def register_fingerprint(
        db: Session,
        fingerprints: FingerprintSamples,
        id_client: str,
        data_summary: List[dict]
):
    # Unfinished function: missing test and enhance register of fingerprint

    position_best_sample = select_the_best_sample(data_summary)
    best_sample = fingerprints.fingerprints[position_best_sample]
    result = get_description_fingerprint(
        name_fingerprint='example',
        source='api',
        data_fingerprint=best_sample,
        mode='register',
        show_result=False,
        save_result=False
    )

    if isinstance(result, int):
        console = ErrorMessage()
        console.show_message(result, web=True)

    # TODO



async def check_quality_of_fingerprints(
        fingerprints: FingerprintSamples
) -> Tuple[bool, list[dict]]:
    is_there_a_good_sample = False
    fingerprint_summary = []
    try:
        count = 0
        for sample in fingerprints.fingerprints:
            fingerprint_name = 'Fingerprint-' + str(count)
            fingerprint_data = get_quality_of_fingerprint(sample, fingerprint_name, return_data='full')

            if isinstance(fingerprint_data, dict):
                if fingerprint_data['quality'] == 'good':
                    fingerprint_data['pos'] = count
                    fingerprint_summary.append(fingerprint_data)
                    is_there_a_good_sample = True

            count = count + 1

    except Exception as e:
        print(e)
        raise e

    return is_there_a_good_sample, fingerprint_summary


def select_the_best_sample(summary_sample_data: List[dict]) -> Optional[int]:
    """
    Return the index where the best sample of fingerprint is. If the list are void the function will return None.

    :param summary_sample_data: (list) A list which contains one or more dictionaries with these keys:
        - **quality**: Could be 'good' or 'bad'
        - **pos**: Place into the list where are saved the sample
        - **indexes**: Contain the indexes 'spatial_index' and 'spectral_index' within a dict

    :return: (int, None) The position where the best sample is. If the list is empty or there are not a good quality
    sample, the function will return void.
    """
    if len(summary_sample_data) < 1:
        return None

    item = -1
    list_pos = -1
    flag_firsts_item = False
    for pos, sample in enumerate(summary_sample_data):
        if sample['quality'] == 'good':
            if not flag_firsts_item:
                item = sample['pos']
                list_pos = pos
                flag_firsts_item = True
            else:
                if sample['indexes']['spectral_index'] > summary_sample_data[list_pos]['indexes']['spectral_index']:
                    item = sample['pos']
                    list_pos = pos
                elif sample['indexes']['spectral_index'] == summary_sample_data[list_pos]['indexes']['spectral_index']:
                    if sample['indexes']['spatial_index'] > summary_sample_data[list_pos]['indexes']['spatial_index']:
                        item = sample['pos']
                        list_pos = pos
                    else:
                        pass
                else:
                    pass

    if not flag_firsts_item:
        return None
    else:
        return item


