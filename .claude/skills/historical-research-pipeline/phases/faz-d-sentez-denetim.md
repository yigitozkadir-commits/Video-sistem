# FAZ D — Sentez & Denetim (Kalite Kapısı)

**Kaynak modüller:** 05 (Synthesis & Narrative Intelligence), 07
(Evidence Architecture), 08 (Chronology & Causality), 15 (Research
Synthesis / Master Dossier), 18 (Research Gaps), 19 (Completeness
Audit), 20 (Readiness Gate)

**Girdi:** `faz-b-dossier.json` + `faz-c-verification.json`

**Çıktı:** `faz-d-master-dossier.json` + `faz-d-readiness.json`

Bu faz, pipeline'ın **kalite kapısıdır**. Buradan "BLOCKED" çıkan bir
araştırma Faz E'ye geçmez.

---

## D1 — Synthesis (Modül 05)

Doğrulanmış araştırmayı özetlemek değil, **içindeki gizli
bağlantıları** keşfetmek: çatışmalar, paradokslar, karakterler,
neden-sonuç zincirleri, özgün açılar. Bu adım henüz senaryo/başlık
üretmez — sadece "bu araştırmada hangi güçlü içerik fırsatları var"
sorusuna cevap arar (Faz E'nin girdisini hazırlar).

## D2 — Evidence Architecture & Claim Packaging (Modül 07)

Her claim'i şu standarda getir: **"Bir iddiayı söylediğimizde, buna
neyin dayandığını birkaç saniyede görebilmeliyiz."**

Her claim paketi şunları içermeli:
- İddia metni
- Bağlı kanıtlar (evidence_id listesi)
- Bağlı kaynaklar (source_id listesi, bağımsızlık durumu)
- Bağlam (gerekliyse)
- Karşı argüman (varsa)
- Güven seviyesi
- `confidence_history`'ye D-fazı kaydını ekle: `{"phase": "D",
  "value": "<nihai değer>", "reason": "<paketleme sırasında son
  netleşme gerekçesi>"}` — B ve C'deki önceki kayıtlar silinmez.
- Fact / inference / interpretation ayrımı korunmuş olarak

## D3 — Chronology & Causality (Modül 08)

**Kritik ilke: Kronoloji ≠ nedensellik.** Bir olayın diğerinden sonra
gerçekleşmesi, ona sebep olduğu anlamına gelmez.

1. Olayları zaman çizelgesine yerleştir (Timeline —
   `reference/sema.md § 7`). Her olayın tarihine bir **kesinlik**
   etiketi ekle: `EXACT | YEAR_ONLY | MONTH_RANGE | YEAR_RANGE |
   BEFORE | AFTER | CIRCA | UNKNOWN`. Takvim dönüşümü gerekiyorsa
   (Hicri, saltanat yılı, vb. → Miladi) `calendar_system` ve
   `conversion_confidence` alanlarını doldur — dönüştürülmüş bir
   tarihi hiç dönüştürülmemiş gibi sunma.
2. Ayrı bir katmanda: hangi olayın hangi olaya **neden olduğu**
   iddiasını, `reference/sema.md § 8`'in **9 nedensellik-bağlantısı
   tipiyle** işaretle (basit "önce/sonra" ikiliğinden çok daha
   ayrıntılı): `DIRECT_CAUSE | INDIRECT_CAUSE | CONTRIBUTING_FACTOR |
   ENABLING_CONDITION | TRIGGER | AMPLIFIER | CONSTRAINT | MEDIATOR |
   CONSEQUENCE`. Faz C1'de zaten yapılmış olan nedensellik
   4-eksen-ayrıştırması (`causal_reasoning`) ve karşı-olgusal test
   (`counterfactual_test`) sonuçlarını buraya taşı.
3. Paralel/eşzamanlı olayları ayrıca not et (yanlış nedensellik riski
   taşırlar).
4. Ön koşul (precondition) tek bir kategori değil, üç kademeye
   ayrılır (`precondition_tier`): **structural** (uzun vadeli, yapısal
   ön-koşul — ör. bir ekonomik sistem), **enabling** (belirli bir anda
   imkan tanıyan koşul), **trigger** (doğrudan tetikleyici olay). Bu
   üçünü doğrudan nedenle (`DIRECT_CAUSE`) karıştırma.
5. **Kronoloji↔Claim geri-besleme döngüsü:** Bu adımda bir zamansal
   çelişki bulursan (ör. bir claim'in iddia ettiği olay sırası, timeline
   ile çelişiyorsa), bu **D2'ye (Claim Packaging) geri dön ve o
   claim'i yeniden değerlendir** anlamına gelir — pipeline'ın tek
   doğrusal istisnası budur, sessizce görmezden gelme.

## D4 — Completeness Audit (Modül 19)

Yayın öncesi denetim kontrol listesi — her madde için evet/hayır +
kanıt:

- [ ] Her `core` önemdeki iddianın kaynak bağlantısı var mı?
- [ ] Birincil kanıt mevcutsa kullanıldı mı?
- [ ] Kaynaklar gerçekten bağımsız mı (aynı `independence_group`
      değil mi)?
- [ ] Karşı kanıt sistematik olarak arandı mı?
- [ ] Ana karşı görüşler (historiography) temsil ediliyor mu?
- [ ] İhtilaflı/milliyetçi konularda kaynakların taraf dağılımı
      dengeli mi (C2 `perspective_diversity` alanı `skewed` veya
      `single_perspective_only` ise, bu ayrıca ve açıkça işaretli
      mi)?
- [ ] Bilinmeyenler açıkça `unknowns` listesinde mi?
- [ ] Spekülasyon hiçbir yerde olgu gibi yazılmamış mı?
- [ ] Birincil/ikincil kaynak ayrımı her kayıtta net mi?
- [ ] Kaynak zinciri (Faz B3) geriye doğru izlenebiliyor mu?
- [ ] Çözülmemiş çelişkiler (Faz C4) açıkça işaretli mi?
- [ ] Research gaps (aşağıda D-gaps) raporlandı mı?
- [ ] **False Completion kontrolü** — "yeterince kaynak bulundu"
      izlenimi, altı ayrı eksende (claim kapsamı, kanıt kalitesi,
      kaynak bağımsızlığı, birincil kaynak kapsamı, karşı-argüman
      kapsamı, boşluk kapsamı) gerçekten doğrulandı mı, yoksa sadece
      kaynak SAYISINA mı bakıldı (bkz. Faz B4)?
- [ ] Faz C1'in Red Team bayrakları (`CITATION_UNVERIFIED`,
      `ESTIMATE_PRESENTED_AS_EXACT`, `ANACHRONISM`,
      `EVIDENCE_INFLATION`) çözüldü mü, yoksa çözülmemiş olarak mı
      paketleniyor (paketlenebilir, ama sessizce değil)?

Her ihlal `severity`: `CRITICAL | HIGH | MEDIUM | LOW | INFO` ile
kaydedilir.

## D-gaps — Research Gaps (Modül 18)

Cevaplanmamış soruları ve gerçek boşlukları listele:
`missing_primary_source | missing_archive | unsearched_language |
understudied_region | chronological_gap | attribution_gap |
causal_gap | methodological_gap | historiographical_gap |
translation_gap`

Her gap için: soru, mevcut kanıtın neden yetersiz kaldığı, olası
kaynak/yöntem, öncelik (`historical_importance × researchability ×
evidence_potential × originality`).

## D5 — Research Readiness Gate (Modül 20) — ZORUNLU KARAR NOKTASI

**Hard blocker'lar** (herhangi biri varsa sonuç otomatik `BLOCKED`):

- Kritik bir `core` iddia hiçbir kaynağa bağlanamıyor
- Birincil kaynak yanlış temsil ediliyor
- Temel bir çelişki D4'te gizli kalmış / raporlanmamış
- Spekülasyon, olgu gibi sunulmuş (herhangi bir yerde)
- Kaynak zinciri güvenilmez (authenticity_risk: high, çözülmemiş)
- Ana karşı görüş hiç araştırılmamış
- İhtilaflı/milliyetçi bir konuda kaynaklar tek taraflı
  (`perspective_diversity: single_perspective_only`) ve karşı
  tarafın literatüründe hiç arama yapılmamış
- Kritik çeviri/tarih problemi çözülmeden bırakılmış

**Durumlar:** `BLOCKED | CONDITIONAL | READY | HIGH_CONFIDENCE_READY`

- `BLOCKED` → Faz E'ye geçilmez. Kullanıcıya net biçimde hangi
  blocker'ların olduğu ve hangi Faz B/C adımına dönülmesi gerektiği
  raporlanır.
- `CONDITIONAL` → Faz E'ye geçilebilir ama paket içinde açıkça
  "koşullu onaylı" claim'ler işaretlenmeli.
- `READY` / `HIGH_CONFIDENCE_READY` → Faz E'ye serbestçe geç.

## Çıktı şemaları

`faz-d-master-dossier.json`:

```json
{
  "phase": "D",
  "master_claims": [ /* reference/sema.md § 2, final güncellenmiş */ ],
  "timeline": [ /* reference/sema.md § 7 */ ],
  "causal_links": [ /* reference/sema.md § 8 */ ],
  "content_opportunities_preview": ["Faz E'ye aktarılacak ham gözlemler"],
  "research_gaps": [
    {"gap_id": "G-01", "type": "", "question": "", "priority": "high|medium|low"}
  ]
}
```

`faz-d-readiness.json`:

```json
{
  "phase": "D5",
  "audit_findings": [
    {"item": "", "status": "pass|fail", "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO", "note": ""}
  ],
  "blockers": ["varsa liste, yoksa boş"],
  "readiness_state": "BLOCKED|CONDITIONAL|READY|HIGH_CONFIDENCE_READY",
  "required_fixes": ["BLOCKED/CONDITIONAL ise buraya yaz"]
}
```

## Orkestrasyon notu

D5 sonucu ne olursa olsun, kullanıcıya **açıkça** raporla (state +
varsa blocker listesi). `BLOCKED` çıkarsa kullanıcıdan onay almadan
Faz E'yi çalıştırma; eksik araştırmayı tamamlamak için Faz B/C'ye
dönmeyi teklif et.
