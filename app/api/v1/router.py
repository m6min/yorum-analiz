import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import (APIRouter, BackgroundTasks, Form, HTTPException, Request,
                    status)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from core.platforms import Platformlar
from core.security import limiter
from db.database import (analiz_sonuclari_koleksiyonu,
                        islem_durumlari_koleksiyonu, yorumlar_koleksiyonu)
from services.worker import analiz_motoru

router = APIRouter()
templates = Jinja2Templates(directory="templates")
@router.get("/", name="ana_sayfa", response_class=HTMLResponse)
async def ana_sayfa(request: Request):
    """ Anasayfa endpointini tutuyor """
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/platform/{platform_adi}", name="platform",response_class=HTMLResponse)
async def platform(platform_adi: str, request: Request):
    """  Ürün linkini kullanıcıdan alır """
    try:
        Platformlar(platform_adi)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"{platform_adi} şuan için desteklenmiyor.")
    return templates.TemplateResponse(request= request, name="form.html",
                                    context={"secilen_platform": platform_adi})


PATTERN = r"^https://[a-zA-Z0-9.-]+\.com/[a-zA-Z0-9/_&+=?#.-]+$"
@router.post("/analiz/{secilen_platform}")
@limiter.limit("3/minute")
async def analiz(secilen_platform: Platformlar, urun_linki: Annotated[str, Form(pattern=PATTERN)],
                arkaplan_motoru: BackgroundTasks, request: Request):
    """ Analiz endpointi ile girilen link kontrol edilip bir yandan model işlemleri başlatılır, 
    yukleniyor endpointine direkt olarak yönlendirme yapar. """
    yapilmis_analiz = await analiz_sonuclari_koleksiyonu.find_one({"urun_linki": urun_linki})
    if yapilmis_analiz:
        # Yapılan eski analizle bugun arasındaki tarih farkını alıp analiz gerekliliği kararlaştırılır
        fark = datetime.now(timezone.utc) - yapilmis_analiz["tarih"].replace(tzinfo=timezone.utc)
        if fark.days < 30:
            islem_id = str(uuid.uuid4())
            await islem_durumlari_koleksiyonu.insert_one({
                "_id": islem_id,
                "state": 1,
                "urun_linki": urun_linki
            })
            return RedirectResponse(url=f"/sonuc/{islem_id}", status_code=status.HTTP_303_SEE_OTHER)

    # uygulamada açık 2 istek varsa 3. alınmaz.
    aktif_islem_sayisi = await islem_durumlari_koleksiyonu.count_documents({"state": 0})
    if aktif_islem_sayisi >= 2:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"mesaj": "Sunucu şu an tam kapasite çalışıyor. Lütfen 1-2 dakika sonra tekrar dene."},
            status_code=503
        )
    islem_id = str(uuid.uuid4())
    await islem_durumlari_koleksiyonu.insert_one({
        "_id": islem_id,
        "state": 0,
        "urun_linki": urun_linki
    })
    arkaplan_motoru.add_task(analiz_motoru, islem_id, urun_linki)
    return RedirectResponse(url=f"/yukleniyor?islem_id={islem_id}", status_code=303)

@router.get("/yukleniyor", response_class=HTMLResponse)
async def yukleniyor(islem_id: str, request: Request):
    if not islem_id:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="load.html", context={
        "islem_id": islem_id
    })

@router.get("/durum/{islem_id}")
async def durum_kontrol(islem_id: str):
    """ Javascriptin state bilgisini aldığı endpoint  """
    islem = await islem_durumlari_koleksiyonu.find_one({"_id": islem_id})
    if not islem:
        return {"state": -1}
    return islem

@router.get("/sonuc/{islem_id}", response_class=HTMLResponse)
async def sonuclari_goster(request: Request, islem_id: str):
    """ State kontrolünü yapıp işlemi gösterir veya anasayfa yönlendirmesi yapar"""
    islem_durumlari = await islem_durumlari_koleksiyonu.find_one({"_id": islem_id})
    if not islem_durumlari or islem_durumlari["state"] != 1:
        return RedirectResponse(url="/", status_code=403)
    url = islem_durumlari.get("urun_linki")
    islem = await analiz_sonuclari_koleksiyonu.find_one({"urun_linki": url})
    if not islem:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="result.html", context={
        "islem_id": islem_id,
        "result": islem["sonuclar"]
    })

@router.get("/api/grafik/{islem_id}")
async def grafik_verilerini_al(islem_id: str):
    """Grafik verilerini JSON tipinde hazırlar

    Args:
        islem_id (str)

    Returns:
        _JSON_
    """
    islem_durumu = await islem_durumlari_koleksiyonu.find_one({"_id": islem_id})
    if not islem_durumu or not islem_durumu.get("urun_linki"):
        return JSONResponse(status_code=404, content="İşlem bulunamadı.")
    url = islem_durumu["urun_linki"]
    # ürüne ait tüm yorumları tanımla
    cursor = yorumlar_koleksiyonu.find({"urun_linki": url})
    yorumlar_db = await cursor.to_list(length=400)
    grafik_verileri = []

    for kayit in yorumlar_db:
        veri = kayit.get("toplanan_veriler", {})
        tarih = veri.get("tarih")
        puan = veri.get("puan")
        if tarih and puan is not None:
            grafik_verileri.append({"x": tarih, "y": puan})

    return JSONResponse(content={"data": grafik_verileri})

@router.get("/hata", response_class=HTMLResponse)
async def hata_endpoint(request: Request):
    """Oluşan hataları bildirmek için path"""
    return templates.TemplateResponse(request=request, name="error.html", context={
        "hata_kodu": 400
    })
