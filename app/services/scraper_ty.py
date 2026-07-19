import asyncio

from playwright.async_api import Browser, Page, async_playwright

from services.base import ORTAK_CONTEXT_SECENEKLERI, ScrapeError, Scraper


class Trendyol:
    """Trendyol platformu yorumları için gereken statik fonksiyonları tutar"""
    @staticmethod
    async def main(url: str) -> list[dict]:
        """Trendyol sitesi için yorumları alan ve döndüren scraping main fonksiyonu.
        Hatalar mock_model içinde exception ile yakalanmalı.
        """
        async with async_playwright() as p:
            tarayici = None
            try:
                tarayici = await p.chromium.launch(headless=True, slow_mo=500, args=["--disable-blink-features=AutomationControlled"])
                sekme = await Trendyol.tum_yorumlara_git(tarayici, url)

                yorumlar = await Trendyol.yorumlari_al(sekme)
            except Exception as e:
                raise ScrapeError(f"Yorumları alma başarısız oldu: {e}")
            finally:
                if tarayici:
                    await tarayici.close()
        return yorumlar


    @staticmethod
    async def tum_yorumlara_git(tarayici: Browser, url: str):
        """Ürünlerin 'Tüm Değerlendirmeler' sayfasına bağlanır."""
        context = await tarayici.new_context(**ORTAK_CONTEXT_SECENEKLERI)
        await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        sekme = await context.new_page()
        # Belleği hızlandırmak için tracking ve resim engellemesi
        await sekme.route("**/*", Scraper.engelle)
        await sekme.goto(url, timeout=30000)
        await Scraper.rastgele_bekle(0.2, 1.0)

        cookie_butonu = sekme.locator("div[aria-describedby*='onetrust-policy-text']")
        await Scraper.rastgele_imlec_hareketi(sekme)
        if await cookie_butonu.is_visible(timeout=3000):
            await sekme.locator("button[id*='onetrust-reject-all-handler']").click()
            await Scraper.rastgele_bekle()

        await Scraper.asagi_kaydir(sekme=sekme)

        await sekme.screenshot(path="ss.png", full_page=True)
        buton = sekme.locator('[data-testid="show-more-button"]').first
        await buton.wait_for(state="attached", timeout=50000)
        await buton.click(force=True)
        await Scraper.rastgele_bekle(0.3, 1.2)

        return sekme

    @staticmethod
    async def yorumlari_al(sekme: Page) -> list[dict]:
        """Asıl yorum sayfasına geçtikten sonraki eylemleri kapsar"""
        beklenecek_eleman = sekme.locator("div[class*='review-list']").first
        await beklenecek_eleman.wait_for(state="visible")
        await Scraper.rastgele_bekle(1.3, 2.5)

        await sekme.evaluate("window.scrollBy(0, 700)")
        toplanan_veriler: list[dict] = []
        gorulen_yorumlar = set()
        kartlar_locator = sekme.locator("div[class='review']")
        while True:
            await sekme.evaluate("""
            () => {
                const linkler = document.querySelectorAll('div.review-comment a.read-more');
                
                for (const link of linkler) {
                    if (link.innerText.includes('Devamını')) {
                        link.click();
                    }
                }
            }
            """)
            await Scraper.rastgele_bekle(0.7, 1.2)
            kartlar = await kartlar_locator.all()
            for kart in kartlar:
                yorum = await kart.locator("span[class*='review-comment']").text_content()
                if yorum and yorum not in gorulen_yorumlar:
                    cekilen_tarih = await kart.locator("div[class*='date']").text_content()
                    tarih = await Scraper.tarih_cevir(cekilen_tarih)
                    yorum = yorum.replace("Devamını Oku", "")
                    temiz_yorum = await Scraper.emoji_temizle(yorum)
                    gorulen_yorumlar.add(temiz_yorum.strip())
                    toplanan_veriler.append({
                        "yorum": temiz_yorum.strip(),
                        "tarih": tarih
                    })

            eski_son_metin = await kartlar_locator.last.text_content()
            eski_toplam_sayi = len(kartlar)
            await Scraper.rastgele_bekle(0.4, 1.2)

            await kartlar_locator.last.scroll_into_view_if_needed()
            await asyncio.sleep(2) # Yeni verinin inmesi için bekle

            yeni_son_metin = await kartlar_locator.last.text_content()
            yeni_toplam_sayi = await kartlar_locator.count()

            if eski_son_metin == yeni_son_metin or eski_toplam_sayi == yeni_toplam_sayi or len(gorulen_yorumlar) > 500:
                break

        return toplanan_veriler
