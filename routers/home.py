from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status


router = APIRouter(
    tags=['main']
)

templates = Jinja2Templates(directory="templates")


@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
)
async def home(
        request: Request
):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@router.get(
    path='/privacy',
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def privacy_policy(
        request: Request
):
    return templates.TemplateResponse(
        "privacy_policy.html",
        {"request": request}
    )


@router.get(
    path='/terms-of-service',
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def terms_of_service(
        request: Request
):
    return templates.TemplateResponse(
        "terms_of_service.html",
        {"request": request}
    )

