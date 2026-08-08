# DEC-0002 — kalan 12 ninni için görsel üretmeden, mevcut görselleri yeniden kullanma

`schemas/decision.schema.json`'ın `question` enum'u burada da bir görsel
küratörlük kararını kapsamıyor (DEC-0001'deki gibi), bu yüzden yine düz
not.

**Soru:** İlk 10 ninninin dışındaki 12 ninni (Altay, Saha, Karaçay-Malkar,
Anadolu, Hakas, Başkurt, Nogay, Gagauz, Irak Türkmenleri/Kerkük, Şor,
Uygur, Ahıska) için 20'şer görsellik set nasıl tamamlanacak?

**Seçim:** Yeni görsel üretmeden, üç kaynaktan yeniden kullanım:
1. **Kendi** — her ninninin `ninniler-part2` Kaggle dataset'inde zaten
   üretilmiş 4-7 kendine özgü coğrafi/atmosfer görseli.
2. **Ödünç** — akraba kültür/coğrafyadan (ör. Sibirya-Altay-Sayan kümesi
   için Tuva'nın kendi coğrafi görselleri; Kafkasya kümesi için
   Azerbaycan'ınkiler; İpek Yolu kümesi için Özbek'inkiler) 2-5 görsel.
3. **Ortak havuz** — ilk 10'un ortak anne/beşik/bebek/yurt-içi/gaz lambası
   görsellerinden (116 benzersiz dosya) doldurma.

Kullanıcının kendi gözlemi ("birçok ninnide aynı ton ve görseller var")
doğrultusunda — bu üç kaynak birlikte her ninniyi eksiksiz 20'ye
tamamlıyor, hiçbiri için yeni prompt gerekmedi. Dağılım (`kendi+ödünç+havuz`):

| Ninni | Kendi | Ödünç | Havuz |
|---|---|---|---|
| Altay | 7 | 4 (Tuva) | 9 |
| Saha | 6 | 3 (Tuva) | 11 |
| Hakas | 5 | 3 (Tuva) | 12 |
| Şor | 4 | 3 (Tuva) | 13 |
| Karaçay-Malkar | 6 | 3 (Azerbaycan) | 11 |
| Ahıska | 4 | 2 (Azerbaycan) | 14 |
| Uygur | 5 | 4 (Özbek) | 11 |
| Nogay | 4 | 5 (Kazak+Karakalpak) | 11 |
| Başkurt | 5 | 4 (Tatar+Çuvaş) | 11 |
| Gagauz | 4 | 2 (Azerbaycan) | 14 |
| Anadolu | 6* | 2 (Kırım Tatarı) | 12 |
| Kerkük | 5* | 2 (Özbek) | 13 |

\* Anadolu ve Kerkük'ün "kendi" sayısına, ilk turda hiçbir ninniye
uymadığı için hariç tutulan 2 "outlier" görsel de dahil (Anatolian
village → Anadolu; Kerkük Kalesi → Kerkük) — bunlar çöp değilmiş,
sadece henüz sırası gelmemiş görsellermiş.

**Reddedilen alternatif:** Her 12 ninni için sıfırdan ~15-16 yeni prompt
yazıp ürettirmek (12×15≈180 yeni görsel). Kullanıcının kendi gözlemiyle
tutarsız olurdu (zaten örtüşen ton/coğrafyayı görmezden gelip gereksiz
tekrar üretim), ve bu stüdyonun "cost is a constraint" ilkesine (madde 6)
aykırı düşerdi.

**Bilinen ödün (madde 4 gereği açıkça işaretleniyor, gizlenmiyor):** Havuz
payı yüksek olan ninniler (Gagauz, Ahıska, Şor: %65-70 ortak havuz) diğer
ninnilerle görsel olarak daha fazla örtüşecek — art arda izleyen biri bunu
fark edebilir. Özellikle **Gagauz**'un kendine özgü tonu (Balkan/Ortodoks)
en zayıf temsil edilen — ileride ayrı bir görsel tur gerekirse ilk aday
burası olmalı.
