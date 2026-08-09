# Concept Card — Dede Korkut (EPIC tier, planning only, no production)

**Durum:** SADECE PLANLAMA. Faz 4(b) tetiklenmeden (uzun-video havuzu
tükenip yeni kaynak gerektiğinde) üretime girmez.

## Backlog'daki 50 kaydın (751-800) gerçek içeriği

`content_backlog.json`'daki 50 kayıt incelendiğinde: sadece **5 kaydın**
gerçek bir hikâye başlığı olduğu görüldü (Boğaç Han, Deli Dumrul, Bamsı
Beyrek, Kan Turalı, Basat ve Tepegöz) — geri kalan 45 kayıt tema/yorum
soruları ("Dede Korkut'ta adalet", "Dede Korkut ve sinema", "Dede
Korkut'tan bugüne kalanlar" gibi), anlatı içeriği değil.

**Önemli dürüstlük notu:** Bu 50 kayıt, gerçek bir "Dede Korkut epic'i"
üretmek için yeterli birincil kaynak İÇERMİYOR — sadece tartışma/pazarlama
katmanı. Gerçek Dede Korkut Kitabı **12 hikâyeden** oluşur (Dresden ve
Vatikan nüshaları), backlog'da sadece 5'i isimlendirilmiş. Gerçek bir epic
üretimi bu 50 kaydı sahne içeriği olarak KULLANAMAZ — Dede Korkut
Kitabı'nın orijinal metnine (M23 araştırma pipeline'ıyla, gerçek Faz
B/C/D/E) geri dönülmesi gerekir.

## Önerilen bölümlenme (üretime geçilirse)

1. **12 hikâye, her biri ~20-30dk** (Dirse Han oğlu Boğaç Han, Salur
   Kazan'ın evinin yağmalanması, Bamsı Beyrek, Kazan Bey'in oğlu Uruz'un
   esir düşmesi, Duha Koca oğlu Deli Dumrul, Kanlı Koca oğlu Kan Turalı,
   Kazılık Koca oğlu Yigenek, Basat'ın Tepegöz'ü öldürmesi, Begil oğlu
   Emren, Uşun Koca oğlu Segrek, Salur Kazan'ın esir düşüp oğlu Uruz
   tarafından kurtarılması, İç Oğuz'a Dış Oğuz'un isyanı) = **~4-6 saat
   toplam**, tek "epic" paketi veya 12 ayrı "bölüm" videosu olarak.
2. Backlog'un 45 tema/yorum kaydı bu üretimden BAĞIMSIZ olarak (veya
   üretimle eş zamanlı tanıtım/keşif katmanı olarak) short_new tier'a
   taşınabilir — içerik olarak zaten kısa-format hook'lar, bir epic
   üretimini beklemeleri gerekmiyor. Bu, kullanıcıya ayrı bir karar
   olarak sunulmalı (bu concept card üretime karar vermiyor, sadece
   kapsamı netleştiriyor).

## Ön koşullar (üretime geçilmeden önce)

- M23 pipeline'ı Dede Korkut Kitabı'nın gerçek metnine (çeviri/edisyon
  seçimi — hangi Türkçe/akademik baskı kaynak alınacak, telif durumu)
  karşı çalıştırılmalı.
- `style/` altında yeni bir destansı-anlatı stil profili gerekebilir
  (mevcut `historical_epic_steppe.json`'dan farklı — daha mitolojik/
  folklorik bir ton).
- Rights/telif: Dede Korkut Kitabı kamu malı (public domain, orta çağ
  eseri) ama MODERN çeviriler telifli olabilir — hangi çevirinin
  kullanılacağı `rights.source_basis` kararını doğrudan etkiler.
