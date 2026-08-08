# FAZ B — Derin Araştırma

**Kaynak modüller:** 03 (Deep Research), 06 (Deep-Dive Expansion), 12
(Research Expansion), 13 (Source Reconstruction / Primary Evidence),
25 (Source Discovery Orchestrator), 26 (Multilingual), 27 (Academic
Literature), 28 (Archive/Museum/Material Evidence)

**Girdi:** Faz A'nın `winning_candidate_id` Concept Card'ı.

**Çıktı:** `faz-b-dossier.json` — Claim listesi + Source Registry +
Evidence listesi (draft, henüz adversarial doğrulanmamış).

---

## B1 — Research Planner

Önce plan kur, sonra ara. Merkezî soruyu alt sorulara böl:

```
Ana soru
 → Alt sorular
   → Bu alt soruları cevaplamak için gereken iddia tipleri
     → Her iddia için gereken kanıt türü (birincil/ikincil/maddi)
       → Hangi kaynak rotaları gerekli (web/akademik/arşiv/çok dilli/malzeme)
```

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
3. **Birincil kaynak / kaynak zinciri çözümü** (Modül 13) — modern
   iddianın arkasındaki zincir: modern yazar → önceki tarihçi → daha
   eski kaynak → birincil kanıt. Mümkün olduğunca zincirin başına
   in.
4. **Çok dilli araştırma** (Modül 26) — konu belirli bir dil/kültür
   alanına aitse, o dildeki terimlerle de ara; çeviri farklarını not
   et, orijinal ifadeyi koru.
5. **Arşiv / müze / maddi kanıt** (Modül 28) — mümkünse: eser,
   yazıt, sikke, arkeolojik kayıt, harita gibi metin-dışı kanıtları
   da ara (özellikle antik/erken dönem konularda önemli).
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
