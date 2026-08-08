# FAZ C — Doğrulama & Analiz

**Kaynak modüller:** 04 (Adversarial Review), 09 (Historiography), 10
(Unknowns & Anomalies), 14 (Cross-Verification), 16 (Source Quality
Ranking), 17 (Claim–Evidence Graph)

**Girdi:** `faz-b-dossier.json`

**Çıktı:** `faz-c-verification.json`

---

## C1 — Adversarial Verification / "Red Team Mode" (Modül 04 + 14)

Temel prensip: **"Bulduğun kanıtın gerçekten iddiayı desteklediğini
kanıtla."** Bu adım boyunca **Red Team Mode**'dasın — amacın claim'i
savunmak değil, çürütmeye çalışmak. Her `core` ve `supporting` önem
seviyesindeki claim için önce temel saldırı sorularını sor:

- Kaynak yanlış olabilir mi?
- Çeviri hatalı olabilir mi?
- Tarih yanlış olabilir mi?
- Kaynaklar gerçekten birbirinden bağımsız mı, yoksa aynı kökten mi
  geliyor (`independence_group` kontrolü)?
- Nedensellik ters kurulmuş olabilir mi?
- Eksik kanıt sonucu değiştirir mi?
- Daha basit / alternatif bir açıklama var mı?
- Hangi kanıt bu iddiayı çürütürdü — böyle bir kanıt arandı mı?

Sonra, aşağıdaki **adlandırılmış dedektörleri** sırayla uygula (her biri
belirli, tekrar eden bir hata sınıfını hedefler — genel "dikkatli ol"
uyarısından farklı olarak, spesifik ve kontrol edilebilir):

- **Citation Hallucination Detector** — Faz B3.2'de zaten uygulanmış
  olmalı (bkz. `phases/faz-b-derin-arastirma.md`); burada, o kontrolden
  geçmemiş (`CITATION_UNVERIFIED`) hiçbir atfın `core`/`supporting`
  claim'e sessizce dayanak yapılmadığını doğrula.
- **False Precision Detector** — bir tahminin kesin bir rakam gibi
  sunulup sunulmadığını kontrol et (ör. nüfus/kayıp/bütçe rakamları).
  Kaynak "yaklaşık", "tahminen" diyorsa ama claim metni kesin bir sayı
  yazıyorsa, `ESTIMATE_PRESENTED_AS_EXACT` ile işaretle. **Bu stüdyoda
  gerçek bir karşılığı var**: `bible/Module_12` ve
  `scripts/pre_render_checklist*.py`'nin uzun-heceli-sayı kontrolü,
  tam olarak böyle bir rakamın (SC-001 nüfus figürü) yanlış telaffuz
  edilmesini üretim sonunda yakalamıştı — bu dedektör aynı sınıf hatayı
  üretimden önce, araştırma aşamasında yakalar.
- **Anachronism Checklist** — somut kontrol listesi: kurum henüz
  kurulmamışken var gibi anlatılıyor mu, unvan henüz kullanımda değilken
  kullanılıyor mu, ülke o isimle henüz yokken o isimle anılıyor mu,
  sınırlar geriye izdüşürülüyor mu (retrojected borders), etnik/millî
  kimlik döneme geriye izdüşürülüyor mu, modern ekonomik kavramlar
  (ör. "GSYİH", "enflasyon") pre-modern bir bağlama geriye izdüşürülüyor
  mu.
- **Nedensellik 4-eksen ayrıştırması + Karşı-olgusal (Counterfactual)
  Test** — herhangi bir nedensel iddia için `reference/sema.md § 8`'in
  `causal_reasoning` dört eksenini (temporal_relationship / correlation
  / mechanism / causal_evidence) ayrı ayrı değerlendir, sonra
  `counterfactual_test` (HIGH/MEDIUM/LOW/UNKNOWN) ile "A olmasaydı B
  yine de olur muydu" sorusunu sor. **Bilgi Kısıtı ilkesi**: aktörün
  kararını yalnızca o an bildiklerine göre değerlendir, sonradan
  öğrenilene göre değil.
- **Cherry-Picking Detector** — kanıt oranını raporla (ör. "10
  kaynaktan 8'i A'yı destekliyor ama sadece B alıntılanmış") ve bir
  risk seviyesi (`none|low|medium|high`) ata.
- **Circular Evidence Detector** — `APPARENT_EVIDENCE_COUNT` (kaç
  kaynak aynı şeyi söylüyor gibi görünüyor) ile
  `INDEPENDENT_EVIDENCE_COUNT`'u (kaç tanesi gerçekten bağımsız kökten
  geliyor) ayrı ayrı say — bunlar sıkça farklıdır.
- **Claim Mutation Detection** — bir iddia yeniden aktarıldıkça
  ifadesinin nasıl kaydığını izle (ör. "muhtemelen X" → "X" → "kesinlikle
  X" zinciri gibi) — bu, `independence_group` kontrolünden ayrı bir
  kontroldür: kaynaklar bağımsız olsa bile, hepsi aynı mutasyona uğramış
  bir ifadeyi tekrarlıyor olabilir.
- **EVIDENCE_INFLATION bayrağı** — art arda claim rafine edilirken
  (Faz B taslağı → C doğrulaması → D paketlemesi), son halin orijinal
  kanıttan daha güçlü bir iddiaya dönüşüp dönüşmediğini kontrol et; öyle
  ise `EVIDENCE_INFLATION` ile işaretle ve claim metnini kanıtla
  eşleşecek şekilde geri çek.

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
   debate`) sahte/yapay anlaşmazlıklardan ayıkla:
   - **Interpretive Leap Detector** — bir tarihçinin kanıttan
     sonucuna giden mantık zincirinde atlanmış bir adım var mı? Varsa,
     o yorumu `based_on` alanında bu boşluğu açıkça belirterek kaydet.
   - **False Disagreement Filter** — iki tarihçinin "anlaşmazlığı"
     gerçek bir kanıt/yorum farkı mı, yoksa sadece terminolojik bir
     örtüşme mi (aynı şeyi farklı kelimelerle mi söylüyorlar)? Sahte
     anlaşmazlık ise `status: "debate"` yerine bunu notlarda belirt.
4. Azınlık görüşünü otomatik yanlış saymadan, ama sadece azınlık
   olduğu için de otomatik geçerli saymadan kaydet. Görüşü şu ölçekte
   sınıflandır (`fringe_scale`): `ACADEMIC_MINORITY | ACADEMIC_FRINGE |
   NON_ACADEMIC_CLAIM | UNSUPPORTED_CLAIM | PSEUDO_HISTORICAL_CLAIM` —
   bu ölçek, "azınlık görüşü" ile "sahte-tarih iddiası"nı birbirine
   karıştırmamak için var; ilk ikisi akademik camianın içinde, son
   üçü dışındadır.
5. Eski yorumların yeni kanıtlarla nasıl değiştiğini not et; değişimin
   büyüklüğünü `revision_impact` ile etiketle: `MINOR | MODERATE |
   MAJOR | PARADIGM_SHIFTING`.
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
   `perspective_diversity`'nin **hangi tür** önyargıdan kaynaklandığını
   da adlandır (`bias_types`, birden fazla olabilir): `national |
   political | ideological | colonial | postcolonial | class |
   institutional | source_availability | language`. `source_availability`
   ve `language` özellikle önemli — bazen "tek taraflı" görünen bir
   literatür, gerçek bir önyargıdan değil, sadece o dildeki/o arşivdeki
   kaynaklara erişimin daha kolay olmasından kaynaklanır; ikisi farklı
   düzeltmeler gerektirir (biri ek arama, diğeri ek eleştirel okuma).
   Hangi dillerin/arşivlerin tarandığını, hangilerinin
   **taranmadığını** da kısaca kaydet (`coverage_log`) — bu, "az
   temsil ediliyor" iddiasının kendisinin de denetlenebilir olmasını
   sağlar.

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
- **Historical Meme/Myth Detector** — "herkes söylüyor" izlenimi veren
  bir iddiayı geriye doğru izle: çoğu zaman tek bir eski/zayıf kaynağın
  çok-adımlı bir aktarım zincirinden (site → site → video platformu →
  sosyal medya) geçerek çoğaltılmış hali olduğu görülür. Zincir
  gerçekten tek bir köke iniyorsa, bunu `FALSE_MYSTERY`/`MYTH` olarak
  işaretle ve zinciri (`transmission_chain`, kısa liste) kaydet —
  **popülerlik, kanıt değildir.**

## C4 — Claim–Evidence Graph (Modül 17)

Claim/Evidence/Source/Interpretation arasındaki ilişkileri açık
ilişki tipleriyle işaretle:
`SUPPORTS | CONTRADICTS | QUALIFIES | DEPENDS_ON | DERIVED_FROM |
CORROBORATES | DISPUTES | INTERPRETS | REFUTES | UNKNOWN_RELATION`

Evidence↔Claim kenarları için, bu genel ilişki tiplerinin yanında daha
ince taneli bir **hizalanma gücü** de kaydedilebilir (opsiyonel,
`reference/sema.md § 3`'ün `alignment_strength` alanı):
`DIRECTLY_SUPPORTS | PARTIALLY_SUPPORTS | INDIRECTLY_SUPPORTS |
CONTEXT_ONLY | DOES_NOT_SUPPORT | CONTRADICTS` — ör. bir kanıt grafikte
`SUPPORTS` olarak bağlanmış olabilir ama gerçekte yalnızca
`CONTEXT_ONLY` (bağlam sağlıyor, iddiayı doğrudan kanıtlamıyor)
olabilir; bu ayrım claim'in gerçek gücünü daha doğru yansıtır.

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
      "updated_confidence": "ESTABLISHED|...",
      "red_team_flags": ["CITATION_UNVERIFIED | ESTIMATE_PRESENTED_AS_EXACT | ANACHRONISM | EVIDENCE_INFLATION | CLAIM_MUTATION_SUSPECTED — hangileri tetiklendiyse, boşsa []"],
      "apparent_vs_independent_evidence_count": {"apparent": 0, "independent": 0}
    }
  ],
  "causal_claims_verified": [
    {
      "claim_id": "C-0001",
      "causal_reasoning": { "temporal_relationship": "", "correlation": "", "mechanism": "", "causal_evidence": "" },
      "counterfactual_test": "HIGH|MEDIUM|LOW|UNKNOWN"
    }
  ],
  "historiography": [
    {
      "topic": "",
      "interpretations": [
        {"scholar_or_school": "", "position": "", "based_on": "", "status": "consensus|debate|minority_view", "fringe_scale": "ACADEMIC_MINORITY|ACADEMIC_FRINGE|NON_ACADEMIC_CLAIM|UNSUPPORTED_CLAIM|PSEUDO_HISTORICAL_CLAIM", "revision_impact": "MINOR|MODERATE|MAJOR|PARADIGM_SHIFTING"}
      ],
      "perspective_diversity": "balanced|skewed|single_perspective_only",
      "perspective_diversity_notes": "milliyet/kurum/taraf dağılımı — hangi taraf(lar) az/hiç temsil edilmiyor, karşı taraf literatüründe arama yapıldı mı",
      "bias_types": ["national|political|ideological|colonial|postcolonial|class|institutional|source_availability|language"],
      "coverage_log": "hangi diller/arşivler tarandı, hangileri taranmadı"
    }
  ],
  "unknowns": [ /* reference/sema.md § 5, FALSE_MYSTERY girişleri için transmission_chain notu eklenebilir */ ],
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
