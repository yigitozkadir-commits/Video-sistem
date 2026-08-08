# Ortak Şema Sözlüğü

Tüm fazlar aşağıdaki ortak kayıt tiplerini kullanır. Bir faz kendi
şemasını icat etmez; burada tanımlı alanları genişletebilir ama
temel alan adlarını değiştirmez. Bu, orijinal 29 modülün her birinin
kendi "Card" formatını icat etmesinden kaynaklanan tutarsızlığı
ortadan kaldırmak için eklenmiştir.

## 1. Epistemik durum sözlüğü (her yerde aynı terimler kullanılır)

İddia / bilgi durumu için **sadece** şu etiketler kullanılır:

- `ESTABLISHED` — çoklu bağımsız kaynak + birincil kanıt destekliyor
- `STRONGLY_SUPPORTED` — güçlü kanıt var, küçük belirsizlikler var
- `PROBABLE` — kanıt ağırlıklı olarak destekliyor ama boşluklar var
- `PLAUSIBLE` — mantıklı ama doğrudan kanıt zayıf/dolaylı
- `CONTESTED` — akademik camiada gerçek bir anlaşmazlık var
- `UNKNOWN` — kanıt yetersiz, karar verilemiyor
- `UNSUPPORTED` — iddia var ama kanıt yok
- `REJECTED` — kanıtla çürütülmüş

Ayrıca "bilinmeyen" kategorisi kendi içinde ayrıştırılır (Modül 10):

- `KNOWN`
- `SUPPORTED_INFERENCE`
- `OPEN_QUESTION`
- `GENUINE_MYSTERY`
- `SOURCE_GAP`
- `CONTROVERSY`
- `HYPOTHESIS`
- `SPECULATION`
- `MYTH`
- `FALSE_MYSTERY`

**Kritik kural:** `SPECULATION` ve `MYTH` hiçbir zaman `FACT` gibi
sunulmaz; her ikisi de açıkça etiketlenir.

## 2. Claim (İddia) kaydı

```json
{
  "claim_id": "C-0001",
  "text": "İddianın tam ve tek anlamlı ifadesi",
  "type": "fact | inference | interpretation | speculation",
  "importance": "core | supporting | peripheral",
  "supporting_evidence": ["EV-0001", "EV-0002"],
  "counter_evidence": ["EV-0007"],
  "sources": ["SRC-0001", "SRC-0002"],
  "independent_sources_count": 2,
  "primary_evidence_used": true,
  "historiographical_status": "consensus | debate | minority_view",
  "confidence": "ESTABLISHED | STRONGLY_SUPPORTED | PROBABLE | PLAUSIBLE | CONTESTED | UNKNOWN | UNSUPPORTED | REJECTED",
  "verification_status": "unverified | pending | confirmed | contested | rejected",
  "confidence_history": [
    {"phase": "B|C|D", "value": "epistemik durum sözlüğünden", "reason": "değişimin kısa gerekçesi"}
  ],
  "notes": "gerekirse kısa not"
}
```

**`confidence_history` kuralı:** `confidence` alanı her değiştiğinde
(B'deki taslak → C1'de doğrulanmış verdict → D2'de paketlenmiş son
hal), eski değer silinmez — `confidence_history`'ye yeni bir kayıt
**eklenir**, mevcut kayıtlar korunur. Böylece "bu iddia neden
STRONGLY_SUPPORTED'dan PROBABLE'a düştü" sorusunun cevabı kaybolmaz.
İlk taslak (Faz B) da dahil, en az bir giriş her zaman olmalı.

## 3. Evidence (Kanıt) kaydı

```json
{
  "evidence_id": "EV-0001",
  "claim_id": "C-0001",
  "description": "Kanıtın ne olduğu",
  "source_id": "SRC-0001",
  "evidence_type": "primary | near-contemporary | secondary | tertiary | derivative | oral_tradition | archaeological | material | epigraphic | numismatic | administrative",
  "supports_or_contradicts": "supports | contradicts | qualifies",
  "strength": "strong | moderate | weak",
  "notes": ""
}
```

## 4. Source (Kaynak) kaydı

```json
{
  "source_id": "SRC-0001",
  "title": "",
  "author_or_creator": "",
  "date": "",
  "language": "",
  "url_or_locator": "",
  "type": "primary | secondary | tertiary | archival | academic | web | material",
  "temporal_proximity": "contemporary | near-contemporary | later | modern",
  "independence_group": "grup kimliği — aynı gruptaki kaynaklar birbirini bağımsız doğrulamaz",
  "bias_indicators": [],
  "translation_risk": "none | low | medium | high",
  "authenticity_risk": "none | low | medium | high",
  "reliability": "high | medium | low | unverified",
  "linked_claims": ["C-0001"]
}
```

## 5. Unknown / Anomaly kaydı

```json
{
  "unknown_id": "U-0001",
  "question": "",
  "known": "",
  "unknown": "",
  "category": "KNOWN | SUPPORTED_INFERENCE | OPEN_QUESTION | GENUINE_MYSTERY | SOURCE_GAP | CONTROVERSY | HYPOTHESIS | SPECULATION | MYTH | FALSE_MYSTERY",
  "competing_explanations": [],
  "researchability": "high | medium | low",
  "priority": "high | medium | low"
}
```

## 6. Angle / Hook kaydı (yalnızca Faz E)

```json
{
  "angle_id": "A-01",
  "central_question": "",
  "core_tension": "",
  "evidence_anchor": ["C-0001"],
  "originality": "high | medium | low",
  "scholarly_strength": "high | medium | low",
  "uncertainty": "high | medium | low"
}
```

```json
{
  "hook_id": "H-01",
  "question": "",
  "supporting_evidence": ["C-0001"],
  "curiosity_mechanism": "contradiction | mystery | reversal | reveal | stakes",
  "risk_of_exaggeration": "none | low | medium | high",
  "confidence": "aynı epistemik sözlük"
}
```

## 7. ID kuralları

- Claim: `C-000n`
- Evidence: `EV-000n`
- Source: `SRC-000n`
- Unknown: `U-000n`
- Angle: `A-0n`
- Hook: `H-0n`

ID'ler proje boyunca **kararlıdır** — bir sonraki fazda değişmez,
sadece yeni alanlar eklenir. Bu sayede Faz E'deki paket, Faz B'deki
ham veriye kadar geriye izlenebilir (traceability requirement).
