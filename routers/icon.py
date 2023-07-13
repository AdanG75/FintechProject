from fastapi import APIRouter
from starlette import status
from starlette.responses import FileResponse

router = APIRouter()
favicon_path = 'favicon.ico'


@router.get(
    path='/favicon.ico',
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    include_in_schema=False
)
async def favicon():
    return FileResponse(favicon_path)