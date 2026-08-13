# Items 1-100 Araştırma Planı

**Başlangıç tarihi**: 2026-08-09  
**Amaç**: İçerik Backlog maddeleri 1-100 için Faz A konsept kartlarını araştırarak bölüm-başına (section-wise) temel araştırma çerçevesini oluşturmak. Her bölüm uzun video veya konsolide short serisi için bir araştırma temelini oluşturacak.

## Bölüm Gruplandırması

| Bölüm ID | Adı | İtem Range | Adet | Amaç | Tier | İlgili Uzun Video? |
|---|---|---|---|---|---|---|
| A-LAYER | A KATMANI — MERAK VE HAFIZA | 1-30 | 30 | Studio'nun meta-katmanı: kültürel bellek, ortak hafıza, kimlik — neden araştırıyoruz | short_new | Foundation (tüm videolara altyapı) |
| BOZ-01 | BÖLÜM 1 — BOZKIRIN DOĞUŞU | 31-60 | 30 | Bozkır coğrafyası, ekonomisi, felsefesi, at-merkezli medeniyet | short_new | "Bozkır Felsefesi" (TBD) veya foundation |
| KURG | KURGANLAR | 61-80 | 20 | Arkeolojik kanıt tabanı: gömü ritüelleri, toplum yapısı, sanat/teknoloji | short_new | "Kurganlar" belgeseli (TBD) |
| KUR-A | KÜR-ARAZ VE ERKEN DÜNYA | 81-100 | 20 | İlk yerleşik medeniyetler, Kafkasya, tarım/çobanlık, metal devrimi | short_new | "Erken Dünya" veya "Kafkasya Evresi" (TBD) |

## Faz A Araştırma Rotası

### Faz A — Her bölüm için:
1. **A1 Discovery**: Temel yazı, sosyal araştırma, haber kaynakları
2. **A2 Story Mining**: Bölüm içindeki önerilen başlıkların arka planında hangi tarihsel iddialar var?
3. **A3 Opportunity Scoring**: evidence_density, novelty, research_gap, counterintuitive_value, narrative_tension, researchability

### Sonuç:
Her bölüm için 1 konsept kartı (faz-a-<section>.json) + Faz A raporu (.md).

**Token Bütçesi**: Faz A sadece keşif ve scoring = ~5-10k tokens/section (minimal). Daha derin Faz B/C yalnızca **kullanıcı onayı sonrası** başlanır.

## İşlem Sırası

1. **A-LAYER** (neden araştırıyoruz) — studio'nun entelektüel temelini anla
2. **BOZ-01** (bozkır) — coğrafya ve medeniyetin itme gücü
3. **KURG** (kurganlar) — arkeolojik kanıt tabanı
4. **KUR-A** (erken dünya) — Kafkasya bağlamında contextual foundation

Paralel araştırma değil, sıralı — her bölümün önceki bölümün bağlamını anlamaya ihtiyacı var.

## Beklenen Çıktı

- `/research/items-1-100/faz-a-alayer.json` + `.md`
- `/research/items-1-100/faz-a-bozkirin.json` + `.md`
- `/research/items-1-100/faz-a-kurganlar.json` + `.md`
- `/research/items-1-100/faz-a-kur-araz.json` + `.md`
- `/research/items-1-100/research-summary.md` (taslak: hangi konuların uzun videoya hazır olduğu)

---

**NOT**: Backlog'daki tüm 1000 maddenin bu yapı ile ayrıştırılması planlıda (Faz 0, M23 otomasyonu TBD). Bu çalışma pilot = proof-of-concept.
