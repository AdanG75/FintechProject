from typing import List

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.orm import branches_orm
from schemas.basic_response import BasicResponse, BasicPasswordChange
from schemas.branch_base import BranchDisplay, BranchRequest

router = APIRouter(
    prefix='/test/branch',
    tags=['tests', 'branch']
)


@router.post(
    path='/',
    response_model=BranchDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_branch(
        request: BranchRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = branches_orm.create_branch(db, request)

    return response


@router.get(
    path='/{id_branch}',
    response_model=BranchDisplay,
    status_code=status.HTTP_200_OK
)
async def get_branch(
        id_branch: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = branches_orm.get_branch_by_id(db, id_branch)

    return response


@router.get(
    path='/market/{id_market}',
    response_model=List[BranchDisplay],
    status_code=status.HTTP_200_OK
)
async def get_branches_by_id_market(
        id_market: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = branches_orm.get_branches_by_id_market(db, id_market)

    return response


@router.get(
    path='/name/{branch_name}',
    response_model=List[BranchDisplay],
    status_code=status.HTTP_200_OK
)
async def get_branches_by_name(
        branch_name: str = Path(..., min_length=1, max_length=49),
        db: Session = Depends(get_db)
):
    response = branches_orm.get_branches_by_branch_name(db, branch_name)

    return response


@router.put(
    path='/{id_branch}',
    response_model=BranchDisplay,
    status_code=status.HTTP_200_OK
)
async def update_branch(
        id_branch: str = Path(..., min_length=12, max_length=49),
        request: BranchRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = branches_orm.update_branch(db, request, id_branch)

    return response


@router.patch(
    path='/new-password/{id_branch}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def update_password_of_branch(
        id_branch: str = Path(..., min_length=12, max_length=49),
        request: BasicPasswordChange = Body(...),
        db: Session = Depends(get_db)
):
    response = branches_orm.set_new_password(db, id_branch, request.password)

    return response


@router.delete(
    path='/{id_branch}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_branch(
        id_branch: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = branches_orm.delete_branch(db, id_branch)

    return response


@router.delete(
    path='/market/{id_market}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_branches_of_market(
        id_market: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = branches_orm.delete_branches_by_id_market(db, id_market)

    return response
