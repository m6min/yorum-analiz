import os
import json
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("API Key bulunamadı. .env dosyasını kontrol edin.")

client = Groq()

def ozellikleri_getir(yorumlar_listesi: list[str]) -> dict:
    """Yorum listesini alıp LLM'den json ister"""
    yorumlar = "\n---\n".join(yorumlar_listesi)
    prompt = f"""
    Sen e-ticaret müşteri yorumlarını analiz eden kıdemli bir ürün yöneticisisin.
    Görevin: Aşağıdaki yorumları okuyup, müşterilerin genel olarak en çok beğendiği 3 özelliği ve en çok şikayet ettiği 3 temel sorunu tespit etmek.

    KESİN KURALLAR:
    1. Her iki liste de TAM OLARAK 3 elemanlı olacak. Ne eksik, ne fazla.
    2. Maddelerin yanına ASLA puan, olasılık, yüzde veya sayı (örn: 0.76) eklemeyeceksin. Saf metin olacak.
    3. Maddeler "ürün dandik", "ürün güzel" gibi basit kelimeler yerine, profesyonel, net ve okunabilir bir dille ifade edilmeli.
    Örnek Doğru Çıktılar: "Yüksek malzeme kalitesi", "Hızlı kargolama", "Beden tablosu uyumsuzluğu", "Kötü paketleme".
    4. Sadece ve kesinlikle json formatında çıktı ver.

    Beklenen json formatı:
    {{
        "ovulenler": ["özellik 1", "özellik 2", "özellik 3"],
        "sikayetler": ["şikayet 1", "şikayet 2", "şikayet 3"]
    }}

    Yorumlar:
    {yorumlar}
    """

    try:
        # Llama 3 modeli
        cevap = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        # Gelen JSON metnini python sözlüğüne çevir
        if cevap.choices and cevap.choices[0].message.content:
            return json.loads(cevap.choices[0].message.content)

        return {"ovulenler": [], "sikayetler": []}

    except Exception as err:
        print(f"API'den cevap beklenirken hata oluştu: {err}")
        return {"ovulenler": [], "sikayetler": []}
