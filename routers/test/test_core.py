from typing import List

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.orm import cores_orm
from db.orm.exceptions_orm import wrong_data_sent_exception
from fingerprint_process.models.core_point import CorePoint
from schemas.basic_response import BasicResponse
from schemas.core_base import CoreDisplay, CoreRequest

router = APIRouter(
    prefix='/test/core',
    tags=['tests', 'core point']
)


@router.post(
    path='/',
    response_model=BasicResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_core_point(
        request: CoreRequest = Body(...),
        db: Session = Depends(get_db)
):
    new_core = CorePoint(
        posy=request.pos_y,
        posx=request.pos_x,
        angle=request.angle,
        point_type=request.type_core.value
    )

    result = cores_orm.create_core_point(db, new_core, request.id_fingerprint)

    return BasicResponse(
        operation="Create",
        successful=result
    )


@router.get(
    path='/{id_core}',
    response_model=CoreDisplay,
    status_code=status.HTTP_200_OK
)
async def get_core_point(
        id_core: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = cores_orm.get_core_point_by_id(db, id_core)

    return response


@router.delete(
    path='/{id_core}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_core_point(
        id_core: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = cores_orm.delete_core_point(db=db, id_core=id_core)

    return response


@router.post(
    path='/fingerprint/{id_fingerprint}',
    response_model=BasicResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_all_core_points_of_a_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=40),
        request: List[CoreRequest] = Body(...),
        db: Session = Depends(get_db)
):
    id_fingerprint_of_request = request[0].id_fingerprint
    new_cores: List[CorePoint] = []

    for element in request:
        if id_fingerprint_of_request != element.id_fingerprint:
            raise wrong_data_sent_exception
        else:
            new_core = CorePoint(
                posy=element.pos_y,
                posx=element.pos_x,
                angle=element.angle,
                point_type=element.type_core.value
            )
            new_cores.append(new_core)

    if id_fingerprint_of_request != id_fingerprint:
        raise wrong_data_sent_exception

    result = cores_orm.insert_list_of_core_points(db, new_cores, id_fingerprint)

    return BasicResponse(
        operation="Create",
        successful=result
    )


@router.get(
    path='/id_fingerprint/{id_fingerprint}',
    response_model=List[CoreDisplay],
    status_code=status.HTTP_200_OK
)
async def get_core_points_of_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = cores_orm.get_core_points_by_id_fingerprint(db, id_fingerprint)

    return response


@router.delete(
    path='/id_fingerprint/{id_fingerprint}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_core_points_of_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = cores_orm.delete_all_core_points_of_fingerprint(db, id_fingerprint)

    return response
