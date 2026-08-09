# Mevcut master videolardan repurpose denetimi (Faz 0, hafif geçiş)

## Kapsam ve dürüstlük notu

`kaggle datasets metadata` ile 9 mevcut masterın (`mehmetkync16/ai-audiobook-studio-videos`
dataset'i) açıklama/subtitle alanları çekildi — ikisi de boş, kullanışlı
bir metin sinyali yok. Videoların gerçek sahne içeriğini görmek tek yol
olarak indirip izlemek (toplam ~5.8GB) — bu, backlog sınıflandırmasının
ikincil bir iyileştirme adımı için orantısız bir maliyet, bu yüzden
**bu geçişte yapılmadı**. Aşağıdaki eşleşmeler yalnızca dosya adı/konu
başlığı temelli hipotezler - `content_backlog.json`'daki `tier`/`source`
alanları bu hipotezlerle DEĞİŞTİRİLMEDİ (yanlış bir "doğrulandı" iddiası
olmasın diye, CLAUDE.md madde 4). Gerçek içerik denetimi ayrı, sonraki
bir görev olarak kalıyor.

## Dosya adı temelli hipotezler (doğrulanmamış)

| Master | Muhtemel örtüştüğü bölüm | Güven |
|---|---|---|
| `berel-hatun-kurgan11.mp4` | KURGANLAR (61-80) — ama KURGANLAR'daki 20 başlık genel "kurgan nedir" soruları, bu video özel olarak Berel kurganına odaklı görünüyor (isminden) - KISMİ örtüşme olası, TAM ikame değil | düşük-orta |
| `avrasya_bozkir_kusagi_master.mp4` | BÖLÜM 1 — BOZKIRIN DOĞUŞU (31-60) ve/veya BOZKIR FELSEFESİ (601-700) | düşük-orta |
| `bozkirin-uyanisi-v2.mp4` | BOZKIR FELSEFESİ (601-700) — başlık ("bozkırın uyanışı") tematik olarak yakın | düşük-orta |
| `taidula-epic-...v2.mp4` | Dosyada doğrudan karşılığı yok (Taidula Hatun, Altın Orda) — muhtemelen backlog dışı, ayrı bir konu | - |
| `urkun-1916.mp4` | Dosyada doğrudan karşılığı yok (1916 Ürkün) — muhtemelen backlog dışı, ayrı bir konu | - |
| `baskurtlar_master.mp4` | TÜRK DÜNYASI HALKLARI (351-400) içinde Başkurt maddesi varsa | düşük |
| `daglarin_uyuyan_devleri_master.mp4`, `gok_umay_atlasi_master.mp4` | Marka/tanıtım içerikleri, backlog'un konu bölümleriyle örtüşmüyor | - |

## Sonuç

Repurpose havuzu şimdilik SADECE `content_backlog.json`'da zaten
işaretlenmiş 100 kayıtla (Aşarşılık Evreni + Ryskulov Dosyası, hepsi
`ryskulov_mektubu_master.mp4`'e bağlı) sınırlı tutuluyor — bu tek eşleşme
dosyanın kendi metniyle güçlü şekilde destekleniyor (bkz.
`content_backlog.json`). Yukarıdaki tablo, gerçek video izleme yapıldığında
takip edilecek bir aday listesi olarak kayda geçirildi, backlog verisine
henüz işlenmedi.
