from fastapi import FastAPI

from core.config import BOUND_TEST_ENTRYPOINTS
from routers import credit_router, fingerprint_router, home, market_router, start_router, static, user_router
from routers.test import test_account, test_address, test_admin, test_branch, test_client, test_core, test_credit, \
    test_deposit, test_fingerprint, test_functions, test_login_attempt, test_market, test_minutia, test_movement, \
    test_outstanding_payment, test_password_recovery, test_payment, test_session, test_transfer, test_user, \
    test_withdraw


def add_main_routers(r_app: FastAPI) -> None:
    # Main endpoints
    r_app.include_router(router=credit_router.router)
    r_app.include_router(router=fingerprint_router.router)
    r_app.include_router(router=home.router)
    r_app.include_router(router=market_router.router)
    r_app.include_router(router=start_router.router)
    r_app.include_router(router=static.router)
    r_app.include_router(router=user_router.router)


def add_test_routers(r_app: FastAPI) -> None:
    if BOUND_TEST_ENTRYPOINTS:
        # test endpoints
        r_app.include_router(router=test_account.router)
        r_app.include_router(router=test_address.router)
        r_app.include_router(router=test_admin.router)
        r_app.include_router(router=test_branch.router)
        r_app.include_router(router=test_client.router)
        r_app.include_router(router=test_core.router)
        r_app.include_router(router=test_credit.router)
        r_app.include_router(router=test_deposit.router)
        r_app.include_router(router=test_fingerprint.router)
        r_app.include_router(router=test_functions.router)
        r_app.include_router(router=test_login_attempt.router)
        r_app.include_router(router=test_market.router)
        r_app.include_router(router=test_minutia.router)
        r_app.include_router(router=test_movement.router)
        r_app.include_router(router=test_outstanding_payment.router)
        r_app.include_router(router=test_password_recovery.router)
        r_app.include_router(router=test_payment.router)
        r_app.include_router(router=test_session.router)
        r_app.include_router(router=test_transfer.router)
        r_app.include_router(router=test_user.router)
        r_app.include_router(router=test_withdraw.router)
