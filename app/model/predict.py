import joblib
import numpy as np

model = joblib.load("model/model.joblib")

def puan_hesapla(yorumlar: list[str]) -> tuple:
    """Playwright'tan gelen n yorumlu listeyi alır,
    modelden geçirir ve 10 üzerinden genel bir puan döner.

    Args:
        yorumlar (list[str])
    """
    if not yorumlar:
        return 0.0, []
    olasiliklar = model.predict_proba(yorumlar)
    # Yorum puanı pozitivite üzerinden 1. index, negativite üzerinden 0. index
    pozitif_puanlar = [round(float(olasilik[1] * 10), 1) for olasilik in olasiliklar]
    genel_puan = np.median(pozitif_puanlar)
    return round(float(genel_puan), 1), pozitif_puanlar
