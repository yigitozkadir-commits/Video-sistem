# Gök Umay Stüdyo Sistemi — Kurulum (Claude Code için)

Bu zip, Gök Umay AI Sesli Kitap/Video Stüdyosu'nun **çalışan tüm sistemini**
içerir: bible modülleri, şemalar, şablonlar, stil profilleri, tüm
scriptler, marka varlıkları (ses/palet presetleri + kapanış logosu) ve
Remotion render şablonu. Bitmiş video projeleri (Avrasya, Ryskulov,
Başkurtlar, Atlas, Dağların Uyuyan Devleri) BİLEREK dahil edilmedi — onlar
bu sistemin ürünüydü, sistemin kendisi değil, ve dosyaları çok büyük
(gigabaytlarca). Bu zip yalnızca YENİDEN KULLANILABİLİR MOTORu taşıyor.

## Claude Code, bu dosyayı okuyorsan yapman gerekenler (sırayla)

1. Bu zip'i repo kök dizinine aç (zaten açılmışsa bu adımı atla).
2. `bash scripts/install.sh` çalıştır — dizin iskeletini kurar, gerekli
   araçları (python3, ffmpeg, ffprobe, node, kaggle CLI) kontrol eder,
   `requirements.txt`'ten Python bağımlılıklarını kurar, `.env.example`'ı
   `.env`'e kopyalar.
3. `python3 scripts/validate.py` çalıştır — 0 hata vermeli. Vermiyorsa
   önce onu düzelt, devam etme.
4. `CLAUDE.md`'yi oku — bu dosya sistemin giriş noktası, senin "rolünü"
   ve hangi görevde hangi bible modüllerini yükleyeceğini tanımlıyor.
   Section 1 "Bounded context" kısmı özellikle önemli: her görevde
   TÜM bible'ı yükleme, sadece görev + M12/M13 (kernel/QA, her zaman) +
   ilgili rol modülünü (M14/M15/M16/M17) yükle.
5. Kullanıcıya (bu hesabın sahibine) şunu sor veya kendiliğinden anlat:
   `.env` içindeki API anahtarlarının (ElevenLabs, gerekiyorsa Google
   Flow) henüz DOLDURULMADIĞINI, gerçek üretim yapmadan önce
   doldurulması gerektiğini.
6. Yeni bir proje başlatılacaksa `INSTALL.md`'deki "Start a project"
   bölümünü ve `README.md`'deki "Starting a new project" bölümünü takip
   et — `scripts/remotion_setup.sh PRJ-<id>` ile `remotion_template/`'i
   yeni projeye kopyala, `scripts/scaffold_ryskulov_project.py` veya
   `scaffold_baskurtlar_project.py`'nin desenini yeni projeye uyarla.

## Neden bu kadar "kendi kendini anlatan" bir paket

Bu sistemin kendi kuralı (CLAUDE.md madde 8): "`studio why <artifact>`
loglardan cevaplanabilmeli — hangi görev, hangi prompt sürümü, hangi seed,
hangi karar, hangi QA raporu." Bu paket de aynı ilkeyle hazırlandı: her
script'in docstring'i NEDEN o şekilde yazıldığını (genelde gerçek bir
production kazası/bug'dan çıkarılmış bir ders olarak) açıklıyor —
`scripts/kaggle_dataset_upload.py`, `scripts/append_studio_outro.py`,
`remotion_template/src/compositions/StudioComposition.tsx` özellikle
dikkatli okunmalı, çünkü her biri gerçek bir üretim hatasının
düzeltmesini içeriyor.

## Kısa içerik özeti

- `bible/` — 22 modül + mimari inceleme (sistemin yasası)
- `schemas/` — 35 JSON Schema (her ajan-arası kontrat)
- `templates/` — 18 üretim ön ayarı (kanal formatları, içerik kuralları)
- `style/` — 14 görsel stil profili
- `prompts/` — versiyonlu prompt nesneleri + eksen kütüphanesi
- `reports/` — kanal-format-istihbarat raporları (CFP-*)
- `scripts/` — 33 Python scripti + kütüphane (scaffold, narration,
  sahne-veri üretimi, render-öncesi kontrol listeleri, Kaggle teslimi,
  doğrulama)
- `brand/` — stüdyo kimliği (ses/palet presetleri + imza kapanış klibi)
- `remotion_template/` — kanonik Remotion kompozisyon iskeleti
- `projects/_scaffold/` + `projects/project.example.json` — yeni proje
  şablonu
- `.github/workflows/render.yml` — isteğe bağlı CI paralel render
  workflow'u

Detaylar için `README.md` (İngilizce, daha ayrıntılı) ve `INSTALL.md`'ye
bak.
