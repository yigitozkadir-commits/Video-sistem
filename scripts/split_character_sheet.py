#!/usr/bin/env python3
"""
Splits a composite Higgsfield character/unit reference sheet (one 1024x1536
PNG containing a turnaround grid, face detail, equipment closeups, palette
swatch, and mood/context illustrations all on one canvas) into individual
crop files.

Why this exists: schemas/character_sheet.schema.json's canonical_refs
already assumes per-angle reference images (M15 §9.1 example:
["REF-CHR-001-front", "REF-CHR-001-three-quarter", "REF-CHR-001-profile"]),
but nothing in the repo produced them - source sheets arrive as one
multi-panel composite. This crops each useful panel out, in three
disposition classes:
  - REF-CHR-*: hero pose, turnaround angles, face detail (character identity)
  - REF-OBJ-*: equipment/weapon/armor closeups, reusable independent of the
    character
  - REF-PAL-*: colour palette swatch, when the sheet has one
  - mood/context: scene illustrations (battle, daily life, unit formation)
    catalogued via image_catalog.schema.json instead of the REF-* namespace,
    since they're not immutable identity references, just B-roll mood refs.

Crop boxes are keyed by LAYOUT (the sheet's panel arrangement), not by
individual character - sheets sharing a layout (e.g. all Yeniçeri variants)
reuse the same coordinates. New layouts (future parts) get a new entry in
LAYOUTS below.

Usage:
    python3 scripts/split_character_sheet.py
Reads CHARACTERS below, writes crops + character_sheet/*.json +
state/reference_catalog.jsonl under projects/PRJ-fetih-1453/.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).parent.parent
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-fetih-1453"
REF_DIR = PROJECT_DIR / "assets" / "reference"
SOURCE_DIR = REF_DIR / "_source"
MOOD_DIR = PROJECT_DIR / "assets" / "reference" / "mood"

# box = (left, top, right, bottom) in source-sheet pixels (all sheets are 1024x1536)
LAYOUTS = {
    "yeniceri": {
        "ref_chr": {
            "hero": (185, 10, 465, 775),
            "front": (505, 60, 630, 400),
            "side": (630, 60, 750, 400),
            "back": (750, 60, 875, 400),
            "three_quarter": (875, 60, 1005, 400),
            "face": (505, 435, 705, 710),
        },
        "ref_obj": {
            "equipment_detail": (705, 435, 1010, 710),
            "weapons": (5, 1113, 285, 1295),
            "armor": (288, 1113, 505, 1295),
            "personal_details": (508, 1113, 755, 1295),
            "costume_detail": (758, 1113, 1010, 1295),
            "symbol": (848, 1310, 1010, 1495),
        },
        "ref_pal": {},
        "identity": {
            "hair": (5, 1010, 285, 1108),
            "eyes": (288, 1010, 605, 1108),
            "skin": (608, 1010, 1010, 1108),
        },
        "mood": {
            "unit_formation": (5, 1310, 285, 1495),
            "battle_pose": (288, 1310, 605, 1495),
            "daily_life": (608, 1310, 845, 1495),
        },
    },
    "acemi": {
        "ref_chr": {
            # this sheet's hero figure overlaps the left text sidebar in the
            # source composite (no clean vertical seam like the other
            # layouts) - cropped as tight as possible, a text sliver may
            # still bleed in on the left edge
            "hero": (175, 10, 375, 720),
            "front": (410, 60, 535, 375),
            "side_right": (535, 60, 660, 375),
            "back": (660, 60, 785, 375),
            "side_left": (785, 60, 910, 375),
            "three_quarter": (910, 60, 1010, 375),
            "face": (410, 410, 595, 715),
        },
        "ref_obj": {
            "equipment_detail": (600, 410, 1010, 715),
            "weapons_armor": (5, 745, 410, 1010),
        },
        "ref_pal": {"palette": (675, 1375, 1010, 1450)},
        "identity": {},
        "mood": {
            "sword_training": (5, 1055, 185, 1215),
            "bow_training": (190, 1055, 405, 1215),
            "discipline_training": (410, 1055, 605, 1215),
            "endurance_training": (608, 1055, 795, 1215),
            "meal_rest": (798, 1055, 1010, 1215),
            "unit_formation": (5, 1255, 355, 1400),
            "battle_prep": (360, 1255, 600, 1400),
        },
    },
    "lagimci": {
        "ref_chr": {
            # same left-sidebar overlap quirk as azap/acemi - tightened, some
            # text may still bleed in on the left edge
            "hero": (180, 15, 460, 770),
            "front": (505, 60, 635, 360),
            "side_right": (635, 60, 755, 360),
            "back": (755, 60, 880, 360),
            "side_left": (880, 60, 1005, 360),
            "face": (505, 390, 715, 715),
        },
        "ref_obj": {
            "equipment_detail": (715, 390, 1015, 715),
            "tools": (5, 755, 650, 950),
        },
        "ref_pal": {"palette": (830, 1450, 1010, 1530)},
        "identity": {},
        "mood": {
            "digging_work": (5, 995, 205, 1160),
            "reinforcement_setup": (207, 995, 405, 1160),
            "gunpowder_placement": (407, 995, 605, 1160),
            "tunnel_support": (607, 995, 805, 1160),
            "explosion_prep": (807, 995, 1010, 1160),
            "sapper_camp": (5, 1195, 355, 1385),
            "tunnel_interior": (360, 1195, 655, 1385),
            "wall_breach": (660, 1195, 1010, 1385),
        },
    },
    "azap": {
        "ref_chr": {
            # same left-sidebar overlap quirk as acemi/lagimci - tightened,
            # some text may still bleed in on the left edge
            "hero": (175, 10, 395, 590),
            "front": (420, 60, 555, 360),
            "side_right": (555, 60, 680, 360),
            "back": (680, 60, 800, 360),
            "side_left": (800, 60, 920, 360),
            "three_quarter": (920, 60, 1010, 360),
            "face": (395, 383, 555, 700),
        },
        "ref_obj": {
            "equipment_detail": (555, 383, 1010, 700),
            "weapons_armor": (5, 700, 545, 950),
        },
        "ref_pal": {"palette": (395, 1455, 545, 1530)},
        "identity": {},
        "mood": {
            "battle_scene_1": (5, 1005, 258, 1165),
            "battle_scene_2": (260, 1005, 513, 1165),
            "battle_scene_3": (515, 1005, 766, 1165),
            "battle_scene_4": (768, 1005, 1010, 1165),
            "vanguard_advance": (5, 1205, 258, 1335),
            "ambush_setup": (260, 1205, 508, 1335),
            "reconnaissance": (510, 1205, 763, 1335),
            "harassing_enemy": (765, 1205, 1010, 1335),
            "unit_order": (5, 1345, 255, 1450),
            "unit_in_formation": (255, 1345, 540, 1450),
            "camp_life": (540, 1345, 775, 1450),
            "on_the_march": (775, 1345, 1010, 1450),
        },
    },
    "topcu": {
        "ref_chr": {
            "hero": (170, 10, 415, 660),
            "front": (440, 60, 565, 380),
            "side_right": (565, 60, 685, 380),
            "back": (685, 60, 810, 380),
            "side_left": (810, 60, 930, 380),
            "three_quarter": (930, 60, 1005, 380),
            "face": (440, 415, 635, 700),
        },
        "ref_obj": {
            "equipment_detail": (640, 415, 1005, 700),
            "cannons": (5, 740, 555, 860),
            "tools": (5, 865, 1005, 1000),
        },
        "ref_pal": {"palette": (850, 1250, 1005, 1420)},
        "identity": {},
        "mood": {
            "gun_placement": (5, 1020, 205, 1200),
            "powder_transport": (207, 1020, 405, 1200),
            "powder_prep": (407, 1020, 605, 1200),
            "firing": (607, 1020, 805, 1200),
            "ammo_prep": (807, 1020, 1005, 1200),
            "usage_scene": (5, 1235, 355, 1420),
            "unit_formation": (360, 1235, 565, 1420),
        },
    },
    "lagimci2": {
        "ref_chr": {
            "hero": (185, 15, 415, 610),
            "front": (460, 60, 585, 355),
            "side_right": (585, 60, 705, 355),
            "back": (705, 60, 825, 355),
            "side_left": (825, 60, 940, 355),
            "three_quarter": (940, 60, 1005, 355),
            "face": (460, 390, 635, 715),
        },
        "ref_obj": {
            "equipment_detail": (640, 390, 1010, 715),
            "tools": (5, 750, 635, 955),
        },
        "ref_pal": {"palette": (410, 1440, 560, 1510)},
        "identity": {},
        "mood": {
            "tunnel_digging": (5, 1015, 172, 1180),
            "soil_removal": (174, 1015, 341, 1180),
            "reinforcement_setup": (343, 1015, 510, 1180),
            "gunpowder_placement": (512, 1015, 679, 1180),
            "ignition_prep": (681, 1015, 848, 1180),
            "tunnel_collapse": (850, 1015, 1010, 1180),
            "usage_areas": (5, 1215, 375, 1400),
            "tunnel_interior": (400, 1215, 690, 1400),
            "unit_formation": (715, 1215, 1010, 1400),
        },
    },
    "sipahi": {
        "ref_chr": {
            "hero": (175, 10, 410, 630),  # tightened, left-sidebar text overlap
            "front": (440, 60, 560, 330),
            "side_right": (560, 60, 680, 330),
            "back": (680, 60, 800, 330),
            "side_left": (800, 60, 905, 330),
            "three_quarter": (905, 60, 1005, 330),
            "face": (440, 365, 620, 690),
        },
        "ref_obj": {
            "equipment_detail": (625, 365, 1005, 690),
            "weapons_armor": (5, 725, 375, 1005),
            "horse_gear": (380, 725, 625, 1005),
            "symbols_flags": (800, 1420, 1010, 1500),
        },
        "ref_pal": {"palette": (615, 1420, 795, 1495)},
        "identity": {},
        "mood": {
            "cavalry_charge": (5, 1035, 205, 1230),
            "spear_assault": (207, 1035, 405, 1230),
            "flank_attack": (407, 1035, 620, 1230),
            "archery": (622, 1035, 825, 1230),
            "breaking_enemy": (827, 1035, 1010, 1230),
            "open_field_battle": (5, 1265, 205, 1390),
            "flank_guard": (207, 1265, 405, 1390),
            "commander_guard": (407, 1265, 620, 1390),
            "reconnaissance": (622, 1265, 825, 1390),
            "pursuit": (827, 1265, 1010, 1390),
        },
    },
    "akinci": {
        "ref_chr": {
            "hero": (180, 15, 405, 660),  # tightened, left-sidebar text overlap
            "front": (440, 60, 565, 355),
            "side_right": (565, 60, 685, 355),
            "back": (685, 60, 805, 355),
            "side_left": (805, 60, 925, 355),
            "three_quarter": (925, 60, 1005, 355),
            "face": (440, 390, 635, 715),
        },
        "ref_obj": {
            "equipment_detail": (640, 390, 1005, 715),
            "weapons_armor": (5, 750, 555, 970),
        },
        "ref_pal": {"palette": (230, 1375, 395, 1450)},
        "identity": {},
        "mood": {
            "scouting": (5, 1035, 205, 1180),
            "raid": (207, 1035, 405, 1180),
            "archery": (407, 1035, 605, 1180),
            "retreat": (607, 1035, 805, 1180),
            "fast_attack": (807, 1035, 1010, 1180),
            "reconnaissance_duty": (5, 1215, 205, 1340),
            "harassing_enemy": (207, 1215, 405, 1340),
            "communication": (407, 1215, 605, 1340),
            "night_raids": (607, 1215, 805, 1340),
            "clearing_path": (807, 1215, 1010, 1340),
            "horse_and_gear": (5, 1375, 225, 1500),
        },
    },
    "aksemsettin": {
        "ref_chr": {
            "hero": (235, 20, 410, 600),  # tightened further, deep left-sidebar text overlap
            "front": (460, 55, 580, 330),
            "side_right": (580, 55, 695, 330),
            "back": (695, 55, 810, 330),
            "side_left": (810, 55, 905, 330),
            "three_quarter": (905, 55, 1005, 330),
            "face": (460, 365, 635, 675),
        },
        "ref_obj": {
            "equipment_detail": (640, 365, 1005, 675),
            "clothing_items": (5, 760, 405, 975),
        },
        "ref_pal": {"palette": (5, 1345, 285, 1415)},
        "identity": {},
        "mood": {
            "meeting_with_fatih": (5, 1005, 205, 1145),
            "conquest_prayer": (207, 1005, 405, 1145),
            "scholarly_council": (407, 1005, 605, 1145),
            "state_council": (607, 1005, 805, 1145),
            "humility_with_people": (807, 1005, 1010, 1145),
            "topkapi_palace": (5, 1175, 205, 1310),
            "scholars_council_room": (207, 1175, 405, 1310),
            "library_study": (407, 1175, 605, 1310),
            "eyup_sultan_lodge": (607, 1175, 805, 1310),
            "among_the_people": (807, 1175, 1010, 1310),
        },
    },
}

# Gallery sheets: multiple named/generic officials as single portraits (no
# turnaround) on one sheet. layout = shared column geometry, portraits =
# panel-name -> box for just the seated-portrait crop (above the caption).
GALLERIES = {
    "gallery1": {
        "source": "file_00000000dc1c8243bae5df73ba79abf3.png",
        "sheet_title": "Osmanlı Devlet Adamları - İlim, Hikmet, Adalet (profil galerisi 1)",
        "portraits": {
            "vizir_i_azam": (5, 705, 172, 885),
            "kazasker": (174, 705, 341, 885),
            "nisanci_basi": (343, 705, 510, 885),
            "defterdar": (512, 705, 679, 885),
            "katip_celebi": (681, 705, 848, 885),
            "seyhulislam": (850, 705, 1010, 885),
        },
        # role -> (name_or_None, note) - None name = generic role archetype,
        # no specific historical individual claimed
        "meta": {
            "vizir_i_azam": (None, "Jenerik rol arketipi, isim/tarih verilmemiş."),
            "kazasker": (None, "Jenerik rol arketipi, isim/tarih verilmemiş."),
            "nisanci_basi": (None, "Jenerik rol arketipi, isim/tarih verilmemiş."),
            "defterdar": (None, "Jenerik rol arketipi, isim/tarih verilmemiş."),
            "katip_celebi": (
                "Kâtip Çelebi",
                "İsim verilmiş ama bu sayfada tarih yok.",
            ),
            "seyhulislam": (None, "Jenerik rol arketipi, isim/tarih verilmemiş."),
        },
    },
    "gallery2": {
        "source": "file_00000000714481f49554adbdc66b59cb.png",
        "sheet_title": "Osmanlı Devlet Adamları - Âlimler, Danışmanlar ve Devlet Yöneticileri (profil galerisi 2)",
        # this gallery's description paragraph is longer and overlaps the
        # portrait further down than gallery1's - narrowed to skip most of it
        "portraits": {
            "seyhulislam_molla_fenari": (5, 760, 172, 865),
            "candarli_halil_pasa": (174, 760, 341, 865),
            "mahmud_pasa": (343, 760, 510, 865),
            "defterdar_ornek": (512, 760, 679, 865),
            "nisanci_ornek": (681, 760, 848, 865),
            "katip_celebi_2": (850, 760, 1010, 865),
        },
        "meta": {
            "seyhulislam_molla_fenari": (
                "Şeyhülislam Molla Fenari (?-1431)",
                "Gerçek tarihi kişi, tarihler 1453 fetih dönemiyle uyumlu (öncesinde vefat etmiş olsa da dönemin makam sahibi figürlerinden).",
            ),
            "candarli_halil_pasa": (
                "Çandarlı Halil Paşa (1360-1457)",
                "Gerçek tarihi kişi, II. Mehmed döneminin sadrazamı - tarihler 1453 fethiyle uyumlu.",
            ),
            "mahmud_pasa": (
                "Mahmud Paşa (ö. 1474)",
                "Gerçek tarihi kişi, Fatih Sultan Mehmed döneminde vezirlik yapmış - tarihler uyumlu.",
            ),
            "defterdar_ornek": (None, "Sayfada açıkça '(Örnek)' olarak işaretli - jenerik arketip, gerçek bir kişiyi temsil etmiyor."),
            "nisanci_ornek": (None, "Sayfada açıkça '(Örnek)' olarak işaretli - jenerik arketip, gerçek bir kişiyi temsil etmiyor."),
            "katip_celebi_2": (
                "Kâtip Çelebi (1609-1657)",
                "TARİHSEL TUTARSIZLIK: Kâtip Çelebi gerçek bir Osmanlı bilgini ama 1609-1657 yıllarında yaşamış - 1453 fethinden ~150 yıl SONRA doğmuş, "
                "bu dönemin devlet adamı olamaz. Sayfa onu diğer 1453-dönemi figürleriyle aynı galeriye yanlışlıkla yerleştirmiş. "
                "Video planlaması aşamasında bu figürün 1453 bağlamından çıkarılması gerekir - ben içerik/anlatım kararı veremem, kullanıcıya bildiriyorum.",
            ),
        },
    },
}

# character_id -> (source filename in scratch extract dir, layout, title, role)
CHARACTERS = {
    "CHR-001": {
        "source": "file_0000000007c8820aacf5fc58bc69642c.png",
        "layout": "yeniceri",
        "title": "Yeniçeri (sarışın, kırmızı-altın üniforma)",
        "role": "Yeniçeri",
        "period": "16. yüzyıl - Osmanlı İmparatorluğu",
        "hair": "Doğal sarı, hafif dalgalı, orta uzunluk",
        "eyes": "Mavi",
        "skin": "Açık",
    },
    "CHR-002": {
        "source": "file_000000009c4c8243be6a60f5a050cb3a.png",
        "layout": "yeniceri",
        "title": "Yeniçeri (sarışın, lacivert-altın üniforma)",
        "role": "Yeniçeri",
        "period": "16. yüzyıl - Osmanlı İmparatorluğu",
        "hair": "Sarı, dalgalı, 6-8 cm",
        "eyes": "Mavi",
        "skin": "Açık buğday",
    },
    "CHR-003": {
        "source": "file_000000002fc081f498c6858e71a25256.png",
        "layout": "yeniceri",
        "title": "Yeniçeri (siyah saçlı, bıyıklı, kırmızı-altın üniforma)",
        "role": "Yeniçeri",
        "period": "16. yüzyıl - Osmanlı İmparatorluğu",
        "hair": "Siyah, düz, 6-8 cm",
        "eyes": "Koyu kahverengi",
        "skin": "Buğday",
    },
    "CHR-004": {
        "source": "file_00000000879482468890912ac85d6d93.png",
        "layout": "acemi",
        "title": "Yeniçeri Acemi Ocağı",
        "role": "Acemi Ocağı (eğitim aşaması)",
        "period": "15. yüzyıl (1453)",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-005": {
        "source": "file_000000007ed48246963ad63ac497dace.png",
        "layout": "lagimci",
        "title": "Lağımcılar (Osmanlı kuşatma mühendisleri)",
        "role": "Lağımcı",
        "period": "15. yüzyıl",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-006": {
        "source": "file_0000000070c48246834ef7b0a99abe45.png",
        "layout": "azap",
        "title": "Azaplar (Osmanlı hafif piyade birliği)",
        "role": "Azap",
        "period": "15. yüzyıl (1453)",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-007": {
        "source": "file_0000000045d881f497798af33ee920d2.png",
        "layout": "topcu",
        "title": "Topçular (Osmanlı topçu birliği)",
        "role": "Topçu",
        "period": "15. yüzyıl (1453)",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-008": {
        "source": "file_00000000ddb481f4bf531a5028f4d49d.png",
        "layout": "lagimci2",
        "title": "Lağımcılar (varyant 2 - farklı üretim/kompozisyon)",
        "role": "Lağımcı",
        "period": "15. yüzyıl (1453)",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-009": {
        "source": "file_00000000f39881f4a3ecbd7f486e13f4.png",
        "layout": "sipahi",
        "title": "Sipahi (Osmanlı kapıkulu süvari birliği)",
        "role": "Sipahi",
        "period": "15. yüzyıl (1453)",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-010": {
        "source": "file_0000000029b8820ab292d8d449a20519.png",
        "layout": "akinci",
        "title": "Akıncı (Osmanlı hafif süvari birliği)",
        "role": "Akıncı",
        "period": "15. yüzyıl (1453)",
        "hair": None, "eyes": None, "skin": None,
    },
    "CHR-011": {
        "source": "file_0000000083d081f48b08b7e90a93bda5.png",
        "layout": "aksemsettin",
        "title": "Akşemsettin (1389-1459) - gerçek tarihi kişi",
        "role": "Osmanlı devlet adamı, âlim ve danışman (Fatih Sultan Mehmed'in manevi hocası)",
        "period": "1389-1459 (1453 fethinde manevi danışman)",
        "hair": None, "eyes": None, "skin": None,
        "historical": True,
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def crop_and_save(im: Image.Image, box: tuple, out_path: Path) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop = im.crop(box)
    crop.save(out_path)
    return {
        "path": str(out_path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(out_path),
        "width": crop.width,
        "height": crop.height,
    }


def main(source_extract_dir: Path) -> None:
    REF_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    ref_entries = []       # -> reference_asset.schema.json (REF-CHR/OBJ/PAL)
    image_entries = []     # -> image_catalog.schema.json (mood/context illustrations)
    next_ref_num = {"CHR": 1, "OBJ": 1, "PAL": 1}
    next_ast_num = 1
    character_sheets = []

    def new_asset_id() -> str:
        nonlocal next_ast_num
        aid = f"AST-IMG-{next_ast_num:06d}"
        next_ast_num += 1
        return aid

    for char_idx, (char_id, meta) in enumerate(CHARACTERS.items(), start=1):
        src_path = source_extract_dir / meta["source"]
        if not src_path.exists():
            print(f"SKIP {char_id}: source not found ({src_path})")
            continue
        layout = LAYOUTS[meta["layout"]]
        im = Image.open(src_path).convert("RGB")

        # archive the untouched source sheet, give it its own asset_id so
        # every crop's derived_from can point at a real AST- id (schema
        # requires derived_from to be an AST- id or null, not a free object)
        archived = SOURCE_DIR / f"{char_id}_{meta['source']}"
        if not archived.exists():
            im.save(archived)
        archived_sha = sha256_file(archived)
        source_asset_id = new_asset_id()

        canonical_refs = []

        def add_ref(prefix: str, panel: str, box: tuple) -> str:
            ref_id = f"REF-{prefix}-{next_ref_num[prefix]:03d}"
            next_ref_num[prefix] += 1
            out = REF_DIR / f"{ref_id}_{char_id}_{panel}.png"
            info = crop_and_save(im, box, out)
            ref_entries.append({
                "reference_id": ref_id,
                "asset_id": new_asset_id(),
                "class": {"CHR": "character", "OBJ": "object", "PAL": "palette"}[prefix],
                "path": info["path"],
                "sha256": info["sha256"],
                "immutable": True,
                "derived_from": source_asset_id,
                "notes": f"{char_id} ({meta['role']}) - panel: {panel}",
            })
            return ref_id

        for panel, box in layout["ref_chr"].items():
            canonical_refs.append(add_ref("CHR", panel, box))
        for panel, box in layout["ref_obj"].items():
            add_ref("OBJ", panel, box)
        for panel, box in layout["ref_pal"].items():
            add_ref("PAL", panel, box)

        for panel, box in layout["mood"].items():
            out = MOOD_DIR / f"{char_id}_{panel}.png"
            info = crop_and_save(im, box, out)
            image_entries.append({
                "asset_id": new_asset_id(),
                "page": char_idx,
                "sha256": info["sha256"],
                "class": "illustration",
                "caption_nearby": panel.replace("_", " "),
                "scores": {
                    "narrative_relevance": 70,
                    "visual_quality": 85,
                    "resolution_adequacy": 60,
                    "reuse_potential": 60,
                    "reference_value": 75,
                },
                "disposition": "REFERENCE_ONLY",
                "rationale": (
                    f"Higgsfield kompozit karakter sayfasından ({char_id}, {meta['role']}) "
                    f"mekanik olarak kırpıldı; mood/context referansı, henüz insan gözden "
                    f"geçirmesi yapılmadı - scores placeholder tahminlerdir."
                ),
            })

        id_bits = [f"{k}: {v}" for k, v in
                   (("hair", meta["hair"]), ("eyes", meta["eyes"]), ("skin", meta["skin"]))
                   if v]
        identity_tokens = "; ".join(id_bits) if id_bits else meta["role"]

        character_sheets.append({
            "character_id": char_id,
            "name": meta["title"],
            "identity_tokens": identity_tokens,
            "canonical_refs": canonical_refs,
            "locked": False,
            "role": meta["role"],
            "period": meta["period"],
            "is_named_historical_figure": bool(meta.get("historical", False)),
            "source_sheet_ref": {
                "path": str(archived.relative_to(REPO_ROOT)),
                "sha256": archived_sha,
            },
        })
        print(f"{char_id} ({meta['layout']}): "
              f"{len(layout['ref_chr'])} REF-CHR, {len(layout['ref_obj'])} REF-OBJ, "
              f"{len(layout['ref_pal'])} REF-PAL, {len(layout['mood'])} mood")

    # Gallery sheets: several officials as single seated portraits on one
    # sheet (no turnaround per person - only one pose exists for each).
    next_gallery_chr = len(CHARACTERS) + 1
    for gallery_key, gallery in GALLERIES.items():
        src_path = source_extract_dir / gallery["source"]
        if not src_path.exists():
            print(f"SKIP gallery {gallery_key}: source not found ({src_path})")
            continue
        im = Image.open(src_path).convert("RGB")
        archived = SOURCE_DIR / f"GALLERY-{gallery_key}_{gallery['source']}"
        if not archived.exists():
            im.save(archived)
        archived_sha = sha256_file(archived)
        gallery_asset_id = new_asset_id()

        for panel, box in gallery["portraits"].items():
            char_id = f"CHR-{next_gallery_chr:03d}"
            next_gallery_chr += 1
            name, note = gallery["meta"][panel]
            ref_id = f"REF-CHR-{next_ref_num['CHR']:03d}"
            next_ref_num["CHR"] += 1
            out = REF_DIR / f"{ref_id}_{char_id}_{panel}_portrait.png"
            info = crop_and_save(im, box, out)
            ref_entries.append({
                "reference_id": ref_id,
                "asset_id": new_asset_id(),
                "class": "character",
                "path": info["path"],
                "sha256": info["sha256"],
                "immutable": True,
                "derived_from": gallery_asset_id,
                "notes": f"{char_id} - {gallery['sheet_title']}, panel: {panel}. {note}",
            })
            character_sheets.append({
                "character_id": char_id,
                "name": name or f"{panel.replace('_', ' ').title()} (jenerik rol arketipi)",
                "identity_tokens": note,
                "canonical_refs": [ref_id],
                "locked": False,
                "role": panel.replace("_", " "),
                "is_named_historical_figure": name is not None,
                "source_sheet_ref": {
                    "path": str(archived.relative_to(REPO_ROOT)),
                    "sha256": archived_sha,
                },
            })
        print(f"gallery {gallery_key}: {len(gallery['portraits'])} portrait characters")

    char_dir = PROJECT_DIR / "state" / "character_sheets"
    char_dir.mkdir(parents=True, exist_ok=True)
    for cs in character_sheets:
        (char_dir / f"{cs['character_id']}.json").write_text(
            json.dumps(cs, indent=2, ensure_ascii=False) + "\n"
        )

    ref_catalog_path = PROJECT_DIR / "state" / "reference_catalog.jsonl"
    with open(ref_catalog_path, "w") as f:
        for entry in ref_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    image_catalog_path = PROJECT_DIR / "state" / "image_catalog.json"
    image_catalog_path.write_text(json.dumps(
        {"project_id": "PRJ-fetih-1453", "images": image_entries},
        indent=2, ensure_ascii=False,
    ) + "\n")

    print(f"\nWrote {len(character_sheets)} character_sheets, "
          f"{len(ref_entries)} reference_asset entries -> {ref_catalog_path}, "
          f"{len(image_entries)} image_catalog entries -> {image_catalog_path}")


if __name__ == "__main__":
    import sys
    source_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if source_dir is None:
        print("Usage: split_character_sheet.py <source_extract_dir>")
        sys.exit(1)
    main(source_dir)
