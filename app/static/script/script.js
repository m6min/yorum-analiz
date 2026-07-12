const URLparam = new URLSearchParams(window.location.search);
const islemId = URLparam.get('islem_id');

const DURUM = {
  BULUNAMADI: -1,
  ISLEMDE: 0,
  TAMAMLANDI: 1
};

let denemeSayisi = 0;
const MAX_DENEME = 60;

async function durumuOgren() {
  if (!islemId) {
    window.location.href = "/";
    return;
  }

  try {
    const cevap = await fetch(`/durum/${islemId}`);
    if (!cevap.ok) throw new Error("Sunucu hatası");

    const veri = await cevap.json();

    if (veri.state === DURUM.TAMAMLANDI) {
      window.location.href = `/sonuc/${islemId}`;
      return;
    }

    if (veri.state === DURUM.BULUNAMADI) {
      window.location.href = "/hata";
      return;
    }

    denemeSayisi += 1;
    if (denemeSayisi >= MAX_DENEME) {
      alert("İşlem çok uzun sürdü. Bunu düzeltmeye çalışıyoruz. Lütfen daha sonra tekrar deneyin.");
      window.location.href = "/";
      return;
    }

    const bekleme = Math.min(1000 + denemeSayisi * 500, 5000);
    setTimeout(durumuOgren, bekleme);
  } catch (err) {
    console.error("Durum alınamadı:", err);
    setTimeout(durumuOgren, 3000);
  }
}

durumuOgren();
