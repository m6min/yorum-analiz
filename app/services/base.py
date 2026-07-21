import asyncio
import random
import re

import emoji
from playwright.async_api import Page

ORTAK_CONTEXT_SECENEKLERI = {
    # context'e eşitlenecek ortak config
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "locale": "tr-TR",
    "viewport": {"width": 1920, "height": 1080},
    "timezone_id": "Europe/Istanbul",
}

class Scraper:
    """Sınıf scraping fonksiyonları için ortak özellik ve metotları tutar."""
    @staticmethod
    async def rastgele_bekle(mini = 1.0, maxi = 3.2):
        """Hareketsizlik için rastgele bekleme süresi yaratır. Default: mini 1.0, maxi 3.2  """
        await asyncio.sleep(random.uniform(mini, maxi))

    @staticmethod
    async def rastgele_imlec_hareketi(sekme: Page):
        """Rastgele mouse hareketi oluşturur"""
        await sekme.mouse.move(random.randint(100, 800), random.randint(100, 600))

    @staticmethod
    async def engelle(route):
        """Resimlerin indirilmesini devre dışı bırakarak tarayıcıyı hızlandırır"""
        if route.request.resource_type in ["image", "media"]:
            # Sadece resim ve video engelle, CSS/font bırak
            await route.abort()
        elif any(x in route.request.url for x in ["google-analytics", "doubleclick", "facebook"]):
            # Reklam ve tracking engelle
            await route.abort()
        else:
            await route.continue_()

    @staticmethod
    async def emoji_temizle(metin:str) -> str:
        """Yorumlardan emojileri çıkartır."""
        return emoji.replace_emoji(metin, replace="")

    @staticmethod
    async def asagi_kaydir(sekme: Page, adim=300, bekleme=0.5):
        """Sayfada aşağı kaydırır. Argümanlar: sekme (Page objesi),
        adim = 300 (int) ve bekleme = 0.5 (ms)
        """
        toplam_yukseklik = await sekme.evaluate("document.body.scrollHeight") / 2
        mevcut = 0

        while mevcut < toplam_yukseklik:
            await sekme.evaluate(f"window.scrollBy(0, {adim})")
            mevcut += adim
            await asyncio.sleep(bekleme)

    @staticmethod
    async def tarih_cevir(cekilen_tarih: str | None) -> str:
        """String şeklinde yazılmış ayı tarih formatına dönüştürür

        Args:
            cekilen_tarih (str):
        """
        aylar = {
            "ocak": "01",
            "şubat": "02",
            "mart": "03",
            "nisan": "04",
            "mayıs": "05",
            "haziran": "06",
            "temmuz": "07",
            "ağustos": "08",
            "eylül": "09",
            "ekim": "10",
            "kasım": "11",
            "aralık":"12"
        }
        if cekilen_tarih:
            parcalar = re.findall(r'[0-9]+|[a-zA-ZğüşıöçĞÜŞİÖÇ]+', cekilen_tarih)
            ay = aylar[parcalar[1].lower()]
            tarih = "-".join([parcalar[2], ay, parcalar[0].zfill(2)])
            return tarih
        raise TypeError

class ScrapeError(Exception):
    """Scrape classlarının metotlarında raise verir"""
