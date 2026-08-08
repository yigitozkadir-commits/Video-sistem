# MODULE 22 — SCENE PLANNING ALGORITHM (SAHNE PLANLAMA ALGORİTMASI)

**Versiyon 0.2 — TASLAK** · **Katman 6 (Intelligence)** · **Rol:** PDF/rapor girdisinden
sahne sayısı, süre ve görsel/video karışımını **otonom** olarak belirlemek.

> Kullanıcı talebi (2026-08-07): "sana bir PDF attığımda kaç sahne yapacağını
> nasıl yapacağını artık kendin belirle, ben sürekli öneride bulunmam
> gerekiyordu." Bu modül o kararı formalleştirir — Teknik Prodüksiyon
> Direktörü (CLAUDE.md §3 "may decide: scene candidates, manifests,
> timelines") yetkisi kapsamında, insan onayına gerek kalmadan uygulanır.
> **Taslak** statüsündedir: kalibrasyon sabitleri yeni projeler tamamlandıkça
> güncellenecek (bkz. §7 Kalibrasyon Verisi).

---

## 1. MİSYON

M17 §5 ("duration is derived, never chosen") ve M17 §7 ("video or still") zaten
BİR sahnenin süresini ve video/still kararını nasıl vereceğini tanımlıyor. Ama
o modül **sahne SAYISINI** ve **proje-geneli video/still hedef oranını**
varsaymıyor — bunlar her seferinde insan girdisiyle belirleniyordu. Bu modül
o boşluğu dolduruyor: bir PDF/rapor/metin geldiğinde, insan hiç
sormadan, kaç sahne olacağını, ne kadar süreceğini ve sahnelerin ne kadarının
video ne kadarının still olacağını **hesaplar**.

---

## 2. GİRDİ SINIFLANDIRMASI (content_type)

Kaynak metnin doğası, aşağıdaki adımların tamamını değiştirir. İlk adım her
zaman sınıflandırma:

| content_type | Belirti | Örnek (bu stüdyoda) |
|---|---|---|
| `research_documentary` | Akademik/araştırma raporu, kaynakça var, üçüncü şahıs anlatım | PRJ-baskurtlar-arastirma |
| `illustrated_story` | Çocuk kitabı / masal, birinci-ikinci şahıs, kısa cümleler, düşük kelime sayısı | PRJ-daglar-uyuyan-devleri |
| `encyclopedic_atlas` | Çok geniş kapsamlı referans metni (>10.000 kelime), doğal bölüm/başlık kırılımları var | PRJ-gok-umay-atlasi |
| `narrative_history` | Kronolojik olay anlatımı, karakterler var ama kurgu değil (örn. 1453 kuşatması) | PRJ-fetih-1453 (video planı geldiğinde) |
| `other` | Yukarıdakilerin hiçbirine net uymuyor | — |

Sınıflandırma otomatik yapılır: `pdftotext` ile çıkarılan metnin kelime sayısı,
başlık/bölüm yapısı (regex ile numaralı/büyük harfli başlıklar), kaynakça
varlığı ve cümle uzunluğu ortalaması üzerinden. Belirsizse `research_documentary`
varsayılan (en güvenli/en nötr pacing).

---

## 3. NARRATION KELİME SAYISI HEDEFİ

```
if content_type == "research_documentary":
    narration_words = source_words × factor
    factor ∈ [0.8, 1.3]   # M21/WebSearch ile doğrulanmış ek araştırma varsa üst sınıra yakın,
                           # rapor zaten yeterince zenginse alt sınıra yakın (bkz. Başkurtlar v2: 2220→1807, 0.81x,
                           # çünkü sıkıştırma + doğrulanmış ek bulgu aynı anda oldu — net etki kaynağa göre değişir)
elif content_type == "illustrated_story":
    narration_words = user-specified duration önceliklidir (kelime değil, SÜRE
                       birincil girdi — çocuk formatı sabit-tempo çalışır, bkz. §5)
elif content_type == "encyclopedic_atlas":
    episode_count = round(source_words / 4000)   # Atlas projesindeki 25.330 kelime → 6 bölüm, kalibrasyon buradan
    narration_words_per_episode = 560             # SABİT, kaynağın oranı DEĞİL - her bölüm bir
                                                    # küratörlü özet, tam transkripsiyon değil.
                                                    # Gerçek ölçüm (ffprobe, 6 atlas-video-*.mp4):
                                                    # 1743s toplam / 6 bölüm = ~290s/bölüm ≈ 560 kelime/bölüm.
                                                    # İlk taslakta bu yanlışlıkla source_words/episode_count
                                                    # (~4200 kelime/bölüm, ~36 dk/bölüm) olarak hesaplanmıştı -
                                                    # gerçek render süreleriyle karşılaştırılınca ~7x fazla
                                                    # çıktığı görüldü ve düzeltildi (bkz. §7 tablo notu).
elif content_type == "narrative_history":
    narration_words = source_words × [1.0, 1.5]  # olay anlatımı genelde genişletilir (bağlam, sahne kurma)
else:
    narration_words = source_words × 1.0
```

---

## 4. SÜRE HESABI — GERÇEK (ÖLÇÜLMÜŞ) WPM KULLAN

Şablonların "hedef" wpm'i (örn. `TPL-baskurtlar-hybrid`: 145 wpm) **planlama
sırasında** kullanılır ama gerçek teslim edilen konuşma hızı duraklama/sessizlik
yüzünden her zaman daha düşüktür (M17 §9 silence rules). Ölçülmüş gerçek:

```
BASKURTLAR_DELIVERED_WPM = 114.6   # 1807 kelime / 945.67s, gerçek render, ffprobe ile ölçüldü
```

```
target_duration_s = narration_words / (DELIVERED_WPM / 60)
```

Planlama aşamasında hep **DELIVERED_WPM** (114–120 aralığı, dil ve içerik
yoğunluğuna göre) kullanılır, şablonun "hedef" wpm'i değil — yoksa süre tahmini
sistematik olarak düşük çıkar (Başkurtlar v2 planında bu hata yapıldı: 145 wpm
ile ~17-19 dk tahmin edildi, gerçek 15.76 dk çıktı — %20 fark).

---

## 5. SAHNE SAYISI

```
avg_scene_length_s = {
  research_documentary: 40–50s   (Başkurtlar gerçek ortalama: 945.67/20 = 47.3s)
  narrative_history:     30–45s   (daha hızlı kesim, aksiyon/olay yoğun)
  illustrated_story:     8–12s    (Dağların Uyuyan Devleri: 480/48 = 10s sabit)
  encyclopedic_atlas:    35–50s   (bölüm içi alt-başlık başına bir sahne)
}

scene_count = round(target_duration_s / avg_scene_length_s)
```

M17 §5 sınırları burada da geçerli: hiçbir sahne 8s altına düşmez (birleştir),
90s üstüne çıkmazsa `long_scene_rationale` gerekmez — çıkarsa böl ya da
gerekçelendir.

---

## 6. VİDEO/STILL ORANI — M17 §7'YE GÜNCELLEME (Flow artık birincil kaynak)

M17 §7'nin "40–60% still" hedefi, video üretiminin **pahalı ve kısıtlı** olduğu
bir dönemde yazıldı (Higgsfield kredi/kota rejimi). Kullanıcı artık görsel VE
videonun büyük çoğunluğunu **Google Flow**'dan kendisi üretiyor — bu maliyet
kısıtını kaldırıyor. Yeni varsayılan, M17'nin karar ağacını (§7) **yapı olarak
korur**, sadece eşikleri gevşetir:

```
Her beat için:
  if beat.function in {breath, transition} and weight < 0.3        → still
  if content is REFERENCE_ONLY (taranmış kitap sayfası, gerçek arşiv fotoğrafı) → still, asla video
  if duration < 2.5s                                                → still
  else                                                               → VIDEO (varsayılan artık bu)

Video seçilen her sahne için ikinci bir yönlendirme kararı:
  if shot needs: çok-karakterli dinamik etkileşim, koreografili çatışma/dövüş,
                 hassas yüz/identity tutarlılığı (kilitli karakter, M15 §9 lock)
                 veya Flow bu proje için bu tür sahnede daha önce başarısız oldu
      → HIGGSFIELD (dikkatli, kısıtlı kullanım — kullanıcı onayı olmadan
        ÜRETME kuralı hâlâ geçerli, bkz. CLAUDE.md + PRJ-fetih-1453 hard rule)
  else
      → FLOW (varsayılan, kullanıcı kendi üretecek)
```

**Hedef karışım (yeni varsayılan, Flow-öncelikli prodüksiyon için):**

| Metrik | Eski (M17 §7, kredi-kısıtlı dönem) | Yeni (Flow birincil kaynak) |
|---|---|---|
| Still oranı | %40–60 | **%20–35** |
| Video oranı | %40–60 | **%65–80** |
| Video kaynağı | — | ~%90 Flow, ~%10 Higgsfield (sadece karmaşık sahne) |
| Uzun sahnelerde (>45s) strateji | still + ara-sahne (insert) ekle | **önce video'ya çevir**, still+insert yığmak son çare |

Somut örnek: 20–30 sahnelik bir belgesel için bu, **10–20 video sahnesi**
demektir (kullanıcının kendi verdiği referans: "bazen videolarda 20 tane ai
video bile bulunabilir"). Başkurtlar v2'nin 4 video / 20 sahne (%20) oranı bu
yeni varsayılanın ALTINDA kalıyor — geriye dönük düzeltilmeyecek (yayınlandı),
ama bir SONRAKİ benzer projede bu oran taban alınmayacak.

**Still'in hâlâ doğru olduğu tek durumlar:** gerçek arşiv fotoğrafı/tarihi
belge/taranmış sayfa (REFERENCE_ONLY, video ile "canlandırmak" tarihsel
sahteciliğe yakın durur), 2.5s'den kısa flaş-kesmeler, ve nefes/geçiş
beat'leri (M17 §7 bu üçünü değiştirmiyor).

---

## 6b. AI-VİDEO SAYISI — SÜRE-BAZLI MUTLAK HEDEF (v0.2)

§6'daki yüzde modeli (`video_ratio_target`) sahne sayısına bağlıydı. Kullanıcı
(2026-08-07) bunun yerine **toplam süreye bağlı, sahne sayısından bağımsız**
somut çapa noktaları verdi:

| Süre | AI-video sayısı |
|---|---|
| 10–15 dk | 5 |
| 30 dk | 10–15 |
| 60 dk | 20 |

```
ANCHORS = [(12.5, 5), (30, 12.5), (60, 20)]   # (dakika, ai_video_count), orta noktalar alındı

ai_video_count_target(duration_min):
    parçalı-doğrusal enterpolasyon, ANCHORS noktaları arasında.
    duration_min < 12.5  → 12.5 dk'daki eğimle orana göre küçült (taban 1)
    duration_min > 60    → son segment eğimiyle (0.25 video/dk) ekstrapole et,
                            ama çıktıda "kalibrasyon dışı — 60dk üstü henüz
                            gerçek projeyle doğrulanmadı" notu taşı.
```

`research_documentary`/`narrative_history` için bu, §6'nın `video_ratio_target`
yüzdesinin **yerine geçer** (birincil model); `video_ratio_target` artık sadece
`illustrated_story`/`encyclopedic_atlas` gibi still-ağır formatlarda ya da
content_type belirsizken fallback olarak kullanılır.

## 6c. GÖRSEL YOĞUNLUĞU — SÜRE-BAZLI MUTLAK HEDEF (v0.2)

Aynı kullanıcı talebi: **15 dakikalık video → 100 görsel**. Google Flow görsel
üretimi "sınırsız" (Higgsfield gibi kredi/kota kısıtı yok) — bu yüzden görsel
sayısı artık sahne başına 1 primary + birkaç insert değil, **çok daha sık**:

```
IMAGE_DENSITY = 100 / 15  # = 6.667 görsel/dakika  (~1 görsel her ~9 saniyede)

image_count_target(duration_min) = round(duration_min × IMAGE_DENSITY)
```

Bu, mevcut sahne-başı-insert mekanizmasını (Başkurtlar v4/v5'te kurulmuş,
`SC-{id}_insert{N}.jpg` deseni, `generate_baskurtlar_scenes_data.py`'nin zaten
otomatik topladığı) DEĞİŞTİRMİYOR — sadece insert SIKLIĞINI artırıyor.
Başkurtlar'ın gerçek yoğunluğu 58 benzersiz still / 945.67s ≈ 3.68 görsel/dk
idi; yeni hedef ~1.8× daha sık. `image_count_target`, toplam sahne süresine
(uzun sahneler daha çok insert alır) orantılı dağıtılır — M17 §5'in
comprehension_margin mantığıyla çakışmaz, sadece "kaç tane" sorusuna cevap
verir, "hangi anda" sorusuna M17 hâlâ kendi karar ağacıyla cevap verir.

## 6d. PDF-İÇİ-GÖRSEL KAYNAK DALI (v0.2)

Bazı kaynak PDF'ler (kullanıcının verdiği örnek: `PRJ-gok-umay-atlasi`'nin
atlas PDF'i, 141 sayfa) kendi içinde zaten kullanılabilir görsel taşır —
`pdfimages -list <pdf>` ile doğrulandı: 541 gömülü raster obje. Bu tür
kaynaklar için Flow'da sıfırdan üretmek yerine, **PDF'in kendi görselleri
kırpılıp yüksek yoğunlukla kullanılır** — bu `bible/Module_14_Claude_Code_Enterprise.md`
§5 "IMAGE PIPELINE"in tarif ettiği ama daha önce hiç kod olarak yazılmamış akış.

```
embedded_image_count = pdfimages -list ile sayım, smask/dekoratif hariç,
                        min 100×100px filtre uygulanmış

if embedded_image_count ≥ 20:
    source_has_embedded_images = true
    → scripts/extract_pdf_images.py çalıştır (M14 §5 pipeline: extract →
      kaba otomatik sınıflandırma → schemas/image_catalog.schema.json'a yaz)
    → çıkarılan+kullanılabilir-disposition'lı görseller image_count_target'a
      (§6c) sayılır; hedefe ulaşmazsa eksik Flow'dan tamamlanır
else:
    → normal akış, tüm görseller Flow'dan üretilir (§6c değişmeden uygulanır)
```

Bu dal M14'ün otoritesini (extraction method, image classification/disposition
"may decide" kapsamında) hiçbir şekilde değiştirmiyor — sadece M22'nin
görsel-sayısı hedefine bir KAYNAK daha ekliyor (Flow-üretimi + PDF-çıkarımı).

## M17/M21 ENTEGRASYONU — AÇIKLIK (v0.2)

M22'nin bu bölümdeki tüm hedefleri (`ai_video_count_target`,
`image_count_target`, `scene_count`) **proje-geneli sayısal hedeflerdir**,
tek tek shot kararı DEĞİLDİR:

- **M17 (AI Director)** hâlâ her shot için kendi 6 soru-ağacını (§4-§10)
  çalıştırır ve `decisions/DEC-*.json`'a yazar — M22 sadece "toplamda kaç
  video, kaç görsel olmalı" der, "BU shot video mu still mi" M17'nin kararı
  olarak kalır. M22'nin hedefi M17'nin kararlarının TOPLAMIYLA uyuşmalı;
  uyuşmuyorsa (örn. M17'nin shot-bazlı kararları toplamda hedeflenen
  `ai_video_count_target`'ın çok altında/üstünde çıkarsa) bu sessizce
  geçilmez, `reasoning`'e not düşülür (CLAUDE.md law #4).
- **M21 (Channel Format Intelligence)** `benchmark_refs` hâlâ tamamen
  opsiyonel bir ilham/kıyas kaynağıdır (M21 §6) — kullanıcı bir kanal/video
  referansı verirse M17'nin `decision`'larına `benchmark_refs` olarak eklenir,
  M22'nin sayısal hedeflerini ASLA geçersiz kılmaz veya zorunlu kılmaz. M21
  kendi başına çalıştırılmadıysa (Gemini havuzu, Claude Code kapsamı dışı,
  bkz. M21 §1) M22 hiçbir şekilde bloklanmaz — M21 girdisi yoksa sadece
  `benchmark_refs` boş kalır.

---

## 7. KALİBRASYON VERİSİ (bu stüdyonun geçmiş projeleri)

Bu tablo yeni bir proje bitince güncellenir — sabitler buradan türetiliyor,
havadan değil:

| Proje | content_type | Kaynak kelime | Narration kelime | Sahne sayısı | Süre (ölçülmüş) | Gerçek wpm | Video/Still |
|---|---|---|---|---|---|---|---|
| PRJ-baskurtlar-arastirma | research_documentary | 2220 | 1807 | 20 | 945.67s (15.76dk) | 114.6 | 4 video / 58 benzersiz still (%20 sahne-video) |
| PRJ-daglar-uyuyan-devleri | illustrated_story | 223 | ~223 (sabit tempo) | 48 | 480s (8dk, sabit) | — (illüstrasyon-tempolu, wpm'e dayanmıyor) | 6 video / 42 still (%12.5) |
| PRJ-gok-umay-atlasi | encyclopedic_atlas | 25330 | ~560/bölüm (6 bölüm, toplam ~3360) | 6 bölüm | 1743s toplam (~290s/bölüm), ffprobe ile ölçüldü | ~115 (varsayım) | 0 video / 121 still (tamamı still, format gereği) |

`PRJ-gok-umay-atlasi` satırı, video oranı hedefinin content_type'a göre
değiştiğinin kanıtı: bir "atlas/ansiklopedi" formatı doğası gereği still-ağır
kalabilir (statik referans görselleri asıl işlevdir) — §6'daki yeni video-öncelik
varsayılanı ÖNCELİKLE `research_documentary` ve `narrative_history` içindir.
Ayrıca bu proje, narration'ın kaynak kelime sayısıyla ORANTILI olmadığının da
kanıtı: 25330 kaynak kelimesi 6 bölüme "orantılı" bölünseydi bölüm başına
~4200 kelime (~36 dk) çıkardı, ama gerçek ölçüm bölüm başına ~560 kelime
(~5 dk) — atlas formatı her bölümü küratörlü bir özet olarak anlatıyor, kaynağın
tamamını okumuyor. `scripts/plan_scene_count.py` bu ayrımı `EPISODE_SOURCE_WORDS`
(bölüm sayısını belirler) ve `EPISODE_NARRATION_WORDS` (süreyi belirler) olarak
ikiye ayırarak uyguluyor.

### 7b. Kullanıcı-verilen hedefler (§6b/§6c) — henüz render-doğrulanmamış

Aşağıdaki 4 nokta 2026-08-07'de kullanıcı tarafından doğrudan verildi, bu
stüdyonun kendi render'larından ÖLÇÜLMEDİ (yukarıdaki tablodaki 3 satırın
aksine). Dürüstlük ilkesi gereği ayrı işaretleniyor — ilk gerçek proje bu
hedeflerle üretilip render edildiğinde bu tablo satırı gerçek ölçümle
değiştirilecek/doğrulanacak:

| Süre | AI-video hedefi (kullanıcı) | Görsel hedefi (kullanıcı) | Durum |
|---|---|---|---|
| 10–15 dk | 5 | 67–100 (6.667/dk oranıyla) | doğrulanmadı |
| 30 dk | 10–15 | 200 | doğrulanmadı |
| 60 dk | 20 | 400 | doğrulanmadı |

---

## 8. ÇIKTI SÖZLEŞMESİ

```
state/scene_plan.json   — bu modülün tek çıktısı, şema aşağıda
```

```json
{
  "content_type": "research_documentary",
  "source_word_count": 2220,
  "narration_word_target": 1807,
  "target_duration_s": 945,
  "avg_scene_length_s": 47,
  "scene_count": 20,
  "video_ratio_target": 0.70,
  "video_scene_target": 14,
  "still_scene_target": 6,
  "ai_video_count_target": 8,
  "image_count_target": 105,
  "source_has_embedded_images": false,
  "embedded_image_count": 0,
  "reasoning": "research_documentary sınıfı, kaynak 2220 kelime, M22 §3 factor 0.81 uygulandı...",
  "calibration_anchor": "PRJ-baskurtlar-arastirma"
}
```

Bu dosya `scripts/plan_scene_count.py <pdf> [--content-type ...] [--target-duration-s N]`
ile üretilir (bkz. §9). Üretildikten sonra M04/M17'nin normal `beats/` →
`decisions/DEC-*.json` akışına girdi olur — bu modül sadece **başlangıç
iskeletini** verir, tek tek sahne kararlarını M17 hâlâ kendi karar ağacıyla
(§4-§7) verir ve kaydeder.

---

## 9. UYGULAMA (script)

`scripts/plan_scene_count.py` — bu modülün formüllerini uygular, `pdftotext`
ile metni çıkarır, content_type'ı basit sezgisel kurallarla tahmin eder (kesin
değilse `--content-type` ile ezilebilir), ve yukarıdaki JSON'u yazar. İnsan
onayı gerektirmez — CLAUDE.md §3 "scene candidates" yetkisi kapsamındadır.
Kullanıcı bir sonraki PDF'i attığında ilk adım budur.

---

## 10. NE ZAMAN İNSANA SORULUR (bu modül bunu değiştirmiyor)

M17 §13 ve CLAUDE.md §7 hâlâ tam geçerli: hikaye anlamı, karakter/ses kimliği,
ilk sahne onayı, master export, `E-LEG-*` ve bütçe hard-stop hâlâ insan
onayı gerektirir. Bu modül SADECE "kaç sahne, ne kadar video" sorusunu insana
sormaktan çıkarıyor — hikayenin NE anlattığını değil.

---

## KALİTE KONTROL NOTU (dürüstlük ilkesi)

Bu modül **taslaktır** çünkü kalibrasyon verisi 3 projeyle sınırlı — istatistiksel
olarak küçük bir örneklem. Her yeni proje bittiğinde §7 tablosu güncellenecek;
6-8 projeden sonra sabitler (avg_scene_length_s aralıkları, video_ratio_target)
daha güvenilir hale gelecek. O zamana kadar bu modülün çıktısı bir **başlangıç
noktası**dır, kör uygulanacak bir kural değil — beklenmedik bir sahne sayısı/süre
çıkarsa (örn. hesaplanan sahne sayısı M17 §5'in 8-90s sınırlarını sistematik
ihlal ediyorsa) bu bir modül hatasıdır, sessizce görmezden gelinmez, kullanıcıya
bildirilir (CLAUDE.md law #4 "no silent degradation").

## ACCEPTANCE CRITERIA

- Her `scene_plan.json` çıktısı `content_type`, `reasoning` ve `calibration_module`
  alanlarını içerir — bir sayı, gerekçesiz üretilmez (CLAUDE.md law #4).
- Hesaplanan ortalama sahne uzunluğu M17 §5 sınırlarının (8–90s) dışındaysa
  çıktı bunu `reasoning` içinde açıkça işaretler, sessizce geçmez.
- `encyclopedic_atlas` çıktısı `episode_count` alanını ve "bu süre TEK BİR
  bölüm içindir" notunu içerir — toplam seri süresiyle karıştırılmaz.
- §7 kalibrasyon tablosu her yeni proje tamamlandığında bir satır büyür;
  sabitler (avg_scene_length_s, video_ratio_target, DELIVERED_WPM) o veriyle
  güncellenir, tahminle değil.
- `ai_video_count_target`/`image_count_target` kullanan her çıktı, bu sayıların
  §7b'de "doğrulanmadı" işaretli kullanıcı-verilen hedeflerden geldiğini
  gizlemez — ilk gerçek render sonrası §7b satırları §7'ye taşınır.

**SONRAKİ MODÜL:** yok (bu, en yeni modül)

**CHANGELOG**
- v0.2 (2026-08-07) — Kullanıcı somut, süre-bazlı çapa noktaları verdi (60dk→20
  AI-video, 30dk→10-15, 10-15dk→5; 15dk→100 görsel). §6b/§6c eklendi:
  `ai_video_count_target`/`image_count_target` artık sahne-sayısından bağımsız,
  toplam-süre-bazlı mutlak hedefler — `research_documentary`/`narrative_history`
  için §6'nın yüzde modelinin yerine geçiyor. §6d eklendi: PDF-içi-görsel kaynak
  dalı (M14 §5 image pipeline'ının ilk kod implementasyonu,
  `scripts/extract_pdf_images.py`), kullanıcının "atlas PDF gibi" örneğiyle
  tetiklendi (541 gömülü raster obje, `pdfimages -list` ile doğrulandı).
  M17/M21 entegrasyonu ayrı bir bölümde netleştirildi. §7b: yeni hedefler
  henüz gerçek render'la doğrulanmadı, dürüstçe ayrı işaretlendi.
- v0.1 (2026-08-07) — Taslak oluşturuldu. Kullanıcı talebi üzerine, M17 §5/§7'nin
  sahne-sayısı ve video-oranı boşluğunu dolduruyor. 3 tamamlanmış projeden
  (Başkurtlar, Dağların Uyuyan Devleri, Gök Umay Atlası) kalibrasyon verisi
  çıkarıldı. M17 §7'nin still-ağırlıklı varsayılanı, Flow'un artık birincil
  ve düşük-maliyetli video kaynağı olması nedeniyle video-öncelikli olarak
  güncellendi; Higgsfield sadece karmaşık/yüksek-hareketli sahneler için
  ayrıldı (kullanıcı onayı kuralı korunuyor).
