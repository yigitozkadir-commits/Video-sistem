#!/usr/bin/env python3
"""
Scaffold generator for PRJ-ryskulov-mektubu. Follows scaffold_baskurtlar_project.py's
pattern: a Python list of 46 scene dicts -> scenes/SC-*.json + prompts_used/<shot_id>/
{image,video}.json against schemas/scene.schema.json + CLAUDE.md §5b's dual-prompt rule.

Source: input/RYSKULOV_ARASTIRMA_RAPORU.docx (prose research report - source_text below
is close to its actual sentences, not the PDF's terse scene-plan bullet points, which are
visual/timing directions only). Scene structure/timing/visual direction follows
input/RYSKULOV_VIDEO_PLANI_46_SAHNE.pdf's 46-scene plan exactly (9 bölüm + açılış + kapanış).

Production-mode decisions (see project.json decisions_log for full reasoning, user-approved
via AskUserQuestion 2026-08-07):
  - Flow-image/video-weighted production (like Avrasya/Başkurtlar), NOT Remotion-native
    data-viz components - user's explicit choice over the Plan agent's original recommendation.
  - Statistic-heavy scenes (SC-018..023, SC-044) get an EXTRA negative-prompt clause banning
    baked-in chart labels/readable numbers - exact figures live ONLY in the spoken narration,
    never asked of the image generator (Avrasya's specimen-label defect is the direct lesson:
    Flow reliably bakes in wrong/garbled text when a prompt implies data/documentation labels).
  - style/archival_restrained_documentary.json's forbidden list (no human bodies/corpses/
    execution/reenactment) applies to every single prompt below - this is a mass-death subject.
  - AI-video kept minimal (2 of 46 scenes: SC-002 hook, SC-046 closing) per project.json's
    decisions_log - this content is text-card/quote/portrait/atmosphere driven, not motion-heavy.

Numbers are spelled out in Turkish AT WRITE TIME (not patched after TTS generation) - this
project is far more numeral-dense than Başkurtlar was, so the fix is applied inline in each
source_text below rather than via a separate NUMBER_FIXES table (harder to keep in sync for
this many distinct figures; inline is the safer default here). main() still runs a blanket
regex assert at the end - a bare digit anywhere is a scaffolding bug, not a style choice.

Re-running this script overwrites scenes/*.json and prompts_used/*/*.json - it's a generator,
not a mutation log.

Usage:
    python3 scripts/scaffold_ryskulov_project.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.production_ledger import _task_id  # noqa: E402

PROJECT_ID = "PRJ-ryskulov-mektubu"
PROJECT_DIR = REPO_ROOT / "projects" / PROJECT_ID
STATE_DIR = PROJECT_DIR / "state"
FPS = 30
WPM = 125  # TPL-ryskulov-hybrid narrator pace

PV_WIDE = "PV-0044"
PV_CLOSEUP = "PV-0031"

STYLE_TAG = "archival_restrained_documentary"
GRADE = "cool grey and faded sepia, low saturation, measured and heavy, not horror-dark"
GRAIN = "period paper/photograph texture where relevant, otherwise clean and unstylised"
PALETTE = "cool grey, faded sepia, carbon black"

NEGATIVE_BASE = (
    "human figures, human faces, portraits of people, photographs of people, "
    "corpses, starving or emaciated human bodies, execution scenes, "
    "any graphic depiction of death or violence, weapons, reenactment, dramatization, "
    "heroic or romantic framing, modern objects out of period, ethnic/costume symbolism, "
    "text, watermark, extra fingers, warped face, plastic skin, camera shake, "
    "oversaturation, anime stylisation, lens flare, "
    # v3 fix (2026-08-08): SC-025's "abstract illegible seal and typewriter
    # text" wording still produced a fully legible "OFFICIAL DECREE" title
    # plus a readable "OFFICIAL SEAL STAMP" ring on a red wax seal, 2/2
    # candidates - same defect class as the portrait fix above (a stated
    # positive-prompt intent for illegibility isn't reliably honored,
    # needs an explicit negative-prompt ban too).
    "readable document titles, legible letterhead text, legible heading text, "
    "legible seal or stamp text, legible title text, "
    # v5 fix (2026-08-08): SC-016's "sealed envelope marked for the
    # Kremlin's attention" produced an anachronistic Imperial double-headed
    # eagle wax seal AND a fully legible Russian stamp reading the prompt's
    # own meaning. SC-042's "blank label" folder printed "FILE NO." /
    # "OFFICIAL FILE" + a fabricated accession number 2/3 times.
    "wax seal emblem, heraldic seal, imperial eagle, tsarist emblem, "
    "folder label text, file tab text, accession number, catalog code, "
    "shelf location tag, section number tag, "
    # v6 fix (2026-08-08): SC-031's "handwritten journal page, ink strokes
    # urgent and uneven" produced fully legible English sentences on the
    # page ("so cold... they're taking us... where are we... fear... no
    # food left... the dark...") - same defect class again (stated
    # illegibility in the positive prompt isn't honored), and here the
    # leaked text also directly named the exact traumatic content the
    # style profile's forbidden list excludes from visuals.
    "legible handwriting, readable journal entries, readable diary text, "
    "legible cursive writing, readable sentences, any invented words on paper"
)
# Extra clause for statistic-heavy scenes - exact figures live only in narration audio,
# never in the image (Avrasya's specimen-label defect: Flow bakes in wrong/garbled text
# whenever a prompt implies a data label, chart, or document reading as legible).
NEGATIVE_STATS_EXTRA = (
    ", readable chart labels, readable numbers, data tables, infographic text, axis labels, "
    "any invented legible text baked into the image"
)

REQUIRED_SUFFIX = (
    "no people, no corpses, no readable text, no chart labels, no numbers, "
    "documentary archival aesthetic, muted and restrained, not sensationalized --style raw"
)

SCENES = [
    # ============================= AÇILIŞ (1-4) =============================
    dict(
        n=1, title="Jenerik / Başlık", scene_type="opening", visual="reuse", reuse_ref=None,
        source_text="",  # title card, no narration - silent, typography only (precedent: Avrasya SC-002)
        citation_ref=None, reliability_badge=None,
    ),
    dict(
        n=2, title="Açılış sorusu", scene_type="opening", visual="video",
        search_keywords=None,  # abstract archive/envelope texture - no real photograph fits a hook line
        source_text=(
            "Tarihte bazı belgeler vardır — iktidarın bildiği ama görmezden geldiği, halkın "
            "yaşadığı ama söyleyemediği gerçeği bir anda yüzeye çıkaranlar. Turar Ryskulov'un "
            "dokuz Mart bin dokuz yüz otuz üç tarihli mektubu bu belgelerden biridir."
        ),
        pv=PV_CLOSEUP,
        subject="a sealed archive folder or envelope, closed, resting on a bare desk, faint official seal visible",
        environment="dim archive room, heavy shadow around the edges of frame",
        lighting="single_desk_lamp",
        camera="push_in.slow", lens="normal", motion="minimal, dust drifting in the lamp light",
        citation_ref=None, reliability_badge=None,
    ),
    dict(
        n=3, title="Bağlam cümlesi", scene_type="explanation", visual="still",
        search_keywords="Kazakhstan steppe winter empty",
        source_text=(
            "Kazakistan'da bin dokuz yüz otuz ile bin dokuz yüz otuz üç yılları arasında yaşanan "
            "büyük kıtlık — Aşarşılık — milyonlarca insanın hayatını kaybetmesine yol açtı. Ama bu "
            "felakete ilişkin resmi Sovyet arşivleri büyük ölçüde kapalıydı."
        ),
        pv=PV_WIDE,
        subject="an empty winter steppe landscape at low light, flat horizon, no figures",
        environment="open Kazakh steppe under a pale winter sky",
        lighting="low_winter_light",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref=None, reliability_badge="KESIN",
    ),
    dict(
        n=4, title="Rapor çerçevesi", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Bu video; mektubun yazılış sürecini, içeriğini, Stalin'in tepkisini ve tarihsel "
            "önemini ele alıyor. Kazakistan e-history.kz arşivi, Sciences Po ve Wilson Center "
            "kaynaklarına dayanmaktadır."
        ),
        pv=PV_CLOSEUP,
        subject="a plain archive folder tab and index card, unreadable abstract typewriter marks only",
        environment="archive shelf edge, shallow depth of field",
        lighting="even_archive_lighting",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Kazakistan e-history.kz, Sciences Po Mass Violence, Wilson Center",
        reliability_badge="KESIN",
    ),
    # ============================= BÖLÜM I (5-9) =============================
    dict(
        n=5, title="Ryskulov'un tanıtımı", scene_type="explanation", visual="still",
        search_keywords="Turar Ryskulov",
        source_text=(
            "Turar Ryskulov, bin sekiz yüz doksan dörtte sıradan bir Kazak ailesinde doğdu. "
            "Bolşevik Devrimi'nin fırsatlarından yararlanarak hızla Sovyet sisteminin üst "
            "kademelerine yükseldi. Kazak tarihinin en yetenekli ve en trajik figürlerinden "
            "biri olarak tanınır."
        ),
        pv=PV_CLOSEUP,
        # v2 fix (2026-08-08): original wording ("period portrait photograph
        # texture") reliably pulled Flow into generating a full human face/figure
        # despite the shared negative prompt banning it - confirmed 3/3 on this
        # exact wording across SC-005/030/033. Rewritten to an empty archival
        # object (blank photo mount, no photograph inside) - implies "there is a
        # portrait on file" without ever depicting one.
        subject="an empty oval photo mount on an aged archival card, the photograph itself missing or removed, only the blank recessed frame visible",
        environment="archival card mounted on a shelf, dim even light",
        lighting="even_archive_lighting",
        camera="static", lens="portrait", motion="none - still frame",
        citation_ref="Nicolas Werth (2003), Ryskulov'un 1997 külliyatı",
        reliability_badge="KESIN",
    ),
    dict(
        n=6, title="Siyasi kariyer", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Türkistan Sovyet Cumhuriyeti'nde Merkez Yürütme Komitesi başkanlığı ve Müslüman "
            "Büro yöneticiliği görevlerini üstlendi. En önemli pozisyonu, Rusya Sovyet Federatif "
            "Sosyalist Cumhuriyeti Başkan Yardımcılığı'ydı — bu görevde on bir yıl kaldı."
        ),
        pv=PV_CLOSEUP,
        subject="a plain typed document listing official titles, abstract illegible typewriter texture, no readable words",
        environment="official desk, single document under lamp light",
        lighting="single_desk_lamp",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Ryskulov'un 1997 külliyatı",
        reliability_badge="KESIN",
    ),
    dict(
        n=7, title="Eşik konumu", scene_type="explanation", visual="reuse", reuse_ref=6,
        source_text=(
            "Hem bir Sovyet yetkilisi hem de Kazak bir aydın olarak bulunduğu bu eşik konumu, ona "
            "hem Sovyet merkezine yakın olma hem de yerel gerçekleri doğrudan gözlemleme imkânı "
            "verdi."
        ),
        citation_ref=None, reliability_badge="GUCLU_CIKARIM",
    ),
    dict(
        n=8, title="Ryskulov'un çelişkisi", scene_type="conflict", visual="still",
        search_keywords=None,
        source_text=(
            "Ryskulov kolektifleştirme politikasını başlangıçta destekledi — onu Kazak "
            "ekonomisini modernize etme fırsatı olarak gördü. Ama bu politikanın uygulanma "
            "biçiminin felakete yol açtığını kendi gözleriyle izledi. Bu çelişki mektubun "
            "tonuna da yansımaktadır: Ryskulov, Stalin'e bir muhalif olarak değil, sisteme "
            "inanan bir Sovyet yetkilisi olarak yazmaktadır."
        ),
        pv=PV_WIDE,
        subject="an abstract split composition, one half pale winter light, other half deep shadow, no figure, symbolic divide",
        environment="a plain neutral wall or screen, sharp division of light and dark",
        lighting="single_desk_lamp",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref=None, reliability_badge="GUCLU_CIKARIM",
    ),
    dict(
        n=9, title="Tarihsel not kutusu", scene_type="explanation", visual="reuse", reuse_ref=42,
        source_text=(
            "Tarihsel not — Ryskulov, mektubu yazmasına rağmen bin dokuz yüz otuz yedide Stalin'in "
            "Büyük Terörü sırasında tutuklandı ve bin dokuz yüz otuz sekizde kurşuna dizildi."
        ),
        citation_ref=None, reliability_badge="KESIN",
    ),
    # ============================= BÖLÜM II (10-14) =============================
    dict(
        n=10, title="1930-1932: Artan felaket, süregelen sessizlik", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "OGPU — Sovyet gizli polisi — ve bölge düzeyindeki yürütme komiteleri, kitlesel göç "
            "ve artan ölüm oranlarına ilişkin kapsamlı raporlar sunmaya başlamıştı. Bu raporlar "
            "merkeze ulaşıyordu. Ama önemsenmedi."
        ),
        pv=PV_CLOSEUP,
        subject="a stack of plain manila report folders, closed, abstract carbon-copy paper texture, no legible text",
        environment="an office in-tray, muted grey light",
        lighting="overcast_diffused",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="OGPU raporları, Sarah Cameron 'The Hungry Steppe'",
        reliability_badge="KESIN",
    ),
    dict(
        n=11, title="Goloshchekin'in çarpıtması", scene_type="conflict", visual="reuse", reuse_ref=10,
        source_text=(
            "Bin dokuz yüz otuz birde Goloshchekin şunu ilan etti: köyünü hiç terk etmemiş Kazak, "
            "artık bölgeden bölgeye seyahat ediyor, kolhozlara katılıyor, iş değiştiriyor. Gerçekte "
            "yaşanan ölümler ve kaçışlar, başarı olarak sunuluyordu."
        ),
        citation_ref="Goloshchekin'in bin dokuz yüz otuz bir açıklaması",
        reliability_badge="KESIN",
    ),
    dict(
        n=12, title="Temmuz 1932: Beşlerin Mektubu", scene_type="discovery", visual="still",
        search_keywords="Gabit Musrepov",
        source_text=(
            "Temmuz bin dokuz yüz otuz ikide beş önde gelen Kazak aydın — Gabit Musrepov, Mansur "
            "Gataulin, Mutash Davletgaliyev, Yembergen Altynbekov ve Kadyr Kuanyshev — ortak bir "
            "itiraz mektubu kaleme aldı: Beşlerin Mektubu."
        ),
        pv=PV_CLOSEUP,
        subject="five plain document pages fanned out on a bare desk, abstract illegible typewriter marks, no readable names",
        environment="official desk, muted daylight",
        lighting="overcast_diffused",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref="Beşlerin Mektubu, 5 Temmuz bin dokuz yüz otuz iki",
        reliability_badge="KESIN",
    ),
    dict(
        n=13, title="Beşlerin Mektubu'nun akıbeti", scene_type="conflict", visual="reuse", reuse_ref=12,
        source_text=(
            "Mektuptan: \"Tek amacımız Kazakistan'daki sosyalist inşaya yardım etmek, bazı "
            "ciddi aksaklıkları işaret etmek ve bizi ilgilendiren meseleleri doğrudan Bölge "
            "Komitesi'ne, parti demokrasisi çerçevesinde Bolşevikçe biçimde sunmaktır.\" Beş "
            "Temmuz bin dokuz yüz otuz iki toplantısında mektubun yazarları milliyetçilikle "
            "suçlandı; partiden ihraç ve cezai kovuşturma tehdidiyle karşı karşıya kaldılar."
        ),
        citation_ref="Bölge Komitesi Bürosu toplantı kararı, 5 Temmuz bin dokuz yüz otuz iki",
        reliability_badge="KESIN",
    ),
    dict(
        n=14, title="Eylem alanının daralması", scene_type="explanation", visual="reuse", reuse_ref=17,
        source_text=(
            "Beşlerin Mektubu'nun bu şekilde karşılanması, açıkça itiraz etmenin ne denli "
            "tehlikeli olduğunu gösterdi; ama felaketin boyutları öyle büyümüştü ki suskunluk "
            "artık sürdürülemez hale geldi. Bu koşullarda Ryskulov farklı bir strateji izledi: "
            "Goloshchekin'e değil doğrudan Stalin'e, bir eleştiri değil bilgi notu biçiminde "
            "yazmaya karar verdi."
        ),
        citation_ref=None, reliability_badge="GUCLU_CIKARIM",
    ),
    # ============================= BÖLÜM III (15-24) =============================
    dict(
        n=15, title="29 Eylül 1932: İlk not", scene_type="discovery", visual="still",
        search_keywords=None,
        source_text=(
            "Yirmi dokuz Eylül bin dokuz yüz otuz ikide Ryskulov'un Stalin'e ilk resmi bildirimi "
            "gönderildi — hayvancılık sektöründeki dramatik düşüşü belgeleyen, temkinli dilli bir "
            "not. Sistemin dili kullanılıyordu: sorunlar, düzeltmeler, iyileştirme önerileri. Ama "
            "altındaki mesaj netti — Kazakistan'da bir şeyler çok yanlış gitmekteydi."
        ),
        pv=PV_CLOSEUP,
        subject="a single typewritten page, abstract illegible marks, dated corner visible but unreadable, resting on a plain desk",
        environment="official desk, single lamp",
        lighting="single_desk_lamp",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Ryskulov'un ilk notu, 29 Eylül bin dokuz yüz otuz iki",
        reliability_badge="KESIN",
    ),
    dict(
        # v4 "vurucu sahne" pass (2026-08-08): this is the film's title
        # artifact - the actual March 9 1933 letter - and it was reusing
        # SC-015's generic typewritten-page shot like a dozen other scenes
        # do. User feedback ("video sade oldu") plus a direct scene-by-scene
        # pass found this specific miss: the one document the whole
        # documentary is named after had no distinctive visual of its own.
        # Given its own dedicated still, deliberately more elevated framing
        # (directional light, sealed formal envelope) than the routine
        # desk-lamp document shots used elsewhere.
        n=16, title="9 Mart 1933: Asıl mektup", scene_type="discovery", visual="still",
        search_keywords=None,
        source_text=(
            "Asıl belge dokuz Mart bin dokuz yüz otuz üç tarihini taşır. Sciences Po Mass Violence "
            "araştırma ağı bu mektubu kıtlığın ilk resmi kabulünü sağlayan belge olarak "
            "nitelendirmektedir."
        ),
        pv=PV_CLOSEUP,
        # v5 fix (2026-08-08): "sealed formal envelope marked for the
        # Kremlin's attention" produced 2/2 defects - an anachronistic
        # Imperial double-headed-eagle wax seal (wrong era for a 1933
        # Soviet document) AND, worse, a fully legible Russian stamp
        # reading "ДЛЯ ДОКЛАДА В КРЕМЛЬ" ("for report to the Kremlin") -
        # Flow rendered the PROMPT'S OWN MEANING as baked-in text. Same
        # lesson as the portrait/decree fixes: don't describe what a mark
        # says or implies, describe an object with no mark to read at all.
        subject="a single unmarked envelope, no seal, no stamp, no visible writing, resting alone in a hard shaft of directional light against deep shadow",
        environment="an otherwise bare desk, dramatic single-source light",
        lighting="single_desk_lamp",
        camera="push_in.slow", lens="macro", motion="slow push in",
        citation_ref="Sciences Po Mass Violence araştırma ağı",
        reliability_badge="KESIN",
    ),
    dict(
        n=17, title="Mektubun açılışı", scene_type="discovery", visual="still",
        search_keywords=None,
        source_text=(
            "\"Bu notu okumanızı ve bu meseleye müdahale etmenizi istiyorum; böylece açlığa "
            "mahkûm edilmiş pek çok insanın hayatını kurtarabilirsiniz.\" — Turar Ryskulov, "
            "Stalin'e Mektup, dokuz Mart bin dokuz yüz otuz üç."
        ),
        pv=PV_CLOSEUP,
        subject="an old typewriter, a single sheet halfway rolled in, abstract illegible type on the page",
        environment="a bare desk, single overhead light",
        lighting="single_desk_lamp",
        camera="push_in.slow", lens="macro", motion="minimal, subtle key vibration as if just struck",
        citation_ref="Ryskulov'un mektubu, dokuz Mart bin dokuz yüz otuz üç",
        reliability_badge="KESIN",
    ),
    dict(
        n=18, title="Bölgesel rakamlar", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Mektubun en çarpıcı bölümü, Kazakistan'ın farklı bölgelerinden derlenen somut "
            "demografik verilerdir. Bu rakamlar soyut değil, kişisel gözlem ve yerel raporlara "
            "dayanmaktadır: Aktubinsk bölgesinde yüzde yirmi sekiz kayıp, Kızılorda'da yüzde "
            "seksen ile seksen beş arası kayıp, Balkaş bölgesinde yüzde seksen kayıp."
        ),
        pv=PV_WIDE,
        subject="an empty flat winter steppe landscape stretching to the horizon, no figures, no readable overlay",
        environment="open Kazakh steppe, muted grey sky",
        lighting="overcast_diffused",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref="Ryskulov'un mektubu, bölgesel demografik veriler",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=19, title="Kyzylorda vurgusu", scene_type="explanation", visual="reuse", reuse_ref=18,
        source_text=(
            "Kızılorda rakamı özellikle çarpıcıdır: nüfusun yalnızca yüzde on beş ile yirmisi "
            "yerinde kalmıştır. Bu, yüzde seksenin üzerinde bir kayıp anlamına gelir — ölüm ya "
            "da kaçış yoluyla."
        ),
        citation_ref="Ryskulov'un mektubu, Kızılorda verisi",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=20, title="Cumhuriyet dışına kaçış rakamları", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Mektup, Kazakistan dışına kaçan Kazakların dağılımını da belgeler: Orta Volga, "
            "Kırgızistan, Batı Sibirya, Kara-Kalpak, Orta Asya, Çin, İran ve Afganistan yönünde. "
            "Bu veriler hem felaketin boyutunu hem de yayılma coğrafyasını göstermesi açısından "
            "kritik öneme sahiptir."
        ),
        pv=PV_WIDE,
        subject="an abstract empty map surface texture, aged paper, faint unreadable ink lines, no labels or legible place names",
        environment="a flat archival map laid on a desk, top-down view",
        lighting="single_desk_lamp",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref="Ryskulov'un mektubu, göç dağılımı verisi",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=21, title="Toplam göç: 1 milyon+", scene_type="explanation", visual="reuse", reuse_ref=20,
        source_text=(
            "Bir milyondan fazla Kazak cumhuriyet dışına kaçtı. Altı yüz on altı bini bir daha "
            "geri dönmedi — Kazak nüfusunun büyük bölümünün yerinden edildiğini gösteren bir "
            "rakam."
        ),
        citation_ref="Ryskulov'un mektubu, göç toplamı",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=22, title="Hayvan varlığı verisi", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Bir Ocak bin dokuz yüz otuz üç itibarıyla Kazakistan'da yalnızca dört buçuk milyon "
            "baş hayvan kalmıştı. Kolektifleştirme arifesinde bu rakam kırk buçuk milyondu — "
            "Kazak ekonomisinin omurgası fiilen yok edilmişti."
        ),
        pv=PV_CLOSEUP,
        subject="an empty winter pasture, bare frozen ground, no animals, no figures, muted grey light",
        environment="open steppe pasture, frost visible on the ground",
        lighting="low_winter_light",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref="Ryskulov'un mektubu, hayvan varlığı verisi",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=23, title="Ölü sayısı verisi", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Kazakistan e-history.kz arşivinin yıl yıl verilerine göre kayıplar şöyledir: bin "
            "dokuz yüz otuzda üç yüz on üç bin kişi öldü; bin dokuz yüz otuz birde yedi yüz elli "
            "beş bin kişi öldü; bin dokuz yüz otuz ikide yedi yüz altmış dokuz bin kişi öldü — "
            "toplamda iki milyon yüz bin kişi. Cameron, Kindler ve Ohayon gibi diğer akademik "
            "kaynaklar ise daha muhafazakâr bir tahminle bir buçuk milyon ölü rakamını "
            "benimsemektedir; ölüm ve göç rakamlarının birbirinden ayrıştırılması güçlüğü, kesin "
            "bir sayım yapılmasını engellemektedir."
        ),
        pv=PV_CLOSEUP,
        subject="a large ledger book left open on a bare table, blank ruled pages with no numbers or names visible, an inkwell gone dry beside it",
        environment="an archive table, weak overhead light",
        lighting="overcast_diffused",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Kazakistan e-history.kz arşivi; Cameron/Kindler/Ohayon karşılaştırması",
        reliability_badge="TARTISMALI",
        stats_scene=True,
    ),
    dict(
        n=24, title="Mektubun tonu ve stratejisi", scene_type="explanation", visual="reuse", reuse_ref=15,
        source_text=(
            "Mektup bir suçlama değil, bir bilgi notu biçiminde kaleme alınmıştır. Goloshchekin "
            "doğrudan hedef gösterilir; ama merkezi otorite — Stalin — doğrudan eleştirilmez. Bu "
            "ton, hem hayatta kalma güdüsünün hem de gerçeği anlatma sorumluluğunun ürünüdür."
        ),
        citation_ref=None, reliability_badge="GUCLU_CIKARIM",
    ),
    # ============================= BÖLÜM IV (25-29) =============================
    dict(
        n=25, title="Mektubun etkisi", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Sciences Po'ya göre mektup, kıtlığın ilk resmi kabulünü sağladı ve somut önlemlere "
            "zemin hazırladı: altı yüz altmış beş bin kişinin iadesini öngören yeniden yerleşim "
            "operasyonu, tahıl yardımı, göçebelere yeniden özel hayvan mülkiyeti hakkı tanıyan "
            "kararname."
        ),
        pv=PV_CLOSEUP,
        # v3 fix (2026-08-08): "official decree document" + "seal" wording
        # reliably produced a legible "OFFICIAL DECREE" title and readable
        # seal-ring text (2/2), despite asking for illegibility - see
        # NEGATIVE_BASE's matching v3 note. Rewritten to a blank-faced
        # object (paper turned away, ink smudge instead of a seal) that
        # doesn't imply a document title exists to be read at all.
        subject="a plain aged paper sheet turned face-down, only the blank reverse side visible, a faint dark ink smudge where a seal impression bled through, resting under lamp light",
        environment="official desk, single overhead light",
        lighting="single_desk_lamp",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Sciences Po Mass Violence araştırma ağı",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=26, title="Goloshchekin'in görevden alınması", scene_type="explanation", visual="reuse", reuse_ref=25,
        source_text=(
            "Goloshchekin, Ocak bin dokuz yüz otuz üçte — mektuptan önce — görevden alındı; "
            "sorumluluk merkezi otoriteden uzaklaştırıldı. Bu görevden alma, hem mektupların "
            "birikmesinin hem de Beşlerin Mektubu'nun birikimli etkisinin bir ürünüdür."
        ),
        citation_ref=None, reliability_badge="GUCLU_CIKARIM",
    ),
    dict(
        n=27, title="\"Yeterli miydi?\" — Hayır", scene_type="conflict", visual="still",
        search_keywords=None,
        source_text=(
            "Yale Uluslararası Araştırmalar Dergisi'nde yayımlanan çalışma şunu ortaya koyar: "
            "Stalin, Kazak halkının kitlesel acılarından bin dokuz yüz otuz ile bin dokuz yüz "
            "otuz iki döneminde en az üç kez haberdar edildi. Buna rağmen tahıl ve et tedarik "
            "kotaları sürdürüldü."
        ),
        pv=PV_WIDE,
        subject="an empty winter steppe road stretching to a flat horizon, no figures, muted overcast light",
        environment="a bare unpaved road across open steppe",
        lighting="low_winter_light",
        camera="pull_out.slow", lens="wide", motion="none - still frame",
        citation_ref="Yale Uluslararası Araştırmalar Dergisi",
        reliability_badge="KESIN",
    ),
    dict(
        n=28, title="Stalin'in özel yazışmaları", scene_type="conflict", visual="reuse", reuse_ref=25,
        source_text=(
            "Sovyet arşivlerinden elde edilen belgeler, Stalin'in iç yazışmalarında \"baskı "
            "hattı\" ifadesini kullandığını ortaya koyar. İki yüzden az ilçenin otuz ikisi kara "
            "listeye alındı — Ukrayna'daki uygulamalarla paralel bir yöntem."
        ),
        citation_ref="Sovyet arşiv belgeleri, Stalin'in iç yazışmaları",
        reliability_badge="KESIN",
    ),
    dict(
        n=29, title="Dile getirilen ifade", scene_type="emotional_pause", visual="still",
        search_keywords=None,
        source_text=(
            "Sovyet yetkilileri gizli notlarında Kazakları \"iki bacaklı kurtlar\" olarak "
            "tanımlamıştır — felaket döneminde Sovyet yönetiminin tutumunu çarpıcı biçimde "
            "özetleyen bir ifade."
        ),
        pv=PV_WIDE,
        subject="a single bare winter tree, stripped and dead-looking, alone on an empty snow-covered plain, heavy storm clouds gathering",
        environment="open Kazakh steppe, no other features",
        lighting="low_winter_light",
        camera="static", lens="wide", motion="none - still frame",
        min_duration_s=6.0,
        citation_ref="Sovyet yetkilileri gizli notları",
        reliability_badge="GUCLU_CIKARIM",
    ),
    # ============================= BÖLÜM V (30-33) =============================
    dict(
        n=30, title="Uraz Isaev'in mektupları", scene_type="explanation", visual="still",
        search_keywords="Uraz Isaev",
        source_text=(
            "Ryskulov'dan önce, Goloshchekin tarafından atanan Kazakistan Halk Komiserleri "
            "Konseyi Başkanı Uraz Isaev de Stalin'e mektuplar yazdı — merkezi partiye ulaşan ilk "
            "resmi uyarılardan biri, ama etkisi sınırlı kaldı."
        ),
        pv=PV_CLOSEUP,
        # v2 fix (2026-08-08): see SC-005's identical fix note - "portrait
        # photograph" wording reliably produces a human face despite the
        # negative prompt.
        subject="a closed archival dossier folder with a blank nameplate, no photograph visible, tied shut with cord",
        environment="archival shelf, dim even light",
        lighting="even_archive_lighting",
        camera="static", lens="portrait", motion="none - still frame",
        citation_ref=None, reliability_badge="KESIN",
    ),
    dict(
        # v4 "vurucu sahne" pass: tagged emotional_pause but was reusing
        # SC-012's generic "five documents fanned on desk" - no distinct
        # treatment for the single most sensitive testimony in the film
        # (a witness account of seeing corpses on the road - the content
        # itself is banned from the image per style forbidden list, but the
        # visual should still mark this as a different KIND of document:
        # a personal handwritten account written while travelling, not an
        # official typed report).
        n=31, title="Gabit Musrepov'un tanıklığı", scene_type="emotional_pause", visual="still",
        search_keywords=None,
        source_text=(
            "Beşlerin Mektubu'nun imzacılarından yazar Gabit Musrepov, ülkeyi gezerek kıtlığın "
            "yıkımını gördü. Turgay bölgesi yollarında pek çok cesetle karşılaştığını, ölçülü "
            "bir dille aktarmıştır; bu tanıklık, Kazak yazınında sansürden kaçabilmiş nadir "
            "belgelerden biridir."
        ),
        pv=PV_CLOSEUP,
        subject="a single journal page covered in dense abstract ink scratches and pressure marks, no legible words, paper texture and ink density implying urgency rather than any readable writing, resting closed on a fold-down travel table",
        environment="a train compartment interior, a frost-covered window beside it, empty winter landscape blurred outside",
        lighting="low_winter_light",
        camera="static", lens="macro", motion="none - still frame",
        min_duration_s=6.0,
        citation_ref="Gabit Musrepov'un tanıklığı",
        reliability_badge="KESIN",
    ),
    dict(
        n=32, title="Kazak ders kitaplarındaki yorumu", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Kazak lise tarih ders kitapları bu mektupları yalnızca uyarı olarak değil, Sovyet "
            "iktidarına karşı bir direniş eylemi olarak da sunmaktadır. Bu yorum, belgelerin "
            "Kazak ulusal hafızasındaki yerini göstermesi açısından önemlidir."
        ),
        pv=PV_CLOSEUP,
        subject="a stack of worn hardcover schoolbooks, blank spines, no readable titles, resting on a plain wooden desk",
        environment="a classroom desk, daylight from a side window",
        lighting="overcast_diffused",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Tandfonline akademik çalışması, Kazak ders kitapları",
        reliability_badge="GUCLU_CIKARIM",
    ),
    dict(
        n=33, title="Oraz Jandosov'un çelişkili konumu", scene_type="conflict", visual="still",
        search_keywords="Oraz Jandosov",
        source_text=(
            "Kazak komünist yetkili Oraz Jandosov, yerleşim yerlerini gezerek defnedilmemiş "
            "cesetlerle karşılaştığını aktardı; ama öte yandan kolektifleştirmeyi savunmaya da "
            "devam etti — dönemin Kazak aydınlarının imkânsız durumunu özetleyen bir çelişki."
        ),
        pv=PV_CLOSEUP,
        # v2 fix (2026-08-08): see SC-005's fix note.
        subject="a plain archival record card in a filing tray, blank ruled lines, no photograph, no portrait",
        environment="archival shelf, dim even light",
        lighting="even_archive_lighting",
        camera="static", lens="portrait", motion="none - still frame",
        citation_ref="Oraz Jandosov'un gözlemleri",
        reliability_badge="GUCLU_CIKARIM",
    ),
    # ============================= BÖLÜM VI (34-37) =============================
    dict(
        n=34, title="Sovyet döneminde sansür", scene_type="explanation", visual="still",
        search_keywords=None,
        source_text=(
            "Ryskulov mektubu ve diğer kıtlık belgeleri, glasnost dönemine — bin dokuz yüz "
            "seksenlerin sonuna — kadar Sovyet arşivlerinde gömülü kaldı. \"Büyük jüt yılları\" "
            "ifadesi bile hassas bir tabuydu."
        ),
        pv=PV_CLOSEUP,
        subject="a locked archive cabinet drawer, dust visible, dim light, no readable label",
        environment="a dim archive storage room",
        lighting="single_desk_lamp",
        camera="static", lens="normal", motion="none - still frame",
        citation_ref="Nicolas Werth (2003)",
        reliability_badge="KESIN",
    ),
    dict(
        n=35, title="Akademik keşif süreci", scene_type="discovery", visual="reuse", reuse_ref=5,
        source_text=(
            "Belgelere akademik erişim, Sovyetler'in çöküşünden sonra mümkün oldu. Tarihçi "
            "Nicolas Werth, iki bin üçte Communisme dergisinde yayımladığı çalışmayla Ryskulov "
            "mektubunu Batı akademisine sistematik biçimde tanıttı — bu, mektubu Batı "
            "akademisine tanıtan ilk kapsamlı çalışmadır."
        ),
        citation_ref="Nicolas Werth, Communisme dergisi, iki bin üç",
        reliability_badge="KESIN",
    ),
    dict(
        n=36, title="1997 külliyatı", scene_type="discovery", visual="reuse", reuse_ref=34,
        source_text=(
            "Ryskulov'un üç ciltlik seçilmiş eserlerinin bin dokuz yüz doksan yedide Kazakistan'da "
            "yayımlanması, mektubun orijinal metinlerine erişimi kolaylaştıran kritik bir dönüm "
            "noktasıydı."
        ),
        citation_ref="Ryskulov'un 1997 külliyatı",
        reliability_badge="KESIN",
    ),
    dict(
        n=37, title="Arşivlerin hâlâ kapalı olması", scene_type="conflict", visual="reuse", reuse_ref=34,
        source_text=(
            "Cambridge Üniversitesi'nden tarihçi Sarah Cameron'a göre Kazakistan'ın gizli polis "
            "arşivleri ve Goloshchekin'in kişisel dosyaları bugün hâlâ araştırmacıların büyük "
            "çoğunluğuna kapalıdır. Bu durum, kıtlığın tam boyutuna ve kasıt meselesine ilişkin "
            "soruların kesin bir yanıt bulmasını hâlâ engellemektedir."
        ),
        citation_ref="Sarah Cameron, 'The Hungry Steppe'",
        reliability_badge="KESIN",
    ),
    # ============================= BÖLÜM VII (38-41) =============================
    dict(
        n=38, title="İlk resmi kabul", scene_type="explanation", visual="reuse", reuse_ref=15,
        source_text=(
            "Sciences Po Mass Violence araştırma ağına göre Ryskulov'un mektubu, kıtlığın Sovyet "
            "yönetimi tarafından ilk kez resmi olarak kabul edilmesini sağladı; bu kabul, hem "
            "pratik önlemler alınmasına hem de Goloshchekin'in görevden alınmasına zemin "
            "hazırladı. Bu açıdan mektup, tarihin en etkili ihbar belgelerinden biridir."
        ),
        citation_ref="Sciences Po Mass Violence araştırma ağı",
        reliability_badge="KESIN",
    ),
    dict(
        n=39, title="Türk Konseyi'nin değerlendirmesi", scene_type="explanation", visual="reuse", reuse_ref=40,
        source_text=(
            "Türk Devletleri Teşkilatı, Aşarşılık'ı \"suç niteliğindeki Stalinist etnik "
            "politika\" olarak nitelendirmiştir. Bu tanımlama, mektubun belgelediği olayların "
            "Türk dünyasının ortak hafızasında nasıl konumlandırıldığını göstermektedir."
        ),
        citation_ref="Türk Devletleri Teşkilatı değerlendirmesi",
        reliability_badge="TARTISMALI",
    ),
    dict(
        n=40, title="Kazak ulusal hafızasındaki yeri", scene_type="explanation", visual="still",
        search_keywords="Turar Ryskulov monument",
        source_text=(
            "Ryskulov, bin dokuz yüz doksan bir sonrası Kazakistan'ında giderek artan bir ulusal "
            "kahraman figürüne dönüştürüldü. Ama başlangıçta kolektifleştirmeyi desteklemiş "
            "olması, bu sahiplenmenin sorgulanması gereken bir boyutunu oluşturuyor."
        ),
        pv=PV_WIDE,
        subject="a plain stone or bronze monument silhouette against an open sky, distant, no readable inscription, no human figures nearby",
        environment="a public square edge, open sky background",
        lighting="overcast_diffused",
        camera="static", lens="wide", motion="none - still frame",
        citation_ref=None, reliability_badge="GUCLU_CIKARIM",
    ),
    dict(
        n=41, title="Soykırım tartışmasındaki konumu", scene_type="conflict", visual="reuse", reuse_ref=25,
        source_text=(
            "Mektup, Aşarşılık'ın soykırım olup olmadığı tartışmasında iki açıdan kritiktir. "
            "Birincisi, Stalin'in bilgi sahibi olduğunu kanıtlaması — bu, kasıtsız bir "
            "felaketten çok bilinçli bir ihmal örüntüsüne işaret etmektedir. İkincisi, kıtlık "
            "ortamında bazı ilçelerin ticaretten men edilerek cezalandırıldığını belgelemesi — "
            "bu önlem, açlığın bir ceza aracı olarak kullanıldığının kanıtı olarak "
            "değerlendirilebilir."
        ),
        citation_ref="Sovyet arşiv belgeleri, akademik soykırım tartışması",
        reliability_badge="TARTISMALI",
    ),
    # ============================= BÖLÜM VIII (42-43) =============================
    dict(
        n=42, title="1937 Büyük Terörü ve idam", scene_type="ending", visual="still",
        search_keywords=None,
        source_text=(
            "Ryskulov, kıtlığı bildiren mektupları yazdıktan birkaç yıl sonra, bin dokuz yüz otuz "
            "yedide Stalin'in Büyük Terörü sırasında tutuklandı. Suçlama tanıdık bir kalıba "
            "uyuyordu: \"milliyetçi\", \"Pan-Türkist\", \"Sovyet karşıtı\". Bin dokuz yüz otuz "
            "sekizde kurşuna dizildi."
        ),
        pv=PV_CLOSEUP,
        # v5 fix: "blank label" phrasing was still ignored 2/3 times -
        # Flow printed "FILE NO." and, worse, "OFFICIAL FILE" + a fabricated
        # accession number "AF-8512-7" plus shelf location tags. Removed
        # the labelled-area concept entirely rather than asking for it to
        # stay blank.
        subject="a closed file folder with no label, tab, or printed marking anywhere on its cover, a single diagonal line drawn across the bare cardstock in dark ink, resting alone on an otherwise empty shelf",
        environment="archive shelf, dim even light",
        lighting="even_archive_lighting",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref="Ryskulov'un 1997 külliyatı",
        reliability_badge="KESIN",
    ),
    dict(
        n=43, title="Rehabilitasyon", scene_type="ending", visual="still",
        search_keywords=None,
        source_text=(
            "Ryskulov, Stalin'in ölümünün ardından bin dokuz yüz elli altıda Sovyet sistemi "
            "içinde rehabilite edildi. Tarihsel önemi, bin dokuz yüz doksan bir sonrasında "
            "Kazakistan'da daha kapsamlı biçimde tanındı."
        ),
        pv=PV_CLOSEUP,
        subject="the same style official file folder, now untied and open, its blank label with no diagonal line, papers visible resting inside, soft light falling across it",
        environment="archive shelf, warmer light than before",
        lighting="single_desk_lamp",
        camera="static", lens="macro", motion="none - still frame",
        citation_ref=None, reliability_badge="KESIN",
    ),
    # ============================= BÖLÜM IX (44-46) =============================
    dict(
        n=44, title="Özet zaman çizelgesi animasyonu", scene_type="montage", visual="still",
        search_keywords=None,
        source_text=(
            "Bin dokuz yüz otuz ile otuz iki arası artan felaket. Temmuz bin dokuz yüz otuz "
            "ikide Beşlerin Mektubu. Eylül bin dokuz yüz otuz ikide ilk not. Ocak bin dokuz yüz "
            "otuz üçte Goloshchekin'in azli. Dokuz Mart bin dokuz yüz otuz üçte asıl mektup. "
            "Bin dokuz yüz otuz üç ilkbaharında önlemler. Bin dokuz yüz otuz yedide tutuklama. "
            "Bin dokuz yüz otuz sekizde idam. Bin dokuz yüz elli altıda rehabilitasyon. Bin "
            "dokuz yüz doksan yedide külliyat. İki bin üçte Werth'in çalışması."
        ),
        pv=PV_WIDE,
        subject="an aged blank timeline strip texture on paper, faint unreadable horizontal line, no legible dates or labels",
        environment="a plain desk surface, single lamp overhead",
        lighting="single_desk_lamp",
        camera="pan.right", lens="wide", motion="slow horizontal drift only",
        citation_ref="Tüm bölümlerin kaynakları",
        reliability_badge="KESIN",
        stats_scene=True,
    ),
    dict(
        n=45, title="Kapanış alıntısı", scene_type="ending", visual="reuse", reuse_ref=17,
        source_text=(
            "\"Bu notu okumanızı ve bu meseleye müdahale etmenizi istiyorum; böylece açlığa "
            "mahkûm edilmiş pek çok insanın hayatını kurtarabilirsiniz.\" Stalin okudu. Bekledi. "
            "Milyonlar öldü. Ryskulov bin dokuz yüz otuz sekizde kurşuna dizildi. Mektup bin "
            "dokuz yüz doksan yediye kadar arşivde kaldı."
        ),
        citation_ref=None, reliability_badge=None,
    ),
    dict(
        n=46, title="Jenerik / kapanış", scene_type="credits", visual="video",
        search_keywords=None,
        min_duration_s=15.0,  # intentionally terse closing line ("Dünya hâlâ bilmiyor.") held on screen with music, like a title card - not under-written
        source_text="Dünya hâlâ bilmiyor.",
        pv=PV_WIDE,
        subject="an empty steppe horizon at dusk, wide open sky, no figures, quiet and still",
        environment="open Kazakh steppe at last light",
        lighting="low_winter_light",
        camera="pull_out.slow", lens="wide", motion="slow pull back, minimal cloud drift",
        citation_ref="Sciences Po, Wilson Center, e-history.kz, Nicolas Werth, Sarah Cameron",
        reliability_badge=None,
    ),
]


def scene_id(n: int) -> str:
    return f"SC-{n:03d}"


def shot_id(n: int, img_idx: int = 1) -> str:
    return f"SH-{n:03d}-{img_idx:02d}"


# Multi-image-per-scene expansion (2026-08-08, user feedback: 21 unique
# visuals for a 12.5min video is too static - avg 32.7s per visual vs. this
# template's own avg_shot_s=6.0 target). Each "still" scene now gets
# round(duration_s / TARGET_S_PER_IMAGE) images (min 1) that crossfade
# within the scene; "video" scenes keep exactly 1 fallback still (the video
# clip itself supplies the motion, kept minimal per the earlier
# AskUserQuestion decision to hold AI-video to just 2 of 46 scenes).
# Same subject/environment across a scene's images (single Flow generation
# request per scene, not re-researched per image) with a distinct
# angle/crop variant per image so the candidates aren't near-duplicates.
TARGET_S_PER_IMAGE = 6.0
VARIANT_MODIFIERS = [
    "",  # image 1: framing as specified in the scene dict
    ", tighter macro detail crop of the same subject",
    ", wider establishing angle of the same subject",
    ", alternate side angle of the same subject",
    ", closer detail on a different element within the same scene",
    ", slightly elevated angle of the same subject",
]


def image_count_for(s: dict) -> int:
    if s["visual"] == "video":
        return 1  # fallback still only - video clip supplies the scene's motion
    if s["visual"] != "still":
        return 0  # reuse scenes generate no images of their own
    return max(1, round(estimate_duration_s(s) / TARGET_S_PER_IMAGE))


def word_count(text: str) -> int:
    return len(text.split())


def estimate_duration_s(s: dict) -> float:
    text = s["source_text"]
    if not text:
        return s.get("min_duration_s", 8.0)  # silent title/logo card floor, matches Avrasya's zero-narration precedent
    return max(round(word_count(text) / WPM * 60, 1), s.get("min_duration_s", 0.0))


def build_flow_request(s: dict, kind: str, img_idx: int = 1) -> dict:
    """kind: 'image' or 'video'. img_idx: 1-based image index within the scene
    (video requests are always img_idx=1 - see image_count_for)."""
    pv = s["pv"]
    duration_s = 6.0 if kind == "video" else max(estimate_duration_s(s), 4.0)
    negative = NEGATIVE_BASE + (NEGATIVE_STATS_EXTRA if s.get("stats_scene") else "")
    variant = VARIANT_MODIFIERS[(img_idx - 1) % len(VARIANT_MODIFIERS)] if kind == "image" else ""
    slots = {
        "subject": s["subject"] + variant,
        "environment": s["environment"],
        "lighting": s["lighting"],
        "camera": s["camera"],
        "lens": {"wide": "28mm equivalent", "portrait": "85mm equivalent",
                  "normal": "50mm equivalent", "macro": "100mm macro"}.get(s.get("lens", "normal"), "50mm equivalent"),
        "motion": s["motion"] if kind == "video" else "none - still frame",
        "style": f"{STYLE_TAG}: {GRADE}, {GRAIN}, {PALETTE}",
        "technical": "16:9, deep focus, restrained framing" if pv == PV_WIDE
                     else "16:9, shallow depth of field, stable framing",
    }
    req = {
        "task_ref": _task_id(STATE_DIR),
        "shot_id": shot_id(s["n"], img_idx),
        "prompt_version": pv,
        "slots": slots,
        "negative": negative + ", " + REQUIRED_SUFFIX,
        "references": [],
        "seed": 20260807601 + s["n"] * 10 + img_idx + (1000 if kind == "video" else 0),
        "candidates": 2,
        "aspect_ratio": "16:9",
        "duration_s": duration_s,
        "model": "google_flow",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "role": "ai_required" if s.get("ai_required") else "fallback_if_no_real_source_found",
    }
    if s.get("notes"):
        req["notes"] = s["notes"]
    return req


def main() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    index = {
        "project_id": PROJECT_ID,
        "version": 1,
        "scenes": [
            {"scene_id": scene_id(s["n"]), "order": s["n"], "title": s["title"],
             "approved": False,
             "continuity_from": scene_id(s["n"] - 1) if s["n"] > 1 else None}
            for s in SCENES
        ],
    }
    (STATE_DIR / "scene_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    scenes_dir = PROJECT_DIR / "scenes"
    prompts_dir = PROJECT_DIR / "prompts_used"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    act_by_section = {}
    section_bounds = [(1, 4, 0), (5, 9, 1), (10, 14, 2), (15, 24, 3), (25, 29, 4),
                       (30, 33, 5), (34, 37, 6), (38, 41, 7), (42, 43, 8), (44, 46, 9)]
    for lo, hi, act in section_bounds:
        for n in range(lo, hi + 1):
            act_by_section[n] = act

    written_scenes = 0
    written_prompts = 0
    bare_digit_hits = []
    for s in SCENES:
        if re.search(r"\d", s["source_text"]):
            bare_digit_hits.append((scene_id(s["n"]), s["source_text"]))

        sid = scene_id(s["n"])
        visual_decision = "video" if s["visual"] == "video" else ("still" if s["visual"] == "still" else "reuse")
        reuse_ref = s.get("reuse_ref")
        reuse_scene_refs = [scene_id(reuse_ref)] if reuse_ref is not None else None
        n_images = image_count_for(s)
        shot_ids = [shot_id(s["n"], i) for i in range(1, n_images + 1)]

        first_sentence = s["source_text"].split(".")[0] + "." if s["source_text"] else s["title"]
        scene_record = {
            "scene_id": sid,
            "act": act_by_section[s["n"]],
            "title": s["title"],
            "summary": s["title"] + " — " + first_sentence,
            "source_text": s["source_text"],
            "duration_estimate_s": estimate_duration_s(s),
            "scene_type": s["scene_type"],
            "continuity_from": scene_id(s["n"] - 1) if s["n"] > 1 else None,
            "shots": shot_ids,
            "qa_status": "pending",
            "visual_decision": visual_decision,
            "visual_reuse_of": reuse_scene_refs,
            "search_keywords": s.get("search_keywords"),
            "ai_required": bool(s.get("ai_required", False)),
            "citation_ref": s.get("citation_ref"),
            "reliability_badge": s.get("reliability_badge"),
            "image_count_target": n_images,
        }
        (scenes_dir / f"{sid}.json").write_text(json.dumps(scene_record, indent=2, ensure_ascii=False) + "\n")
        written_scenes += 1

        if visual_decision == "reuse":
            continue

        for i in range(1, n_images + 1):
            shot_dir = prompts_dir / shot_id(s["n"], i)
            shot_dir.mkdir(parents=True, exist_ok=True)
            (shot_dir / "image.json").write_text(
                json.dumps(build_flow_request(s, "image", i), indent=2, ensure_ascii=False) + "\n"
            )
            written_prompts += 1
        if visual_decision == "video":
            video_shot_dir = prompts_dir / shot_id(s["n"], 1)
            (video_shot_dir / "video.json").write_text(
                json.dumps(build_flow_request(s, "video", 1), indent=2, ensure_ascii=False) + "\n"
            )
            written_prompts += 1

    total_words = sum(word_count(s["source_text"]) for s in SCENES)
    total_duration_s = sum(estimate_duration_s(s) for s in SCENES)
    total_images = sum(image_count_for(s) for s in SCENES)
    print(f"{PROJECT_ID}: {written_scenes} scenes, {written_prompts} flow_shot_request files written")
    print(f"total unique images across all scenes: {total_images}")
    print(f"total narration words: {total_words}, estimated narration: {total_words / WPM:.1f} min at {WPM} wpm")
    print(f"total estimated duration (incl. silent/title cards): {total_duration_s:.1f}s ({total_duration_s/60:.2f} min)")

    if bare_digit_hits:
        print(f"\nERROR: {len(bare_digit_hits)} scene(s) still contain bare digits (TTS-unsafe):")
        for sid, text in bare_digit_hits:
            print(f"  {sid}: {text}")
        sys.exit(1)
    print("\nConfirmed: zero bare digits in any scene's source_text.")


if __name__ == "__main__":
    main()
