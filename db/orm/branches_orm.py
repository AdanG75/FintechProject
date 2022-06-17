from typing import List
import uuid

from sqlalchemy.orm import Session

from core.utils import is_valid_phone_number
from db.models.branches_db import DbBranch
from db.orm.exceptions_orm import db_exception, element_not_found_exception, \
    not_unique_branch_name_exception, phone_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.branch_base import BranchRequest, BranchUpdateRequest
from secure.hash import Hash


@multiple_attempts
def create_branch(db: Session, request: BranchRequest, id_market: str, id_address: int) -> DbBranch:
    branch_uuid = uuid.uuid4().hex
    id_branch = f"BRH-{branch_uuid}"

    if not is_valid_phone_number(request.phone):
        raise phone_exception

    try:
        branch = get_branch_by_id_market_and_branch_name(db, id_market, request.branch_name)
    except element_not_found_exception:
        new_branch = DbBranch(
            id_branch=id_branch,
            id_market=id_market,
            id_address=id_address,
            branch_name=request.branch_name,
            service_hours=request.service_hours,
            phone=request.phone,
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


def get_branches_by_id_address(db:Session, id_address: int) -> List[DbBranch]:
    try:
        branches = db.query(DbBranch).where(
            DbBranch.id_address == id_address,
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


def get_branch_by_id_market_and_branch_name(db: Session, id_market: str, branch_name: str) -> DbBranch:
    branch = db.query(DbBranch).where(
        DbBranch.id_market == id_market,
        DbBranch.branch_name == branch_name,
        DbBranch.dropped == False
    ).one_or_none()

    if branch is None:
        raise element_not_found_exception

    return branch


@multiple_attempts
def update_branch(db: Session, request: BranchUpdateRequest, id_branch: str) -> DbBranch:
    updated_branch = get_branch_by_id(db, id_branch)

    if updated_branch.branch_name != request.branch_name:
        try:
            get_branch_by_id_market_and_branch_name(db, request.id_market, request.branch_name)
        except element_not_found_exception:
            updated_branch.branch_name = request.branch_name
        else:
            raise not_unique_branch_name_exception

    updated_branch.id_address = request.id_address
    updated_branch.service_hours = request.service_hours
    updated_branch.password = Hash.bcrypt(request.password)

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

