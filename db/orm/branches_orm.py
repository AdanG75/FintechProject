from typing import List
import uuid

from sqlalchemy.orm import Session

from core.utils import is_valid_phone_number, set_phone_number_format
from db.models.branches_db import DbBranch
from db.orm.exceptions_orm import db_exception, element_not_found_exception, \
    not_unique_branch_name_exception, phone_exception, option_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.branch_base import BranchRequest
from secure.hash import Hash


@multiple_attempts
def create_branch(db: Session, request: BranchRequest) -> DbBranch:
    if request.phone is not None:
        formatted_phone = set_phone_number_format(request.phone)
        if not is_valid_phone_number(request.phone):
            raise phone_exception
    else:
        formatted_phone = request.phone

    try:
        branch = get_branch_by_id_market_and_branch_name(db, request.id_market, request.branch_name, mode='all')
    except element_not_found_exception:
        branch_uuid = uuid.uuid4().hex
        id_branch = f"BRH-{branch_uuid}"

        new_branch = DbBranch(
            id_branch=id_branch,
            id_market=request.id_market,
            branch_name=request.branch_name,
            service_hours=request.service_hours,
            phone=formatted_phone,
            password=Hash.bcrypt(request.password)
        )

        try:
            db.add(new_branch)
            db.commit()
            db.refresh(new_branch)
        except Exception as e:
            db.rollback()
            raise db_exception

        return new_branch

    if branch.dropped:
        return update_branch(db, request, branch.id_branch)

    raise not_unique_branch_name_exception


def get_branch_by_id(db: Session, id_branch: str) -> DbBranch:
    try:
        branch = db.query(DbBranch).where(
            DbBranch.id_branch == id_branch,
            DbBranch.dropped == False
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if branch is None:
        raise element_not_found_exception

    return branch


def get_branches_by_id_market(db: Session, id_market: str) -> List[DbBranch]:
    try:
        branches = db.query(DbBranch).where(
            DbBranch.id_market == id_market,
            DbBranch.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    if branches is None or len(branches) < 1:
        raise element_not_found_exception

    return branches


def get_branches_by_branch_name(db: Session, branch_name: str) -> List[DbBranch]:
    try:
        branches = db.query(DbBranch).where(
            DbBranch.branch_name == branch_name,
            DbBranch.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    if branches is None or len(branches) < 1:
        raise element_not_found_exception

    return branches


def get_branch_by_id_market_and_branch_name(
        db: Session,
        id_market: str,
        branch_name: str,
        mode: str = 'active'
) -> DbBranch:
    try:
        if mode == 'active':
            branch = db.query(DbBranch).where(
                DbBranch.id_market == id_market,
                DbBranch.branch_name == branch_name,
                DbBranch.dropped == False
            ).one_or_none()
        elif mode == 'all':
            branch = db.query(DbBranch).where(
                DbBranch.id_market == id_market,
                DbBranch.branch_name == branch_name
            ).first()
        else:
            raise option_not_found_exception

    except Exception as e:
        raise db_exception

    if branch is None:
        raise element_not_found_exception

    return branch


@multiple_attempts
def update_branch(db: Session, request: BranchRequest, id_branch: str) -> DbBranch:
    updated_branch = get_branch_by_id(db, id_branch)

    if updated_branch.branch_name != request.branch_name:
        try:
            get_branch_by_id_market_and_branch_name(db, request.id_market, request.branch_name)
        except element_not_found_exception:
            updated_branch.branch_name = request.branch_name
        else:
            raise not_unique_branch_name_exception

    if request.phone is not None:
        formatted_phone = set_phone_number_format(request.phone)
        if not is_valid_phone_number(request.phone):
            raise phone_exception
    else:
        formatted_phone = request.phone

    updated_branch.service_hours = request.service_hours
    updated_branch.phone = formatted_phone
    updated_branch.password = Hash.bcrypt(request.password)
    updated_branch.dropped = False

    try:
        db.commit()
        db.refresh(updated_branch)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_branch


@multiple_attempts
def delete_branch(db: Session, id_branch: str) -> BasicResponse:
    branch = get_branch_by_id(db, id_branch)

    branch.dropped = True

    try:
        db.commit()
        db.refresh(branch)
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
def delete_branches_by_id_market(db: Session, id_market: str) -> BasicResponse:
    branches = get_branches_by_id_market(db, id_market)

    for branch in branches:
        branch.dropped = True

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="batch delete",
        successful=True
    )

