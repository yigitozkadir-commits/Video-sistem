---
name: historical-research-pipeline
description: Derin, kaynak temelli, akademik düzeyde tarihsel araştırma yapıp bu stüdyonun bir sonraki projesine kaynak (project.json.source) olarak beslenebilecek, denetlenebilir bir "Research Package" üreten uçtan uca iş akışı. Kullanıcı bir tarihsel konu, dönem veya soru verdiğinde; "tarih araştırması yap", "bu konuyu araştır", "video için tarih konusu bul", "research package hazırla" gibi isteklerde bu skill tetiklenir. 29 modüllük bir konsept tasarımının 5 fazlı, Claude Code üzerinde gerçekten çalıştırılabilir sürümü, bu stüdyonun CLAUDE.md yasalarına bağlanmış haliyle.
---

# Historical Research Pipeline — Orkestratör

Bu skill, 29 ayrı "modül" olarak tasarlanmış bir konsept dokümanını,
Claude Code üzerinde gerçekten çalıştırılabilecek **5 fazlı bir iş
akışına** indirger. Orijinal 29 modül birbirine çok yakın/örtüşen
görevler tanımlıyordu (ör. Modül 03/06/12/25 hepsi "daha çok kaynak
bul" işlevi görüyordu); bu sürüm aynı işlevleri tekrarsız şekilde
5 faza topluyor, ama hiçbir yeteneği kaybetmiyor.

**Bu stüdyoya özgü bağlam:** Bu skill, `CLAUDE.md`'nin tanımladığı
"AI Audiobook Studio OS"a yeni bir **üretim-öncesi (pre-production)
rol** ekler — `bible/Module_23_Historical_Research_Pipeline.md`'de
tanımlı. Diğer tüm projeler (PRJ-avrasya-bozkir-kusagi,
PRJ-ryskulov-mektubu, PRJ-baskurtlar-arastirma, PRJ-ninniler-atlasi)
şimdiye kadar kullanıcının önceden yazıp verdiği bir `.docx`/`.pdf`
kaynak belgeyle başladı (`project.json.source.file`). Bu skill, o
kaynak belgeyi kullanıcı yerine **araştırıp üretir** — çıktısı
(`faz-e-package.md`) yeni bir projenin `source.file`'ı olabilir. M23'e
bakın: tam köprü, `rights.source_basis` ataması, ve bu stüdyonun 8
yasasının bu pipeline'a nasıl uygulandığı orada.

## Neden 5 faz?

| Orijinal modüller | Bu sistemde |
|---|---|
| 01, 02, 11 | **Faz A — Keşif & Konsept** |
| 03, 06, 12, 13, 25, 26, 27, 28 | **Faz B — Derin Araştırma** |
| 04, 09, 10, 14, 16, 17 | **Faz C — Doğrulama & Analiz** |
| 05, 07, 08, 15, 18, 19, 20 | **Faz D — Sentez & Denetim (Kalite Kapısı)** |
| 21, 22, 23, 24, 29 | **Faz E — Üretim Paketi** |

Her faz kendi dosyasında (`phases/faz-a-*.md` vb.) ayrıntılı talimat,
alt görev listesi ve **tam JSON şeması** içerir. Bu SKILL.md yalnızca
orkestrasyonu anlatır; iş mantığı faz dosyalarındadır. Ortak şemalar
(Claim/Evidence/Source/Unknown/Angle/Hook) `reference/sema.md`'de, ve
nihai paketin resmi JSON Schema karşılığı
`schemas/research_package.schema.json`'dadır (M23'ün emrettiği gibi,
bu stüdyonun 1. yasası — "contract over prose" — burada da geçerli).

## Ne zaman kullanılır

- "X hakkında derin tarih araştırması yap"
- "Bu konuyu [yeni proje] için araştır"
- "Şu tarihsel iddiayı doğrula / çürütmeye çalış"
- "Research package / dosier hazırla"
- Kullanıcı zaten bir konu/soru/dönem belirtmiş ve derinlemesine,
  kaynaklı, denetlenebilir bir araştırma istiyor.

Basit "bana X hakkında bilgi ver" tarzı sıradan sorularda bu ağır
pipeline'ı **çalıştırma** — sadece doğrudan cevap ver. Bu skill,
kullanıcı açıkça çok adımlı / derin / yayına hazır araştırma
istediğinde devreye girer.

## Çalışma prensibi (tüm fazlarda ortak)

1. **Konuşma, iddia değil.** Her önemli tarihsel iddia ayrı bir
   "claim" olarak ele alınır ve kaynağa bağlanır.
2. **Fact / Inference / Interpretation / Speculation ayrımı** her
   zaman korunur, hiçbir zaman birbirine karıştırılmaz.
3. **Bilinmiyor, geçerli bir sonuçtur.** Kanıt yoksa "muhtemelen"
   diye tahmin üretilmez; `UNKNOWN` / `OPEN QUESTION` olarak
   işaretlenir. Bu, CLAUDE.md'nin 4. yasasının ("no silent
   degradation") bu pipeline'daki karşılığıdır.
4. **Tek kaynak = zayıf iddia.** Bağımsız doğrulaması olmayan
   iddialar açıkça düşük güvenilirlikle etiketlenir.
5. **Adversarial mod zorunlu.** Kanıt bulmak yetmez; o kanıtı
   çürütmeye çalışmak (Faz C) sürecin ayrılmaz parçasıdır.
6. **Senaryo/başlık/thumbnail üretilmez.** Bu pipeline yalnızca
   araştırma ve içerik-açısı seçimine kadar gider (Faz E sonunda
   durur); video metni yazımı (bu stüdyoda M05/M17'nin işi) bu
   skill'in kapsamı dışındadır.

## Orkestrasyon akışı

```
KULLANICI GİRDİSİ (konu / dönem / soru / serbest metin)
        ↓
FAZ A — Keşif & Konsept
   A1 discovery → A2 story-mining → A3 opportunity-scoring
   ÇIKTI: Concept Card (1 veya birkaç aday, kullanıcı seçer)
        ↓
FAZ B — Derin Araştırma
   B1 research-plan → B2 claim-decompose → B3 çok-kanallı kaynak
   taraması (web/akademik/arşiv/çok-dilli/malzeme kanıtı)
   ÇIKTI: Research Dossier (draft) + Source Registry
        ↓
FAZ C — Doğrulama & Analiz
   C1 adversarial-verification → C2 historiography →
   C3 unknowns/anomalies → C4 claim-evidence graph →
   C5 source quality ranking
   ÇIKTI: Verification Report + Claim–Evidence Graph
        ↓
FAZ D — Sentez & Denetim (KALİTE KAPISI)
   D1 synthesis → D2 evidence packaging → D3 chronology/causality
   → D4 completeness audit → D5 READINESS GATE (BLOCKED/CONDITIONAL/READY)
   ÇIKTI: Master Research Dossier + Readiness Report
   ⚠️ D5 "BLOCKED" derse Faz E'ye GEÇİLMEZ, eksikler kullanıcıya
      raporlanır ve Faz B/C'ye geri dönülür.
        ↓
FAZ E — Üretim Paketi
   E1 angle-selection → E2 hook-discovery → E3 package-format →
   E4 archive/versiyonlama
   ÇIKTI: Research Production Package (.md + .json, dosya olarak teslim edilir)
        ↓ (opsiyonel, kullanıcı isterse)
   Yeni bir PRJ-* projesinin project.json.source olarak kullanılır — M23 §4
```

## Adım adım orkestrasyon talimatı

1. Kullanıcının girdisini al. Girdi zaten netse (belirli bir tarihsel
   soru/iddia) Faz A'yı hızlı geçebilirsin (tek konsept, doğrudan
   B'ye). Girdi geniş bir alan/dönem ise Faz A birden fazla aday
   üretir ve **AskUserQuestion** ile kullanıcıya hangisini
   derinleştireceğini sor.
2. Her fazın çıktısını `research/<proje-slug>/` altında ilgili JSON+MD
   dosyası olarak **gerçekten yaz** (Write aracıyla — bkz. "Dosya
   düzeni"). Bu, Modül 24'ün (archive/version control) karşılığıdır —
   ilerlemeyi kaybetmemek ve kullanıcının ara çıktıları görebilmesi
   için şarttır. `research/` bu deponun kökünde, `projects/`'in
   kardeşi yeni bir dizindir (bir proje henüz `PRJ-*` olarak
   scaffold edilmeden önce araştırma burada birikir).
3. Web araştırması gerektiren her adımda gerçek **WebSearch** /
   **WebFetch** araçlarını çağır. Bu bir simülasyon değildir —
   kaynaklar gerçek olmalı, URL'ler gerçek olmalı. Kaynak
   bulunamıyorsa "kaynak bulunamadı" diye dürüstçe işaretle, uydurma.
4. Faz D sonunda mutlaka **Readiness Gate** kararını kullanıcıya açık
   şekilde raporla (READY / CONDITIONAL / BLOCKED). Kullanıcı
   onaylamadan Faz E'ye geçme.
5. Faz E sonunda `research/<proje-slug>/faz-e-package.json` ve
   `.md` dosyalarını Write ile yaz, **SendUserFile** ile kullanıcıya
   teslim et (`status: "proactive"`, `display: "attach"` — bu bir
   üretim çıktısı, sohbet içi bir görselleştirme değil).
6. Uzun sürecek bir konuda (çok sayıda WebSearch gerekecekse) bunu
   kullanıcıya en başta söyle; gerekirse fazları ayrı mesajlarda
   ilerlet (hepsi tek turda bitmeyebilir).
7. **İlerleme bildirimi normu:** Düzenli olarak kısa durum
   güncellemesi ver. Kural: her faz tamamlandığında (A→B→C→D→E
   geçişlerinde) ve bir fazın içinde yaklaşık her 10-15
   WebSearch/WebFetch çağrısında bir, 1-3 cümlelik bir özet ver ("şu
   ana kadar X claim bulundu, Y kaynak tarandı, şu an Z'yi
   doğruluyorum" gibi). Kısa bir cümle yeterli, uzun ara rapor yazmaya
   gerek yok.
8. Faz E bittiğinde ve kullanıcı paketi bir projeye dönüştürmek
   isterse, M23 §4'teki köprüyü uygula: `faz-e-package.md`'yi yeni
   projenin `input/` dizinine kopyala, sha256'sını hesapla,
   `project.json.source` alanını doldur, `rights.source_basis:
   "owned"` ata (`rights.evidence_ref`, paketin `bibliography`
   alanına işaret etsin). Bu adım kullanıcı açıkça istemeden
   otomatik yapılmaz — araştırma paketi kendi başına da geçerli bir
   teslimattır.

## Dosya düzeni (bir proje için)

```
research/<proje-slug>/
  00-input.md
  faz-a-concept.json
  faz-b-dossier.json
  faz-c-verification.json
  faz-d-master-dossier.json
  faz-d-readiness.json
  faz-e-package.json
  faz-e-package.md          ← insan-okunabilir final rapor
```

Faz dosyaları arasındaki JSON şemaları için `phases/` altındaki
dosyalara bakın:

- `phases/faz-a-kesif-konsept.md`
- `phases/faz-b-derin-arastirma.md`
- `phases/faz-c-dogrulama-analiz.md`
- `phases/faz-d-sentez-denetim.md`
- `phases/faz-e-uretim-paketi.md`

Ortak kayıt şemaları (Claim, Source, Evidence, Confidence seviyeleri
vb.) için `reference/sema.md` dosyasına bakın — tüm fazlar bu ortak
sözlüğü kullanır, her faz kendi şemasını icat etmez. Nihai paketin
(`faz-e-package.json`) resmi JSON Schema karşılığı
`schemas/research_package.schema.json`'dadır; teslimden önce
`jsonschema.validate()` ile (veya `scripts/validate.py` bir sonraki
çalıştırmasında) bu şemaya karşı doğrulanabilir olmalı.

## Kısayol modları

Kullanıcı tüm pipeline'ı değil, tek bir faz/görev istiyorsa (ör.
"sadece bu iddiayı doğrula", "sadece kaynakları derecelendir"), ilgili
faz dosyasını tek başına çalıştır; önceki fazların çıktısı yoksa
kullanıcıdan gerekli minimum bilgiyi (iddia metni + varsa kaynaklar)
iste ve o fazı bağımsız çalıştır.

## Gerekli araçlar / API anahtarları

**Hiçbir yeni ücretli API anahtarı gerekmez.** Bu pipeline yalnızca
Claude Code'un yerleşik **WebSearch**, **WebFetch** ve
**AskUserQuestion** araçlarını kullanır — hepsi zaten bu ortamda
mevcut. Opsiyonel iyileştirmeler için `bible/Module_23_Historical_Research_Pipeline.md`
§6'ya bakın (ör. Semantic Scholar API anahtarı, yalnızca akademik
tarama hacmi/rate-limit'i iyileştirir, pipeline anahtarsız da tam
çalışır).
