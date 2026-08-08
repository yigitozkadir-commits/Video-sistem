# FAZ B — Derin Araştırma

**Kaynak modüller:** 03 (Deep Research), 06 (Deep-Dive Expansion), 12
(Research Expansion), 13 (Source Reconstruction / Primary Evidence),
25 (Source Discovery Orchestrator), 26 (Multilingual), 27 (Academic
Literature), 28 (Archive/Museum/Material Evidence)

**Girdi:** Faz A'nın `winning_candidate_id` Concept Card'ı.

**Çıktı:** `faz-b-dossier.json` — Claim listesi + Source Registry +
Evidence listesi (draft, henüz adversarial doğrulanmamış).

---

## B0 — Adaptif Araştırma Derinliği

Her alt soru/claim için aynı brute-force derinliğe gitme — konunun
epistemik riskine göre ölçekle (bu stüdyonun "cost is a constraint"
yasasının bu pipeline'daki karşılığı):

1. **Basic** — sıradan, tartışmasız, çevre bağlam bilgisi (ör. bir
   şehrin coğrafi konumu).
2. **Standard** — ana akım tarihsel iddialar, iyi belgelenmiş.
3. **Deep** — `core` önemdeki claim'ler, veya tek kaynağa dayanan
   iddialar.
4. **Academic** — ihtilaflı/az belgelenmiş konular; akademik literatür
   taraması (B3.2) zorunlu hale gelir.
5. **Archival/Specialist** — `historiographical_status: debate`
   olan veya milliyetçi/çatışmalı bir konudaki (bkz. Faz C2
   `perspective_diversity`) kritik claim'ler; arşiv/malzeme kanıtı
   (B3.5) ve çok dilli tarama (B3.4) zorunlu hale gelir.

Seviye seçimi `core`/`supporting`/`peripheral` önem derecesiyle
**birebir aynı değil** — peripheral bir claim bile, ihtilaflı bir konuda
Deep/Academic seviye gerektirebilir; core bir claim bile, tartışmasızsa
Standard'da kalabilir.

## B1 — Research Planner

Önce plan kur, sonra ara. Merkezî soruyu alt sorulara böl:

```
Ana soru
 → Alt sorular
   → Bu alt soruları cevaplamak için gereken iddia tipleri
     → Her iddia için gereken kanıt türü (birincil/ikincil/maddi)
       → Hangi kaynak rotaları gerekli (web/akademik/arşiv/çok dilli/malzeme)
       → Hangi sorgu tipi (arama stratejisini netleştirmek için):
         EXACT_CLAIM | PRIMARY_SOURCE | EARLIEST_ATTESTATION |
         COUNTER_EVIDENCE | ALTERNATIVE_INTERPRETATION | SOURCE_ORIGIN |
         LOST_DOCUMENT | ARCHIVAL_TRACE | LANGUAGE_SPECIFIC |
         NEGATIVE_SEARCH
```

Sorgu tipi etiketlemesi, B3'ün altı kanalını rastgele değil hedefli
kullanmak içindir — ör. `EARLIEST_ATTESTATION` bir sorgu B3.3'ün kaynak
zinciri çözümüne, `LANGUAGE_SPECIFIC` B3.4'ün çok dilli taramasına
yönlendirilir.

## B2 — Claim Decomposer

Concept Card'daki merkezi soruyu, her biri ayrı ayrı araştırılabilir
**atomik claim**'lere böl (bkz. `reference/sema.md` § 2). Her claim'e
`core/supporting/peripheral` önemi ata. Taslak `confidence` değerini
verirken `confidence_history`'ye ilk kaydı ekle:
`{"phase": "B", "value": "<taslak değer>", "reason": "ilk tarama sonrası taslak"}`.

## B3 — Çok kanallı kaynak taraması

Aşağıdaki kanalları, konunun ihtiyacına göre (hepsi her konu için
zorunlu değil — Source Router mantığı) seç ve gerçek araçlarla tara:

1. **Web / genel keşif** — **WebSearch**, sonra ilgili sayfaları
   **WebFetch** ile derinlemesine oku.
2. **Akademik literatür** (Modül 27) — mümkünse akademik arama
   sorguları dene (**WebSearch** ile "site:scholar.google.com",
   dergiler, üniversite yayınları — opsiyonel Semantic Scholar API
   anahtarı varsa `api.semanticscholar.org`'a doğrudan WebFetch ile de
   sorgu atılabilir, bkz. M23 §6); her çalışma için: soru, yöntem,
   kanıt, sonuç, sınırlamalar, sonraki eleştiriler.
   **Citation Hallucination Detector**: bir akademik kaynağı Source
   Registry'ye eklemeden önce, yazar/yıl/yayın/sayfa bilgisinin
   gerçekten var olduğunu ve iddia edilen içeriği gerçekten
   içerdiğini doğrula (WebFetch ile kaynağın kendisini veya güvenilir
   bir katalog kaydını kontrol ederek). Doğrulanamıyorsa kaynağı
   `reliability: "unverified"` ile ekle ve claim'e bağlarken
   `notes` alanına `CITATION_UNVERIFIED` yaz — asla var olduğu
   doğrulanmamış bir atfı sağlammış gibi kullanma.
3. **Birincil kaynak / kaynak zinciri çözümü** (Modül 13) — modern
   iddianın arkasındaki zincir: modern yazar → önceki tarihçi → daha
   eski kaynak → birincil kanıt. Mümkün olduğunca zincirin başına in;
   bulduğun en eski atfı kaynağın `earliest_attestation` alanına yaz
   (`reference/sema.md § 4`).
4. **Çok dilli araştırma** (Modül 26) — konu belirli bir dil/kültür
   alanına aitse, o dildeki terimlerle de ara; çeviri farklarını not
   et, orijinal ifadeyi koru.
5. **Arşiv / müze / maddi kanıt** (Modül 28) — mümkünse: eser,
   yazıt, sikke, arkeolojik kayıt, harita gibi metin-dışı kanıtları
   da ara (özellikle antik/erken dönem konularda önemli). Konu
   gerektiriyorsa (ör. göç/nüfus tarihi, bozkır tarihi) demografik,
   genetik ve paleoiklim kanıtları da bu kanala dahildir
   (`reference/sema.md § 3`'ün `evidence_type` listesi) — ama
   **yalnızca soruyu gerçekten cevaplıyorsa**, "tamlık için" ekleme.
   Bir arşiv kaydına ulaşamıyorsan (kayıp/parça/ihtilaflı), kaynağın
   `document_status` alanını (`KNOWN | MISSING | FRAGMENTARY |
   DISPUTED | UNLOCATED`) doldur — bu, B3b'nin erişim durumundan
   ayrı, kaydın kendi varlık durumudur.
6. **Karşı kanıt araması (negative search)** — sadece destekleyici
   kanıt aramakla yetinme; "X iddiasını çürüten kaynak var mı" diye
   de ayrıca ara.

Her bulunan kaynak, Source Registry'ye `reference/sema.md § 4`
şemasıyla eklenir. Her önemli iddia, Evidence kaydına
(`reference/sema.md § 3`) bağlanır.

## B3b — Erişilemeyen Kaynak Protokolü

**WebFetch** bir kaynağa ulaşamazsa (paywall, 404, erişim engeli),
tek adımda "kaynak bulunamadı" diye işaretleyip geçme. Sırayla dene,
ilk başarılı olanda dur:

1. **Wayback Machine / Internet Archive** — **WebFetch** ile
   `https://web.archive.org/web/*/<orijinal-url>` dene (bu stüdyoda
   `scripts/find_reference_images.py`'nin `archive_org` sağlayıcısı da
   aynı Internet Archive altyapısını görsel kaynak taraması için
   kullanıyor — anahtar/kurulum gerekmez, aynı serbest erişim).
2. **Google Books önizlemesi** — kitap/makale ise **WebSearch** ile
   başlık + yazar + "google books" sorgusuyla ara.
3. **Aynı içeriğe başka bir yayının atfı** — makalenin kendisine
   değil, ona atıf yapan/alıntılayan başka bir akademik kaynağa
   ulaşmayı dene (dolaylı ama bazen yeterli).
4. **Kütüphane/kurumsal arşiv kaydı** — en azından kaynağın var
   olduğunu doğrulayan bir katalog/DOI kaydı ara (içeriğe erişim
   olmasa bile).

Bu dört adımın hepsi başarısızsa, kaynağı `SOURCE_GAP` olarak
işaretle (bkz. `reference/sema.md § 1`) ve **hangi adımların
denendiğini** kısaca not et (`attempted_access_methods` alanı) —
sadece "bulunamadı" yazıp geçme, ne denendiğini kaydet ki aynı
kaynak sonraki bir oturumda tekrar baştan denenmesin.

## B4 — Genişleme / Doygunluk (Saturation)

Araştırma şu noktaya kadar derinleştirilir:

- Yeni aramalar mevcut bulguları tekrar etmeye başlıyor,
- Karşı kanıt araması da doygunluğa yaklaşıyor,
- Açık soruların sınırları belirginleşti.

Bu noktaya ulaşınca genişlemeyi durdur ve kalanları `research_gaps`
olarak işaretle (Faz D'de detaylandırılacak).

**Bağlam Sınırı (Context Boundary) kuralı:** Bağlamsal/çevresel
araştırmayı (ana soruyu doğrudan cevaplamayan ama anlamak için gereken
arka plan), daha fazla bağlam artık ana sorunun cevabını
**değiştirmemeye** başladığı noktada durdur. Bağlam araştırması kendi
başına bir amaç değildir — ne kadar ilginç olursa olsun.

**Sahte Tamamlanma (False Completion) uyarısı:** "N kaynak bulundu"
tek başına tamamlanma göstergesi değildir — gerçek tamamlanma altı ayrı
eksende ölçülür: claim kapsamı, kanıt kalitesi, kaynak bağımsızlığı,
birincil kaynak kapsamı, karşı-argüman kapsamı, boşluk kapsamı. Faz D4'te
tam denetim listesiyle tekrar kontrol edilir — burada sadece "sayı
yeterli göründü" diye erken durmamak için bir hatırlatma.

## Zorunlu disiplin

- Fact / inference / interpretation / speculation ayrımını asla
  bulanıklaştırma.
- Bir kaynağın çok tekrarlanması = doğrulanmış demek değildir; kaç
  **bağımsız** kaynak olduğuna dikkat et (`independence_group` alanı).
- Kaynak bulunamıyorsa doğrudan pes etme — önce **B3b Erişilemeyen
  Kaynak Protokolü**'ndeki sırayı uygula; hepsi başarısızsa
  `SOURCE_GAP` olarak açıkça işaretle. Asla kaynak uydurma, asla URL
  uydurma.

## Çıktı şeması — `faz-b-dossier.json`

```json
{
  "phase": "B",
  "candidate_id": "CAND-01",
  "research_question": "",
  "sub_questions": [""],
  "claims": [ /* reference/sema.md § 2 formatında, draft */ ],
  "evidence": [ /* § 3 */ ],
  "sources": [ /* § 4 */ ],
  "counter_evidence_search_performed": true,
  "cross_language_search_performed": true,
  "material_evidence_checked": true,
  "saturation_reached": true,
  "open_gaps_preview": ["kısa not — Faz D'de detaylandırılacak"]
}
```
