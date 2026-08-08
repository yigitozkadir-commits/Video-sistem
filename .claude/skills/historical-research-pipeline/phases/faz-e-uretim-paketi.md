# FAZ E — Üretim Paketi

**Kaynak modüller:** 21 (Content Angle Selection), 22 (Hook
Discovery), 23 (Research Package Formatter), 24 (Final Archive &
Version Control), 29 (Research Automation Orchestrator — routing
mantığı)

**Girdi:** `faz-d-master-dossier.json` (yalnızca `readiness_state`
READY/CONDITIONAL/HIGH_CONFIDENCE_READY ise)

**Çıktı:** `faz-e-package.json` + `faz-e-package.md` (nihai,
kullanıcıya teslim edilen dosyalar)

Bu faz hâlâ **senaryo, başlık veya thumbnail üretmez.** Pipeline'ın
son noktası, video/içerik üretim sürecine devredilebilecek temiz bir
araştırma paketidir.

---

## E1 — Content Angle Selection (Modül 21)

Onaylanmış araştırmadan en güçlü içerik açısını seç. Aday açı
kaynakları:
`central_question | contradiction | mystery | revisionist |
evidence_discovery | person_or_event | myth_correction |
historiographical_debate | unexpected_consequence`

Her aday açı `reference/sema.md § 6` (Angle) şemasıyla puanlanır.
Seçim ilkesi: güçlü kanıt + gerçek tarihsel soru + anlamlı gerilim +
araştırma derinliği — **sadece merak değeri yeterli değildir.**

Reddedilen açıları da kısaca gerekçesiyle listele (şeffaflık için).

## E2 — Hook & Question Discovery (Modül 22)

Seçilen açıdan doğal olarak çıkan güçlü soruları bul
(`reference/sema.md § 6`, Hook). Hook sınıfları:
`what_really_happened | why_did_x_happen | who_was_responsible |
evidence_contradicts_story | what_disappeared |
historians_changed_minds | what_primary_source_actually_says |
what_remains_unknown`

**Güvenlik kuralı:** Bir hook, araştırmanın kanıtlamadığı bir şeyi
vaat edemez. Her hook'un `supporting_evidence` alanı gerçek claim
ID'lerine bağlı olmalı; abartı riski varsa `risk_of_exaggeration`
alanında açıkça işaretlenmeli.

## E3 — Research Package Formatter (Modül 23)

Master araştırmayı, video üretim iş akışına aktarılabilecek temiz,
modüler pakete dönüştür. Paket yapısı:

```
PROJECT
├── research_question
├── winning_angle
├── hook_candidates
├── claims
├── evidence
├── primary_sources
├── secondary_sources
├── chronology
├── historiography
├── competing_interpretations
├── anomalies
├── unknowns
├── contradictions
├── confidence
├── research_gaps
└── bibliography
```

Her veri nesnesi kararlı ID, tip, metin, kaynak/kanıt bağlantıları,
güven seviyesi ve durum içerir (bkz. `reference/sema.md`).

**Kopya/alıntı disiplini:** `evidence[].description` ve claim
metinleri **parafraz** olmalı — akademik kaynaktan doğrudan uzun
alıntı içermemeli. 15 kelimeyi aşan doğrudan alıntı yapılmaz; bir
kaynaktan en fazla bir kısa (15 kelime altı) doğrudan alıntı
alınabilir, gerisi kendi cümlelerinle özetlenir. Bu, Claude'un genel
telif kısıtının bir tekrarı değil, E3'e özel bir hatırlatmadır —
Evidence açıklamaları kaynak metnin yapısını/cümle sırasını da
birebir izlememeli, gerçek bir yeniden ifade olmalı.

## E4 — Archive & Version Control (Modül 24)

Nihai teslimatta şunlar korunur (kaybolmaması için):

- Kullanılan tüm arama sorguları (kısa liste, Faz B/C boyunca
  atılanlar)
- Kaynak listesi (tam Source Registry)
- Reddedilen hipotezler / reddedilen kaynaklar (varsa, neden
  reddedildiğiyle)
- Faz D'deki audit sonucu ve readiness kararı
- Versiyon durumu: `DRAFT|RESEARCHING|VERIFIED|AUDITED|READY|
  SUPERSEDED|ARCHIVED` — bu paket için uygun olanı işaretle

**Reproducibility ilkesi:** Paketteki her önemli sonuç, geriye doğru
şu zincirle izlenebilmelidir: `Claim → Evidence → Source → Search
query / provenance`. Bu yüzden E3'teki her claim'in evidence/source
bağlantıları eksiksiz olmalı.

### Teslim Sözleşmesi (Handoff Contract)

Bu pipeline senaryo/video metni yazımını kapsamıyor (bkz. SKILL.md
"Çalışma prensibi" madde 6) — paket bir sonraki aşamaya (senaryo
yazarı / başka bir skill veya süreç) devredilir. O devrin sessizce
format uyumsuzluğuna düşmemesi için, `faz-e-package.json`'ın **en az
şunları garanti ettiği** kabul edilir; hiçbiri boş/eksik bırakılamaz
(veri yoksa bile alan `[]` veya `null` olarak açıkça bulunur,
sessizce silinmez):

1. `winning_angle` ve en az bir `hook_candidates` girişi
2. Her `claims` girişinin `confidence` + `confidence_history` +
   `sources` dolu olması (boş bir claim paketlenmez)
3. `sources.primary` ve `sources.secondary` ayrı ayrı listelenmiş
4. `contradictions` ve `unknowns` — boşsa bile boş liste olarak var
5. `readiness_summary.state` — alıcı sürecin paketi ne düzeyde
   güvenle kullanabileceğini bilmesi için (`CONDITIONAL` ise
   `blockers`/koşullar da görünür olmalı)
6. `bibliography` — insan-okunabilir tam liste

`faz-e-package.md` insan-okunabilir raporu bu garantiyi tekrar
etmez, sadece okunabilir özetini sunar; asıl sözleşme
`faz-e-package.json` şemasınadır.

## Çıktı şeması — `faz-e-package.json`

```json
{
  "phase": "E",
  "project_title": "",
  "research_question": "",
  "winning_angle": { /* reference/sema.md § 6 Angle */ },
  "rejected_angles": [{"angle_id": "", "reason": ""}],
  "hook_candidates": [ /* § 6 Hook, ranked */ ],
  "claims": [ /* final, § 2 */ ],
  "evidence": [ /* final, § 3 */ ],
  "sources": {
    "primary": [ /* § 4 */ ],
    "secondary": [ /* § 4 */ ]
  },
  "chronology": [ /* Faz D timeline */ ],
  "historiography": [ /* Faz C2 */ ],
  "unknowns": [ /* § 5 */ ],
  "contradictions": [ /* Faz C4 unresolved */ ],
  "confidence_map": {"C-0001": "ESTABLISHED"},
  "research_gaps": [ /* Faz D gaps */ ],
  "bibliography": ["tam kaynakça listesi, insan-okunabilir"],
  "version_state": "READY",
  "readiness_summary": { "state": "", "blockers": [] }
}
```

## İnsan-okunabilir çıktı — `faz-e-package.md`

JSON paketinin yanı sıra, aynı içeriği **düz, okunabilir Markdown**
raporu olarak da üret (bu, kullanıcının doğrudan okuyacağı dosyadır):

1. Araştırma sorusu ve seçilen açı
2. Hook adayları (sıralı)
3. Ana iddialar ve güven seviyeleri (tablo)
4. Kronoloji özeti
5. Tarih yazımı / farklı yorumlar
6. Bilinmeyenler ve gizemler
7. Çözülmemiş çelişkiler
8. Araştırma boşlukları (gelecekte araştırılabilir)
9. Kaynakça

## Orkestrasyon notu — teslimat

1. **Write** ile hem `.json` hem `.md` dosyasını
   `research/<proje-slug>/` altına yaz (bu deponun `projects/`
   dizininin kardeşi — bkz. SKILL.md "Dosya düzeni").
2. `faz-e-package.json`'ı yazmadan önce (veya yazdıktan hemen sonra)
   `schemas/research_package.schema.json`'a karşı doğrula — elde
   `jsonschema` varsa doğrudan `jsonschema.validate()`, yoksa en
   azından "Teslim Sözleşmesi" bölümündeki 6 maddeyi elle kontrol et.
   Bu stüdyonun 1. yasası ("contract over prose") burada da geçerli:
   şemaya uymayan bir paket teslim edilmez, önce düzeltilir.
3. **SendUserFile** ile ikisini birden kullanıcıya sun
   (`status: "proactive"`, `display: "attach"`).
4. Kısa bir kapanış notu ver: readiness durumu, kaç claim, kaç
   kaynak, varsa açık gaplar — ama uzun bir postamble yazma.
5. **Opsiyonel köprü — projeye dönüştürme.** Paket teslim edildikten
   sonra, kullanıcı bunu yeni bir `PRJ-*` projesinin kaynağı yapmak
   isterse (kendiliğinden yapma, sor veya kullanıcı zaten istemiş
   olsun), `bible/Module_23_Historical_Research_Pipeline.md` §4'teki
   adımları uygula: `faz-e-package.md`'yi yeni projenin `input/`
   dizinine kopyala, sha256 hesapla, `project.json.source` alanını
   doldur, `rights.source_basis: "owned"` ata,
   `rights.evidence_ref`'i paketin `bibliography` alanına
   bağla. Bundan sonrası bu stüdyonun normal proje scaffold akışıdır
   (`scripts/scaffold_<proje>_project.py` deseni) — bu skill'in
   kapsamı dışında.
