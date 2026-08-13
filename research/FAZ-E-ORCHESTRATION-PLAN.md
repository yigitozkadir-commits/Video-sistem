# Faz E Orkestrasyon Planı — 18 Bölüm (12+6)

## Durum

**Faz D Tamamlanan Sections:**
- ✅ **12 Bölüm** (4 Cluster): A-LAYER, BOZ-01, KURG, KÜR-ARAZ, BOZ-02A, MİT, ESKİ-HALK, BÜYÜK-DEV, MANAS, MÜZİK-SESLER, AŞARIŞILIK, RYSKULOV
- 🔄 **2 Bölüm** (6th Cluster): YAŞAYAN MİRAS, HAFIZANIN SINAVI — Faz D çalışıyor

**Faz E Hazır Olma:** 2 bölüm Faz D tamamlandığında → Tüm 18 bölüm için Faz E başlatılabilir

---

## Faz E Görevler (E1-E4)

### **E1: Angle Selection (Açı Seçimi)**

Her bölüm için "tarihsel açı" seç:

**FOUNDATION Cluster:**
- A-LAYER: "İnsanlar neden çoğunlukla 80-100 yıl ötesini unutur?"
- BOZ-01: "Güneydoğu Rusya 4000 yıl kuraklaşırken, kültürler nasıl göçer?"
- KURG: "Gimbutas'ın kurgan hipotezi neden eski kaldı? (2015+ DNA bulguları)"
- KÜR-ARAZ: "Nehir bölgelerinin iklim değişikliğine dayanıklılığı"
- BOZ-02A: "Mitoloji nerede kesin harita veri haline geliyor?"
- MİT: "Tengriizm: İslam-öncesi totemizmden modern inanç sistemi olarak evrim"

**HISTORY Cluster:**
- ESKİ-HALK: "Bozkırın eski halkları neden kayıp tarihe düştü?"
- BÜYÜK-DEV: "Göktürkler kimdir? (Hun halefleri değil, eş zamanlı paralel devlet)"

**CULTURE Cluster:**
- MANAS: "Bir efsane 1M+ satır kadar uzun olabilir mi? (Oral geleneğin uçsuz bucaksızlığı)"
- MÜZİK-SESLER: "Eski enstrümanlar 1000 yıl aynı kalabilir mi?"

**OTTOMAN Cluster:**
- AŞARIŞILIK: "Ryskulov'un teoloji mektepleri: Tarih vs. mitle çelişki"
- RYSKULOV: "Sovyet 1937: Bir el yazmasının kaderini değiştiren tarih"

**6th Cluster:**
- YAŞAYAN MİRAS: "UNESCO tanırken kültür niye yenilenir? (Kurumsal validasyon etkisi)"
- HAFIZANIN SINAVI: "Cyrillic alfabe değiştirilmesi = Kimlik değiştirilmesi mi?"

---

### **E2: Hook Discovery (Kopya/Başlık Araştırması)**

Her açı için **videonun en ilginç claim'i** bul:

**Örnek E2 Outputs:**

| Bölüm | Açı | Hook (Video başlığı için) | Claim | Why It Hooks |
|-------|-----|---|---|---|
| BOZ-01 | Göçün iklimi | "4000 Yıl Kuraklaşan Bozkırda İnsanlar Nasıl Yaşadı?" | Çölleri belirtmek İllasyon değil, iklim mühendisliği | Unexpected framing: nature as engineer |
| KURG | Gimbutas paradigması | "1950 Hipotezi vs. 2015 DNA: Bir Arkeoloji Devrimi" | Kurgan hypothesis now superseded by aDNA | Paradigm collapse is dramatic |
| MANAS | Oral tradition scale | "530 bin Satrı: İnsanlar Bir Hikayeyi Kaç Gece Anlatabilir?" | Manas line variants (50K - 530K+) | Abundance paradox hooks curiosity |
| HAFIZANIN SINAVI | Alfabe politics | "Bir Harf Değişimi Bir Medeniyeti Nasıl Değiştirir?" | Cyrillic imposition (1938-1941) | Personal identity tied to writing system |

---

### **E3: Package Format**

**Output per Section:**

```
research/<section>/faz-e-package.json
{
  "phase": "E",
  "section": "<name>",
  "items_range": "<range>",
  "angle": "<E1 selection>",
  "hook": "<E2 discovery>",
  "claims": [ ... ],  // From Faz D
  "historiography": { ... },  // From Faz D
  "production_readiness": {
    "status": "READY|CONDITIONAL",
    "qualifications": [ ... ]
  },
  "bibliography": [ ... ],  // All sources from Faz B+C+D
  "readiness_verdict": "HUMAN_DECISION_REQUIRED"  // User must finalize
}
```

---

### **E4: Archive & Versioning**

```
research/FAZ-E-FINAL-PACKAGES/
  ├── faz-e-package-1-a-layer.json
  ├── faz-e-package-2-boz-01.json
  ├── ... (18 packages total)
  ├── FAZ-E-MASTER-MANIFEST.json  // All 18 sections listed + metadata
  └── DELIVERY-READY-2026-08-09.md
```

---

## Faz E Agent Orchesration

**Single Master Agent** will:
1. Read all 12+2 Faz D master dossiers
2. For each section: execute E1 (angle) + E2 (hook)
3. Generate faz-e-package.json per section
4. Create FAZ-E-MASTER-MANIFEST
5. Report: "18/18 packages ready for user review + gate verdicts"

---

## Human Gate — Faz E Verdicts

**User Decision Required (Per Section):**

1. **Angle**: Kabul et mi? (User can edit/refine)
2. **Hook**: Prodüksiyon için uygun mu?
3. **Production Readiness**: READY mi, CONDITIONAL mi?
4. **Final Verdict**: Bu bölüm video üretime giriyor mu?

---

## Timeline

- 🔄 6th Cluster Faz D: ~1 saat (şu anda çalışıyor)
- ⏳ Faz E Master Agent: ~1-2 saat (18 section)
- 👤 User Review + Gate Verdicts: ~1-2 saat

**Total: ~4-5 saat → Tüm 18 bölüm production-ready package**

---

## Next Step After Faz E

Once all 18 packages approved:
- Bridge to **PRJ-*-* projects** (per CLAUDE.md M23 §4)
- Each section becomes input for video production (M05/M17 pipeline)
