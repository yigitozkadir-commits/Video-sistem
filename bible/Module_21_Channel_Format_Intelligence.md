# MODULE 21 — KANAL FORMAT ZEKÂSI (CHANNEL FORMAT INTELLIGENCE)

**Versiyon 2.0** · **Katman 9** (Harici Zeka) · **Rol:** Rekabetçi Format Araştırması  
**Yürütücü:** Claude Code — WebSearch/WebFetch + kullanıcının sağladığı belgeler (docx/PDF)

**⚠️ DÜZELTME (v2.0, 2026-08-07):** v1.0 bu modülü "bağımsız bir Gemini-API sistemi, Claude Code tarafından asla çalıştırılmaz" olarak tanımlıyordu. Bu hiç doğru olmadı — dört gerçek CFP raporu (`reports/channel_format_profile_{gercegi_bul,nida_yildirim,sercanbaylan,portal}.json`) zaten üretildi ve hepsi Claude Code tarafından, WebSearch + kullanıcının yüklediği analiz belgeleriyle yazıldı. Ne bir Gemini anahtar havuzu (`reports/gemini_key_pool_ledger.json`) ne de ayrı bir yürütücü hiç var oldu. Bu sürüm modülü gerçekte ne olduğuna göre yeniden yazıyor — CFP şeması ve mevcut 3 rapor değişmiyor, sadece yürütücü/kapsam iddiası düzeltiliyor. Bir sonraki bölüm bunun neden bir sorun olduğunu ve neyin değişmediğini açıklıyor.

---

## 1. MİSYON

Kullanıcının belirttiği kanal/video örnekleri üzerinden, o içeriklerin **YAPISINI** çıkarır:
- Kanca süresi ve türü
- Sahne/kesme ritmi
- Anlatım hızı (wpm)
- Müzik yoğunluğu
- Başlık ve thumbnail kalıp eğilimleri

Bu bilgi **M17 AI Director**'a bir "kıyas noktası" (benchmark) olarak sunulur; hiçbir zaman hikaye, karakter canon veya prompt **İÇERİĞİNİ** ezmez veya değiştirmez.

---

## 2. YETKİ SINIRLARI

### Karar verebilir:
- Format kalıpları
- Pacing benchmark'ları
- Hook şablon türleri
- Sahne-süresi dağılım örnekleri
- Başlık/thumbnail kalıp eğilimi özetleri
- Narration speed, music density, cut frequency

### Karar veremez:
- Hikaye içeriği
- Karakter/ses kimliği (M15 §9 lock kuralı burada da geçerli)
- Prompt'ların creative içeriği
- Bible/schemas/prompts altında herhangi bir dosya yazması
- Hiçbir şekilde CLAUDE.md veya operational config değiştirmesi

### Asla yapamaz:
- Bir kanalın video/ses/görselini indirip yeniden kullanması
- Birebir metin/replik aktarması
- İçerik reprodüksiyonu
- Sadece **ölçülebilir yapısal metrikler** (sayı, oran, kategori) üretir

---

## 3. GERÇEK YÜRÜTÜCÜ — Claude Code, WebSearch + kullanıcı belgeleri

Havuz/rotasyon/kota apparatus'u yok çünkü ayrı bir API sistemi yok. Gerçek akış:

1. Kullanıcı bir kanal/video referansı verir (URL) VE/VEYA kendi hazırladığı bir
   analiz belgesi yükler (docx/PDF — üç mevcut raporun ikisi tam olarak bu
   yoldan geldi: kullanıcının kendi 50 maddelik uygulamalı analizi).
2. Claude Code `WebSearch`/`WebFetch` ile kanalın genel yapısını araştırır
   (kullanıcı sadece URL verdiyse) VEYA kullanıcının belgesini doğrudan okur
   (kullanıcı belge yüklediyse — bu her zaman daha güçlü kanıt, `confidence`
   alanına yansıtılır).
3. Bulgular `schemas/channel_format_profile.schema.json`'a uyacak şekilde
   yazılır, `confidence` alanı kanıtın gücünü dürüstçe yansıtır (sadece
   WebSearch: düşük; kullanıcının uygulamalı belgesi: yüksek — `CFP-0001`'in
   kendi `notes` alanında bu yükseliş 0.3→0.75 olarak kayıtlı, gerçek bir
   emsal).
4. Ölçülemeyen/doğrulanamayan alanlar (`cut_frequency_per_min`,
   `narration_pace_wpm` gibi kare-kesin metrikler) **icat edilmez** — boş
   bırakılır, `notes` alanında neden ölçülemediği yazılır (CFP-0001'in kendi
   örneği: "Frame-exact metrics... still were not measured from actual
   footage/transcripts and remain unset rather than invented").

Bu, M13'ün "Deterministic Check (T1)" hiyerarşisine girmez — bu modülün
çıktısı doğası gereği yorumlayıcı/araştırmacı, kare-kesin değil; dürüstlük
mekanizması havuz/kota değil, `confidence` alanı + boş-bırakma disiplinidir.

---

## 4. GİRDİ

- `target_channels`: Kullanıcının incelenmesini istediği kanal/video referansları
  - Format: YouTube URL veya channel ID
  - Kullanıcı tarafından **açıkça** verilir
  - Bu modül kendiliğinden kanal keşfi/taraması yapmaz
  - **Pasif ve hedef-belirtilmiş çalışır**

---

## 5. ÇIKTI KONTRATI

```
reports/channel_format_profile_<channel_id>.json  — CFP-xxxx şemasıyla
```

Tüm çıktılar `schemas/channel_format_profile.schema.json` ile validate edilir.
(v1.0'daki `reports/gemini_key_pool_ledger.json` kaldırıldı — hiç var olmayan
bir havuzun durumunu tutan bir dosya.)

---

## 6. M17 İLE ENTEGRASYON

**M17 §3 Decision Object**'ine opsiyonel bir alan eklenir:

```json
{
  "shot_id": "SC-001",
  "decision": "video",
  "benchmark_refs": ["CFP-0007"],
  "reasoning": "Hero beat, established format supports longer action sequences"
}
```

**Önemli:**
- `precedent_refs` (kendi geçmiş kararları) ile karıştırılmaz
- `benchmark_refs` sadece **dış ilham noktasıdır**
- Hiçbir zaman **zorunlu** değildir
- Hikaye/karakter kararını **asla geçersiz kılamaz**
- M17 §2 **authority ladder** aynen geçerli: **Director hâlâ tek yaratıcı otorite**

---

## 7. HATA MODLARI VE İLK HAMLELER

| Belirti | Sebep | İlk hamle | İnsan Bildirimi |
|---------|-------|-----------|-----------------|
| Kaynağa erişilemiyor (private/silinmiş) | Video/kanal artık yok | Finding kaydet, atla | Evet, warning seviyesi |
| WebSearch/WebFetch yetersiz kanıt döndürüyor | Kanal hakkında az genel bilgi var | `confidence` düşük tutulur, alanlar boş bırakılır — icat edilmez | Evet, info seviyesi |
| Kullanıcının belgesi CFP şemasına uymuyor bir iddia içeriyor | Belge format-dışı bir şey ölçmüş | Şemaya uyan alanlara aktar, gerisini `notes`'a düz metin olarak koy | Evet, info seviyesi |
| Şema doğrulamıyor | Yazım hatası/eksik zorunlu alan | `error.schema.json` döndür | **HALT** — debug required |

---

## 8. KABUL KRİTERLERİ (özet — resmî liste §11'de)

- [ ] Her profil `sha256` + `generated_at` + kaynak referans içerir
- [ ] Hiçbir alan **birebir metin/kare/ses içermez** — sadece sayısal/kategorik metrikler
- [ ] Disclaimer: "Structural/format analysis only. No content reproduction."
- [ ] M17 kararları hâlâ kendi log'undan "neden" sorusuna cevap veriyor
  - `benchmark_refs` kararın **SEBEBİ** değil, sadece **ilham kaynağı referansıdır**
- [ ] Bu modülün hiçbir çıktısı şu altına yazmaz:
  - `bible/`
  - `schemas/` (kendi şeması hariç)
  - `prompts/`
  - `scenes/*/spec`
- [ ] Şema doğrulaması geçti: `python3 scripts/validate.py reports/channel_format_profile_*.json`

---

## 9. OPERASYONEL NOTLAR

### Ne zaman çalışır
- Ana prodüksiyon akışını bloklamaz — kullanıcı bir kanal referansı verdiğinde
  veya bir analiz belgesi yüklediğinde tetiklenir, arka planda/ayrı bir turda
  işlenir.
- Sonuç M17 kararlarına opsiyonel girdi olarak sunulur; hazır olmasa da M17
  kendi ağacıyla karar vermeye devam eder (§10).

### Maliyet
- WebSearch/WebFetch bu oturumun standart araçları — ayrı bir API maliyeti
  veya kota yok. Kullanıcının belge yüklemesi de ücretsiz.

### Saklama
- Rapor saklama süresi için resmî bir politika yok (v1.0'ın "30 gün" iddiası
  hiç uygulanmadı) — mevcut 3 rapor süresiz saklanıyor, ileride gerekirse
  netleştirilecek.

---

## 10. SONRAKI BAĞLANTILAR

**NONE** — Bu katman (Katman 9, en dışta) diğer modüllere aşağıdan bağımlı değil. Yukarıdan opsiyonel girdi sağlar.

Başka modüller buna bağlı değildir; kapatılırsa sistem çalışmaya devam eder (M17 benchmark_refs sadece opsiyoneldir).

---

## 11. ACCEPTANCE CRITERIA

- [ ] Her CFP raporu `schemas/channel_format_profile.schema.json`'a karşı doğrulanır (`python3 scripts/validate.py`)
- [ ] Her profil `sha256` + `generated_at` + kaynak referans (URL veya kullanıcı belgesi adı) içerir
- [ ] Hiçbir alan birebir metin/kare/ses reprodüksiyonu içermez — sadece yapısal/sayısal/kategorik metrikler
- [ ] Ölçülemeyen alanlar (`cut_frequency_per_min` gibi kare-kesin metrikler) icat edilmek yerine boş bırakılır, `notes`'ta neden belirtilir
- [ ] `confidence` alanı kanıtın gerçek gücünü yansıtır (WebSearch-only < kullanıcı belgesi)
- [ ] M17'ye giden `benchmark_refs` hiçbir zaman zorunlu değildir, hikaye/karakter kararını geçersiz kılmaz
- [ ] Bu modül `bible/`, `schemas/` (kendi şeması hariç), `prompts/`, `scenes/*/spec` altına hiçbir şey yazmaz

---

## CHANGELOG

- **v2.1 (2026-08-08):** `CFP-0004` (Portal) eklendi — dördüncü kanal, ilk
  kez bu sürümde profillendi. Ayrıca `CFP-0002` (Gerçeği Bul) ve `CFP-0003`
  (Nida Yıldırım) kullanıcının sağladığı bağımsız 50-madde derin-analiz
  kaynağıyla zenginleştirildi (`confidence` sırasıyla 0.7→0.8, 0.6→0.75) —
  kaynak PDF'ler `reports/source_docs/{gercegi_bul,nida_yildirim,portal}_50madde/`
  altında arşivlendi. CFP-0004'ün kaynak materyali, önceki iki kanaldan
  farklı olarak, nihilizmi/depresyonu "en rasyonel tepki" olarak
  çerçeveleyip anonim anlatıcı etrafında "kült" dilini bir başarı ölçütü
  sayıyor — bu, `templates/TPL-baskurtlar-hybrid.json`/`TPL-ryskulov-hybrid.json`'daki
  K4/K9 dışlama kararlarından daha kapsamlı bir editoryal filtrelemeyi
  gerektirdi (`templates/TPL-portal-video-essay.json`'ın
  `content_rules.rules_explicitly_not_adopted`'ı bunu tam gerekçesiyle
  belgeliyor). CFP şeması değişmedi.
- **v2.0 (2026-08-07):** v1.0'ın "bağımsız Gemini-API sistemi, Claude Code
  tarafından çalıştırılmaz" iddiası kaldırıldı — üç gerçek CFP raporu zaten
  Claude Code tarafından WebSearch + kullanıcı belgeleriyle üretilmişti, ayrı
  bir yürütücü hiç var olmadı. 3-key Gemini havuzu, `gemini_key_pool_ledger.json`
  çıktısı, RPM/rate-limit hata modları ve `.env`'deki `GEMINI_API_KEY_01/02/03`
  kaldırıldı (hiçbiri hiç kullanılmadı). CFP şeması ve mevcut 3 rapor
  değişmedi. ACCEPTANCE CRITERIA ve CHANGELOG bölümleri eklendi
  (`scripts/validate.py` eksikliği zaten uyarıyordu).
- **v1.0:** İlk taslak — Gemini-API tabanlı bağımsız sistem olarak tasarlandı, hiç bu şekilde uygulanmadı.

---

**END OF MODULE 21**
