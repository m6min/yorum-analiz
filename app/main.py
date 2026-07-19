import asyncio
import logging
import sys
import os

from fastapi.responses import FileResponse
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.v1.router import router
from core.security import limiter

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Yorum Analizi API", version="1.0")

app.state.limiter = limiter

app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.exception_handler(StarletteHTTPException)
@app.exception_handler(RequestValidationError)
async def hatalari_uret(request: Request, exc: StarletteHTTPException | RequestValidationError):
    """ 404 ve diğer kodlu hatalar için özel hata sayfalarına yönlendirme yapar """
    if isinstance(exc, RequestValidationError):
        logger.error("Validasyon hatası - Path: %s - Detay: %s", request.url.path, exc.errors())
        return templates.TemplateResponse(request=request, name="error.html",
                                        context={"hata_kodu": 422, "hata_mesaji": "Geçersiz istek"},
                                        status_code=422)
    logger.error("Hata %s: %s - Path: %s", exc.status_code, exc.detail, request.url.path)
    if exc.status_code == 404:
        return templates.TemplateResponse(request=request, name="404.html",
                                        context={"hata_mesaji": exc.detail}, status_code=404)

    return templates.TemplateResponse(request=request, name="error.html",
                                    context={ "hata_kodu": exc.status_code,
                                            "hata_mesaji": exc.detail}, status_code=exc.status_code)

@app.get("/fotograf")
async def fotograf_getir():
    # Eğer fotoğraf varsa ekranda göster
    if os.path.exists("ss.png"):
        return FileResponse("ss.png")
    return {"mesaj": "Henüz fotoğraf çekilmedi"}

@app.exception_handler(RateLimitExceeded)
async def rate_limit_yakalayici(request: Request, exc: Exception):
    """Rate limitini aşan kullanıcılara error.html gösterir."""
    #logger.error("Hata %s: %s - Path: %s", exc.status_code, exc.detail, request.url.path)
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"mesaj": "Çok fazla istek attın! Lütfen daha sonra tekrar dene."},
        status_code=429
    )
app.add_exception_handler(RateLimitExceeded, rate_limit_yakalayici)
