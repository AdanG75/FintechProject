from fastapi import APIRouter, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from schemas.fingerprint_model import FingerprintSimpleModel
from web_utils.image_on_web import save_fingerprint_in_memory


templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/test/functions',
    tags=["test"]
)

@router.get(
    path="/fingerprint/image",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def get_fingerprint_image(
        request: Request,
        fingerprint_model: FingerprintSimpleModel = Body(...)
):
    fingerprint = save_fingerprint_in_memory(fingerprint_model.fingerprint)

    return templates.TemplateResponse("raw_fingerprint.html", {"request": request, "fingerprint_img": fingerprint})

