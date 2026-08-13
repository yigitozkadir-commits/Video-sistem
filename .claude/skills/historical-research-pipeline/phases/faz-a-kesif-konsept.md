# FAZ A — Keşif & Konsept

**Kaynak modüller:** 01 (Deep Discovery), 02 (Historical Story Miner),
11 (Content Opportunity Engine)

**Girdi:** Kullanıcının verdiği konu / dönem / kişi / açık soru (geniş
veya dar olabilir).

**Çıktı:** `faz-a-concept.json` — bir veya birkaç **Concept Card**.

---

## A1 — Discovery (keşif)

Amaç: Konuyu ana akım anlatının ötesine taşımak; alternatif isimler,
ilişkili varlıklar, az bilinen yan konular bulmak.

Adımlar:

1. **Search expansion** — konunun alternatif adlarını, eski
   yazımlarını, farklı dillerdeki karşılıklarını üret (ör. "Mehmed
   II" → "Fatih Sultan Mehmed", "Muhammad II", dönemsel yazımlar).
2. Gerçek **WebSearch** ile 3-6 farklı sorguyla geniş tara: konunun
   kendisi, ilişkili kişiler/olaylar, akademik tartışma var mı,
   birincil kaynak izi var mı.
3. **Rabbit-hole/kaynakça takibi**: bulduğun sayfalardan/makalelerden
   referans verilen daha eski/az bilinen kaynaklara **WebFetch** ile
   bak — yeni aday konular ortaya çıkabilir.
4. Wikipedia/popüler kaynaklar başlangıç noktasıdır, **nihai kaynak
   değildir** — akademik/arşiv izine geçmeye çalış.
5. Kaynaklar arası çelişki gördüysen bunu not et — çelişki, keşif
   sinyalidir, gizlenmez.
6. "Signal sources" (YouTube, Reddit, forumlar) sadece **kamu
   ilgisini** ölçmek için kullanılabilir, tarihsel kanıt olarak asla
   kullanılmaz.

Çıktı: 3-8 arası "araştırmaya değer aday" (candidate), her biri kısa
gerekçeyle.

## A1b — Kapsam-Genişliği Kapısı

A1 taramasından sonra, konuyu Faz B'de **tek bir claim
decomposition ile makul şekilde kapsanabilir mi** diye değerlendir:

- Konu, tek bir merkezi soru + makul sayıda alt-soruya (B1)
  bölünebiliyor mu ("Marcello 1492'de neden kovuldu" gibi)?
- Yoksa konu, kendi başına onlarca ayrı araştırma dosyası gerektiren
  bir alan mı ("Osmanlı-Venedik ilişkileri" gibi — dönemler,
  olaylar, kişiler içeren bir şemsiye başlık)?

**Eşik:** Bir konu, makul bir B1 alt-soru ağacıyla (kabaca 3-8 alt
soru) kapsanamayacak kadar genişse, doğrudan Faz B'ye geçme. Bunun
yerine A3'te birden fazla dar candidate üret (şemsiye konuyu alt
konulara böl) ve **AskUserQuestion** ile kullanıcıya **"bu konu çok
geniş, hangi alt konuyla derinleşelim"** diye sor — bu, A3'ün zaten
yaptığı "birden fazla aday sunma" akışıyla aynı mekanizmayı kullanır,
sadece tetikleyici sebep farklıdır (kullanıcı tercihi değil, kapsam
kontrolü).

Dar/net bir soru zaten verilmişse bu adım anlık geçilir (tek
candidate, otomatik onay — bkz. Orkestrasyon notu).

## A2 — Story Mining (içerik konseptine dönüştürme)

Her aday için şu soruları cevapla:

- Bu malzemenin hangi yönü güçlü bir tarihsel **soru** etrafında
  kurulabilir?
- Kanıt potansiyeli var mı (birincil kaynak beklenebilir mi)?
- Doygunluk: Bu konu zaten çok mu işlenmiş, yoksa özgün mü?
- Anlatı gerilimi var mı (çelişki, paradoks, beklenmedik sonuç)?
- Araştırma riski nedir (kanıt bulma zorluğu)?

**Sınır:** Bu adımda senaryo, başlık veya thumbnail üretilmez —
sadece araştırılabilir "concept" tanımlanır.

## A3 — Opportunity Scoring

Fikir sınıflarına göre etiketle:

`forgotten_history | reinterpretation | historical_mystery |
evidence_contradiction | lost_source | revisionist_challenge |
unexpected_consequence | attribution_problem | chronological_anomaly |
myth_correction | academic_controversy | unresolved_question`

Skorlama ekseni (her biri high/medium/low):
`evidence_density, novelty, research_gap, counterintuitive_value,
narrative_tension, researchability`

**Temel kural:** Clickbait/merak değeri, araştırma değerinin yerine
geçemez — bir aday yalnızca "ilginç görünüyor" diye yüksek
puanlanmaz, altında gerçek kanıt potansiyeli olmalı.

## Çıktı şeması — `faz-a-concept.json`

```json
{
  "phase": "A",
  "input_summary": "kullanıcının orijinal isteğinin özeti",
  "candidates": [
    {
      "candidate_id": "CAND-01",
      "title": "kısa başlık",
      "central_question": "araştırılabilir tarihsel soru",
      "subject_type": "person | event | institution | place | concept | debate",
      "period": "",
      "geography": "",
      "opportunity_class": "myth_correction | ... (yukarıdaki listeden)",
      "scores": {
        "evidence_density": "high|medium|low",
        "novelty": "high|medium|low",
        "research_gap": "high|medium|low",
        "counterintuitive_value": "high|medium|low",
        "narrative_tension": "high|medium|low",
        "researchability": "high|medium|low"
      },
      "known_sources_seen": ["url veya kaynak adı"],
      "research_risk": "low | medium | high — kısa açıklama",
      "recommended": true
    }
  ],
  "winning_candidate_id": "CAND-01 (kullanıcı onayladıysa)"
}
```

## Orkestrasyon notu

Birden fazla güçlü aday varsa, hepsini kısa listelenmiş şekilde
kullanıcıya sun (**AskUserQuestion** ile tekli seçim sorusu olarak
sunulabilir) ve hangisiyle Faz B'ye devam edileceğini sor. Girdi zaten
tek ve dar bir soru ise (kullanıcı belirli bir iddiayı sormuşsa), tek
bir Concept Card üretip otomatik olarak `winning_candidate_id` ata ve
kullanıcıya sormadan devam et.
