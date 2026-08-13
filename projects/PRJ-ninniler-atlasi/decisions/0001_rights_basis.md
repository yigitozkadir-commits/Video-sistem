# DEC-0001 — rights.source_basis = "owned"

`schemas/decision.schema.json`'ın `question` enum'u (scene_length,
camera_choice, video_or_still, ...) bir haklar/rights belirleme sorusunu
kapsamıyor — bu yüzden bu kayıt JSON şema-doğrulamalı bir `decision`
nesnesi değil, düz bir not. `project.json`'ın `rights.evidence_ref` alanı
buraya işaret ediyor.

**Soru:** `project.json`'daki `rights.source_basis` ne olmalı?

**Seçim:** `"owned"`

**Gerekçe:** Kaynak metin (`Ninniler_Atlasi_Faz1-5.docx`,
`Ninniler_Metinler.docx`) kullanıcının/Gök Umay projesinin kendi akademik
derlemesi — kamuya açık ikincil kaynaklardan (ansiklopedi maddeleri,
akademik makaleler, folklor arşivleri) sentezlenmiş özgün bir rapor,
üçüncü tarafın telifli bir kitabının/PDF'inin taranması değil. Tüm 275
görsel (200 + 75) Flow ile üretilen orijinal illüstrasyonlar, gerçek bir
fotoğrafın/çizimin kopyası değil.

**Reddedilen alternatifler:**
- `"unknown"` — CLAUDE.md madde 4 gereği sistemi durdurur
  (`HOLD_LEGAL`); ama burada gerçekten belirsiz değil, kaynağın
  kullanıcının kendi derlemesi olduğu konuşma bağlamından açık.
- `"public_domain"` — ninni sözlerinin kendisi (Kazak, Kırgız vb.
  orijinal metinler) muhtemelen kamu malı/folklor, ama Faz1-5
  raporlarının derleme/sentez metni ve üretilen görseller değil; bu
  etiket kaynağın tamamını yanlış tanımlar.

**Güven düzeyi:** Bu benim (Claude Code) çıkarımım, hukuki bir doğrulama
değil — kullanıcı yanlış olduğunu düşünürse `project.json`'da tek satır
değiştirilir.
