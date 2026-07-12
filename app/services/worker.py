import traceback
from datetime import datetime, timezone

from core.platforms import Platformlar
from db.database import (analiz_sonuclari_koleksiyonu,
                        islem_durumlari_koleksiyonu, yorumlar_koleksiyonu)
from model.llm_service import ozellikleri_getir
from model.predict import puan_hesapla
from services.scraper_ty import Trendyol


async def analiz_motoru(islem_id: str, url: str):
    """İşleri yapan fonksiyonları sıraya koyar ve çalıştırır.

    Args:
        islem_id (uuid.UUID)
    """
    try:
        toplanan_veriler = await Trendyol.main(url)
        if not toplanan_veriler:
            await islem_durumlari_koleksiyonu.update_one(
                {"_id": islem_id},
                {"$set": {"state": -1, "context": "Bu üründe yorum bulunamadı."}}, upsert=True
            )
            return
        sadece_yorumlar = [veri["yorum"] for veri in toplanan_veriler]
        ortalama_puan, tekil_puanlar = puan_hesapla(sadece_yorumlar)
        kaydedilecek_veriler = []
        for index, veri in enumerate(toplanan_veriler):
            kaydedilecek_veriler.append({
                "urun_linki": url,
                "toplanan_veriler": {
                    "yorum": veri["yorum"],
                    "tarih": veri["tarih"],
                    "puan": tekil_puanlar[index]
                }
            })
        await yorumlar_koleksiyonu.insert_many(kaydedilecek_veriler)
        llm_ozeti = ozellikleri_getir(sadece_yorumlar)
        await analiz_sonuclari_koleksiyonu.insert_one(
            {"urun_linki": url,
            "tarih": datetime.now(timezone.utc),
                    "sonuclar": {
                        "pozitif_oran": ortalama_puan,
                        "ovulen_ozellikler": llm_ozeti["ovulenler"],
                        "sikayetler": llm_ozeti["sikayetler"]
                        }}
        )
        await islem_durumlari_koleksiyonu.update_one(
            {"_id": islem_id},
            {"$set": {"state": 1}}, upsert=True
        )
    except Exception as err:
        print("\n" + "="*50)
        print("HATA: ")
        traceback.print_exc()
        print("="*50 + "\n")
        await islem_durumlari_koleksiyonu.update_one(
            {"_id": islem_id},
            {"$set": {"state": -1, "context": str(err)}}
        )
