# FAZ C — Doğrulama & Analiz

**Kaynak modüller:** 04 (Adversarial Review), 09 (Historiography), 10
(Unknowns & Anomalies), 14 (Cross-Verification), 16 (Source Quality
Ranking), 17 (Claim–Evidence Graph)

**Girdi:** `faz-b-dossier.json`

**Çıktı:** `faz-c-verification.json`

---

## C1 — Adversarial Verification (Modül 04 + 14)

Temel prensip: **"Bulduğun kanıtın gerçekten iddiayı desteklediğini
kanıtla."** Her `core` ve `supporting` önem seviyesindeki claim için
şu saldırı sorularını sor:

- Kaynak yanlış olabilir mi?
- Çeviri hatalı olabilir mi?
- Tarih yanlış olabilir mi?
- Kaynaklar gerçekten birbirinden bağımsız mı, yoksa aynı kökten mi
  geliyor (`independence_group` kontrolü)?
- Nedensellik ters kurulmuş olabilir mi?
- Eksik kanıt sonucu değiştirir mi?
- Daha basit / alternatif bir açıklama var mı?
- Hangi kanıt bu iddiayı çürütürdü — böyle bir kanıt arandı mı?

Gerekirse ek **WebSearch** ile karşı kanıt/çürütme arayışını
derinleştir (negative search).

Her claim için zincir doldurulur:

```
CLAIM → SUPPORTING EVIDENCE → STRONGEST COUNTER-EVIDENCE →
INDEPENDENT CONFIRMATION → ALTERNATIVE EXPLANATION →
REMAINING WEAKNESS → CURRENT VERDICT
```

Verdict değerleri: `confirmed | strongly_supported |
supported_but_qualified | contested | weak | unresolved | rejected`

Bu verdict, claim'in `confidence` alanını **günceller** (Faz B'deki
taslak değeri değil, artık doğrulanmış değeri). Eski değeri silme —
`confidence_history`'ye yeni bir kayıt ekle: `{"phase": "C", "value":
"<yeni değer>", "reason": "<neden değişti — hangi karşı kanıt/
bağımsızlık sorunu vb.>"}`.

## C2 — Historiography & Competing Interpretations (Modül 09)

Tarihsel **gerçek** ile tarihsel **yorum**u ayır:

1. Konuyla ilgili farklı tarihçi/ekol yorumlarını bul.
2. Her yorumun hangi kanıta dayandığını çıkar.
3. Gerçek akademik anlaşmazlıkları (`historiographical_status:
   debate`) sahte/yapay anlaşmazlıklardan ayıkla.
4. Azınlık görüşünü otomatik yanlış saymadan, ama sadece azınlık
   olduğu için de otomatik geçerli saymadan kaydet.
5. Eski yorumların yeni kanıtlarla nasıl değiştiğini not et.
6. **Perspektif çeşitliliği kontrolü** — özellikle milliyetçi/
   çatışmalı tarih anlatılarında (sınır ihtilafları, soykırım
   tartışmaları, etnik/dini çatışmalar vb.) kullanılan kaynakların
   **milliyet/kurum/taraf dağılımını** kontrol et. Bu,
   `independence_group` (aynı kökten mi geliyor) kontrolünden
   **ayrı** bir kontroldür — bağımsız ama tek taraflı kaynaklar da
   olabilir. İhtilaflı bir konuda kaynakların büyük çoğunluğu tek
   bir tarafın/ekolün tarihçilerinden geliyorsa bunu
   `perspective_diversity` alanıyla işaretle: `balanced | skewed |
   single_perspective_only`. `skewed` veya `single_perspective_only`
   ise, karşı tarafın/diğer tarafların akademik literatüründe ayrıca
   arama yapılmalı (mümkünse çok dilli arama, bkz. Faz B3.4) ve
   sonuç ne olursa olsun (bulundu/bulunamadı) not edilmelidir.

## C3 — Unknowns & Anomalies (Modül 10)

Gerçekten bilinmeyen / açıklanamayan / kaynak bakımından eksik
noktaları bul (`reference/sema.md § 5` şemasıyla). Kritik kontroller:

- "Herkes söylüyor" iddiasının **ilk kaynağını** ara.
- İkincil kaynakların birbirinden gerçekten bağımsız olup olmadığını
  kontrol et.
- Kaynak yokluğunu, olayın yokluğuyla karıştırma.
- Kanıtlanmamış bir motivasyonu olgu gibi yazma.
- Popüler "gizem" ile akademik bilinmezliği ayır (`FALSE_MYSTERY` vs
  `GENUINE_MYSTERY`).

## C4 — Claim–Evidence Graph (Modül 17)

Claim/Evidence/Source/Interpretation arasındaki ilişkileri açık
ilişki tipleriyle işaretle:
`SUPPORTS | CONTRADICTS | QUALIFIES | DEPENDS_ON | DERIVED_FROM |
CORROBORATES | DISPUTES | INTERPRETS | REFUTES | UNKNOWN_RELATION`

**Weak-link analizi** — her zincirde şunları işaretle:
- En zayıf kanıt halkası
- Tek kaynağa bağımlı iddialar (`orphan` risk)
- Bağımsız doğrulaması olmayan bağlantılar
- Varsayıma dayalı inference zincirleri
- Çözülmemiş çelişkiler

## C5 — Source Quality & Provenance (Modül 16)

Her kaynağı tek bir puanla değil, ayrı eksenlerde değerlendir:
`authenticity, temporal_proximity, independence, corroboration,
translation_risk, authenticity_risk`. Sonuçları
`sources[].reliability` alanına yaz (`high|medium|low|unverified`).

## Çıktı şeması — `faz-c-verification.json`

```json
{
  "phase": "C",
  "claims_verified": [
    {
      "claim_id": "C-0001",
      "verdict": "confirmed|strongly_supported|supported_but_qualified|contested|weak|unresolved|rejected",
      "strongest_counter_evidence": "",
      "independent_confirmation": true,
      "alternative_explanation": "",
      "remaining_weakness": "",
      "updated_confidence": "ESTABLISHED|..."
    }
  ],
  "historiography": [
    {
      "topic": "",
      "interpretations": [
        {"scholar_or_school": "", "position": "", "based_on": "", "status": "consensus|debate|minority_view"}
      ],
      "perspective_diversity": "balanced|skewed|single_perspective_only",
      "perspective_diversity_notes": "milliyet/kurum/taraf dağılımı — hangi taraf(lar) az/hiç temsil edilmiyor, karşı taraf literatüründe arama yapıldı mı"
    }
  ],
  "unknowns": [ /* reference/sema.md § 5 */ ],
  "claim_evidence_graph_summary": {
    "orphan_claims": ["C-000x"],
    "weak_links": ["C-000x — açıklama"],
    "unresolved_contradictions": ["C-000x vs C-000y — açıklama"]
  },
  "source_reliability_updates": [
    {"source_id": "SRC-0001", "reliability": "high|medium|low|unverified", "notes": ""}
  ]
}
```
