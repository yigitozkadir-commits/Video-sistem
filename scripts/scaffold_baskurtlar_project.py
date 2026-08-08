#!/usr/bin/env python3
"""
Scaffold generator for PRJ-baskurtlar-arastirma (v2). Writes project.json's
production_plan mirror data into scene_index.json, scenes/SC-*.json, and
prompts_used/<shot_id>/image.json (+ video.json for AI-hero scenes) - all
against schemas this repo already defines but that were unpopulated before
this project (scene.schema.json, scene_index.schema.json,
flow_shot_request.schema.json).

v2 change from v1: narration is no longer a heavily-condensed summary -
it uses the source report's own sentences closer to their full form, plus
verified additions from further research (see the "Başkurtlar Video Planı
v2" plan section for each finding's source). One correction is included:
the report's claim that Kuray/Ural Batır/Sabantuy/forest beekeeping are on
UNESCO's Intangible Cultural Heritage list could not be verified against
UNESCO's own ICH database (Russia is not even a state party to that
convention) - SC-015 replaces that claim with what IS verifiable (TURKSOY's
inventory, a UNESCO Biosphere Reserve, a Russian federal trademark).

Each non-reuse scene also carries `search_keywords` (English) for
scripts/find_reference_images.py to try against Wikimedia Commons before
falling back to the Flow prompt this script still generates for every
scene - "search the real world first, generate only what can't be
photographed" (Ural Batır, being mythological, is the one scene marked
ai_required=True).

Re-running this script overwrites scenes/*.json and prompts_used/*/*.json
with the same content - it's a generator, not a mutation log. It does NOT
overwrite state/reference_image_sources.jsonl (find_reference_images.py's
output) - that's a separate, additive step run afterward.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
from production_ledger import _task_id  # noqa: E402

PROJECT_ID = "PRJ-baskurtlar-arastirma"
PROJECT_DIR = REPO_ROOT / "projects" / PROJECT_ID
STATE_DIR = PROJECT_DIR / "state"
FPS = 30
WPM = 145  # TPL-baskurtlar-hybrid narrator pace

PV_WIDE = "PV-0044"       # flow.shot.wide.establishing
PV_CLOSEUP = "PV-0031"    # flow.shot.closeup.realisation

NEGATIVE_STILL = ("text, watermark, extra fingers, warped face, plastic skin, "
                   "modern objects, camera shake, oversaturation, distorted horizon, "
                   "duplicated architecture, tilted frame, anime stylisation, lens flare")
NEGATIVE_VIDEO = ("text, watermark, extra fingers, warped face, plastic skin, "
                   "modern objects, camera shake, oversaturation, fast motion, "
                   "anime stylisation, lens flare")

GRADE = "desaturated warm shadows, cool highlights, film curve"
GRAIN = "fine 35mm"
PALETTE = "earth tones, ochre, deep red, cold grey"

SCENES = [
    dict(
        n=1, title="Giriş ve Nüfus", scene_type="opening", visual="video",
        search_keywords=None,  # tried "Bashkortostan steppe" - best hit was an unrelated cell tower, rejected on visual review; hero scene needs AI video anyway
        source_text=(
            "Başkurtlar, Türk dünyasının ayırıcı ve önemli bir parçasıdır. Ural Dağları'nın "
            "eteğinde Başkurdistan Cumhuriyeti'nde yaşayan bu halk, Rusya'nın en büyük Türk "
            "azınlığını oluşturur. Başkurtlar, İslamiyet öncesi Türk inançlarından kalma "
            "izlerle Hanefî İslam'ın derinliklerinde sentez yaşayan, 10. yüzyıldan itibaren "
            "tarihî kaynaklarda yer alan, Ural Batır destanında anlatılan kültürel değerlere "
            "sahip bir toplum olarak tanınmaktadır. Başkurdistan Cumhuriyeti, Volga "
            "Bölgesi'nin batısında ve Ural Dağları'nın eteğinde konumlanmış, Başkurt "
            "nüfusunun yoğun olarak yaşadığı ana bölgedir; başkenti Ufa şehridir. Rusya'nın "
            "2010 nüfus sayımına göre Başkurt nüfusu 1.584.554'tü; 2021 sayımına göre bu "
            "rakam 1.570.000'e, anadili Başkurtça konuşanların sayısı ise 1.080.000'e "
            "güncellenmiştir. Nüfusun büyük bölümü hâlâ Başkurdistan Cumhuriyeti'nde "
            "yaşamakta, geri kalan Başkurt diasporası ise Tataristan, Perm Diyarı, Samara, "
            "Orenburg ve Sibirya bölgelerinde dağınık olarak yerleşmiş durumdadır. 20. "
            "yüzyıl boyunca Başkurt nüfusunun nisbi oranında bir azalış gözlenmiştir; bu, "
            "Sovyet dönemi göçleri, kentleşme hareketleri ve asimilasyon baskılarının "
            "sonucudur."
        ),
        pv=PV_WIDE,
        subject="Ural Mountains foothills at dawn, vast Bashkir steppe stretching to the horizon",
        environment="rolling steppe grassland meeting forested foothills, a distant yurt encampment for scale",
        lighting="golden_hour",
        camera="drone", lens="wide", motion="slow forward drift, grass moving in wind",
    ),
    dict(
        n=2, title="Etnogenez ve Köken", scene_type="explanation", visual="still",
        search_keywords=None,  # tried "Ural archaeology" - best hit was a regional museum's entrance, not archaeological content, rejected on visual review
        source_text=(
            "Başkurt etnoniminin kökeni hakkında farklı akademik görüşler bulunmaktadır. En "
            "yaygın teori 'baş' (lider) ve 'kurt' (kuvvet) kelimelerinin birleşmesinden "
            "türediğini ileri sürer. Çin kaynakları 'Pa-ssŭ-kŭn' olarak kaydedilmiş olan bu "
            "halka işaret etmektedir. Başkurtlar, Altın Orda dönemi boyunca bağımsız bir "
            "kabile yapısını korumuş, ancak siyasi anlamda Moğol hâkimiyeti altında "
            "yaşamıştır; 16. yüzyıldan itibaren Rusya Çarlığı'nın genişlemesiyle Rus "
            "hâkimiyeti altına girmişlerdir. Ural bölgesindeki arkeolojik buluntular, 9-10. "
            "yüzyıllardan itibaren burada yerleşik bir Türk nüfusun varlığını göstermektedir; "
            "Kazakov'un arkeolojik çalışmaları Bulgar ve Türk medeniyetinin izlerini ortaya "
            "koymaktadır. İbn Fadlan'ın 10. yüzyıl seyahatnâmesi, Başkurtların müslüman fakat "
            "animistik uygulamaları sürdüren bir toplum olduğunu kaydeder."
        ),
        pv=PV_WIDE,
        subject="early medieval Turkic encampment on the Ural steppe, weathered archaeological grave markers in foreground",
        environment="open steppe at the edge of a river, scattered ancient burial mounds",
        lighting="overcast_soft",
        camera="static", lens="wide", motion="environmental only, distant smoke drifting",
    ),
    dict(
        n=3, title="Wilhelm Radloff ve Bilimsel Keşif", scene_type="discovery", visual="still",
        search_keywords="Wilhelm Radloff",
        source_text=(
            "19. yüzyılda Başkurtlar ve diğer Türk halkları üzerine yapılan en kapsamlı "
            "bilimsel çalışmalardan biri, Alman doğumlu Türkolog Wilhelm Radloff'a — Rusça "
            "adıyla Vasili Radlov'a — aittir. Rusya İmparatorluk Bilimler Akademisi bünyesinde "
            "çalışan Radloff, 1866 ile 1907 yılları arasında on ciltlik 'Proben der "
            "Volkslitteratur der türkischen Stämme' — Türk Boylarının Halk Edebiyatından "
            "Örnekler — adlı eserini yayımladı. Bu eser, Orta Asya ve Ural bölgesi Türk "
            "halklarının dil ve sözlü kültürünü sistematik olarak belgeleyen ilk bilimsel "
            "çalışma kabul edilir ve bugün dijitalleştirilerek herkesin erişimine açılmıştır."
        ),
        pv=PV_CLOSEUP,
        subject="an elderly 19th-century European scholar in period dress, seated at a wooden desk with open field notebooks",
        environment="a modest academy study lined with books and ethnographic sketches",
        lighting="single_window_soft",
        camera="static", lens="portrait", motion="minimal, page turning",
    ),
    dict(
        n=4, title="Dil", scene_type="explanation", visual="still",
        search_keywords="Kashgari Diwan",
        source_text=(
            "Başkurt Türkçesi, Kıpçak dilinin doğu kolunda yer almaktadır. Tatar Türkçesine "
            "yakın olmakla birlikte, ayrı bir dil olarak kabul edilir; Başkurt dilinde Bulgar "
            "ve Kıpçak unsurlarının sentezi görülmektedir. Kaşgarlı Mahmud, 11. yüzyılda "
            "Başkurt dilini ayrı bir Türk dili olarak tanımlamıştır. Günümüzde Başkurt dili, "
            "Başkurdistan Cumhuriyeti'nin resmi dillerinden biridir. Ancak genç kuşaklarda "
            "Rusça eğitimin dominantlığı, Başkurt dilinin öğrenilme oranını azaltmıştır. "
            "UNESCO'nun Tehlike Altındaki Diller Atlası, Başkurt dilini 'Kırılgan' — "
            "Vulnerable — kategorisinde sınıflandırmaktadır: bu, dilin çoğu çocuk tarafından "
            "hâlâ kullanıldığı ama bazı kısıtlamalarla karşılaştığı anlamına gelir."
        ),
        pv=PV_CLOSEUP,
        subject="an aged hand-bound manuscript page, Turkic script visible, resting on worn wood",
        environment="a scholar's table lit by a single window, dust motes in the light",
        lighting="single_window_soft",
        camera="static", lens="portrait", motion="minimal, page edge trembling slightly",
    ),
    dict(
        n=5, title="Ural Batır Destanı", scene_type="montage", visual="video",
        search_keywords=None,  # mythological - no real photograph can exist
        ai_required=True,
        source_text=(
            "Ural Batır, Başkurt halkının en önemli destan geleneğidir. Bu destan, Başkurt "
            "toplumunun değerleri, dünya görüşü, kahramanlık anlayışı ve sosyal yapısını "
            "çeşitli katmanlarında yansıtmaktadır. Destanda, Ural isminde bir kahraman, "
            "düşman kabilelere karşı mücadele ederek Başkurt halkını birleştirir. Destan, "
            "göçebe yaşamın zorlukları, at yetiştiriciliğinin önemliliği ve Tengrici "
            "kozmolojinin izlerini taşımaktadır. Destan, 1910 yılında Başkurt folklorcu "
            "Muhammetşa Burangulov tarafından, konuya hâkim iki yaşlı Başkurt bilgesinden "
            "derlenerek ilk kez yazıya geçirilmiştir. Modern akademik araştırmalara göre, "
            "Ural Batır destanı, Oğuz destanları geleneği ve İran epik geleneğinin etkisini "
            "taşırken, özgün Başkurt değerleri ile harmoni içindedir."
        ),
        pv=PV_CLOSEUP,
        subject="a lone epic warrior on horseback silhouetted against a stormy steppe sky, spear raised",
        environment="open battlefield steppe, distant rival riders",
        lighting="overcast_soft",
        camera="static", lens="normal", motion="horse mane and cloak moving in wind, minimal",
    ),
    dict(
        n=6, title="İnanç Sistemi", scene_type="explanation", visual="still",
        search_keywords="Bashkortostan mosque",
        source_text=(
            "Başkurtlar, İslamiyet öncesi Türk inanç sistemini — Tengricilik, Yer-Su "
            "inançları, şamanizm — ve Hanefî İslamını sentezlemişlerdir. 10. yüzyıldan "
            "itibaren kademeli olarak İslamı benimseyen Başkurtlar, kendi kültürel kalıpları "
            "içinde dini yaşamıştır. Günümüzde Başkurtlar ağırlıklı olarak Müslümandır, ancak "
            "eski Türk inanç kalıntıları — Sabantuy bayramı, yer-su inançları — halen "
            "canlıdır. Sovyet dönemi ateizmi sonrası, 1990'lardan itibaren dini canlanma "
            "hareketleri başlamıştır."
        ),
        pv=PV_WIDE,
        subject="a small wooden mosque at the edge of the steppe beneath an open sky, an ancient stone waymarker nearby",
        environment="steppe grassland at dusk, sky transitioning from gold to deep blue",
        lighting="golden_hour",
        camera="static", lens="wide", motion="environmental only, clouds drifting",
    ),
    dict(
        n=7, title="Müzik ve Sanat Gelenekleri", scene_type="montage", visual="video",
        search_keywords="Bashkir kuray",
        source_text=(
            "Başkurt müzik geleneği, Kuray adı verilen enstrümanı merkez alır. Kuray, "
            "ağaçtan yapılan, düdük benzeri bir enstrümandır ve Başkurt halk müziğinde temel "
            "rol oynar. Destan anlatıcılığı — baytçılık — Başkurt sözlü kültürünün önemli bir "
            "yönüdür; baytçılar destanları müzik eşliğinde uzun saat anlatırlar. Kuray, 2018 "
            "yılında Rusya Federal Fikri Mülkiyet Servisi tarafından Başkurdistan'ın bölgesel "
            "markası olarak tescillenmiştir. Modern Başkurt müzik sahnesi, geleneksel "
            "unsurları çağdaş müzik biçimleriyle harmanlamaya çalışmaktadır."
        ),
        pv=PV_CLOSEUP,
        subject="weathered hands playing a kuray reed flute, close on the instrument and fingers",
        environment="seated by a felt tent opening, soft interior firelight behind",
        lighting="firelight_warm",
        camera="static", lens="macro", motion="fingers moving over the instrument, breath visible in cold air",
    ),
    dict(
        n=8, title="Maddi Kültür ve Giyim", scene_type="explanation", visual="still",
        search_keywords="Bashkir traditional costume",
        source_text=(
            "Başkurt geleneksel giyimi, göçebe yaşamın ihtiyaçlarına uygun tasarlanmıştır. "
            "Erkekler için kaftan benzeri giyimler, kadınlar için pullu elbiseler ve "
            "başlıklar karakteristiktir. Keçe ve deri işçiliği, Başkurt el sanatlarının "
            "önemli parçasıdır. Ev eşyaları, ahşap oymacılığı ve dokumacılık, Başkurt maddi "
            "kültürünün belli başlı öğeleridir. Orta Asya el sanatlarının tarzını taşıyan bu "
            "ürünler, Başkurt kimliğinin taşıyıcılarıdır."
        ),
        pv=PV_CLOSEUP,
        subject="a Bashkir woman in traditional coin-embroidered dress and headdress, standing portrait",
        environment="felt tent interior, woven textiles visible in soft background",
        lighting="single_window_soft",
        camera="static", lens="portrait", motion="fabric and coin ornaments moving slightly",
    ),
    dict(
        n=9, title="Mutfak Kültürü", scene_type="explanation", visual="still",
        search_keywords=None,  # tried "kumis Bashkir" - real, correctly-licensed, but a run-down roadside kiosk photo, rejected on visual production-quality grounds
        source_text=(
            "Başkurt mutfağı, göçebe ekonomisinden beslenmiştir. At eti, koyun eti, süt "
            "ürünleri — ayran, peynir, yoğurt — temel yemekleri oluştururken, artan tarım "
            "ekonomisiyle ekmek ve tahıl ürünleri de müdahil olmuştur. Başkurt balı, Ural "
            "ormanlarında arıcılık yapılmasından dolayı önemli bir yemek maddesidir; bal "
            "sadece gıda değil, tıbbi bir ürün olarak da kullanılmış ve Başkurt ekonomisinin "
            "önemli bir parçası olmuştur."
        ),
        pv=PV_CLOSEUP,
        subject="a low wooden table set with kumis in a bowl, dark bread, and a comb of forest honey",
        environment="felt tent interior floor setting, woven rug beneath",
        lighting="firelight_warm",
        camera="static", lens="normal", motion="steam rising gently, minimal",
    ),
    dict(
        n=10, title="Arıcılık ve Orman Kültürü", scene_type="explanation", visual="still",
        search_keywords="Bashkir honey",
        source_text=(
            "Ural ormanlarında orman arıcılığı, asırlarca Başkurt ekonomisinin ana kaynağı "
            "olmuştur. Barkuri adı verilen orman arıcılığında, arılar doğal ağaçlarda "
            "yaşamakta ve Başkurtlar bu arılardan medeni biçimde faydalanmaktadır. Bu "
            "geleneğin merkezinde, sadece Başkurdistan'ın Burzyan bölgesinde bulunan yaban "
            "bal arısı vardır. Başkurt balının Rusya ve dünya pazarlarında ün yapması, bu "
            "ürünün kalitesi ve geleneksel üretim yöntemleri nedeniyledir. Günümüzde orman "
            "arıcılığı, çevre sorunları ve modernleşme nedeniyle tehlike altındadır; 2012 "
            "yılında Başkurt Ural Doğa Rezervi, tam olarak bu yaban arısı popülasyonunu ve "
            "ona bağlı bal avcılığı geleneğini korumak amacıyla UNESCO'nun Dünya Biyosfer "
            "Rezervleri Ağı'na dahil edilmiştir."
        ),
        pv=PV_WIDE,
        subject="a centuries-old pine forest with a traditional bashkort hollowed hive marked high on a trunk",
        environment="dense Ural forest, dappled light through canopy",
        lighting="overcast_soft",
        camera="tilt.up", lens="wide", motion="leaves and light shifting, minimal",
    ),
    dict(
        n=11, title="Bayramlar ve Ritüeller", scene_type="montage", visual="video",
        search_keywords="Sabantuy wrestling",
        source_text=(
            "Sabantuy — Sabanay, Sabantus — Başkurtların en önemli bahar festivalidir. Tarım "
            "sezonunun başlangıcında kutlanan bu festival, eski Türk medeniyetinin izlerini "
            "taşır. Sabantuy'da atış yarışları, güreş müsabakaları, şarkı söylemeler yapılır. "
            "Düğün gelenekleri, derse (sözleşme) aşamasından nikâha kadar uzanan ritüellerle "
            "zengindir. Doğum ritüelleri, bebeğin adlandırılması, sünnet kutlamaları; cenaze "
            "gelenekleri, gömülme şekli ve helallaşma ritüelleri, Başkurt toplumunun din ve "
            "kültür sentezini gösterir."
        ),
        pv=PV_WIDE,
        subject="a spring festival gathering on open grassland, wrestlers competing, a crowd watching",
        environment="open field festival ground, felt tents and banners at the edges",
        lighting="golden_hour",
        camera="pan.right", lens="wide", motion="crowd and wrestlers in motion, banners moving in wind",
    ),
    dict(
        n=12, title="Sovyet Dönemi", scene_type="flashback", visual="still",
        search_keywords=None,  # tried "Bashkortostan Soviet" - best hit was an unrelated WWII machine gun museum display, rejected on visual review
        source_text=(
            "Bolşevik İhtilali sonrası Başkurdistan bağımsız bir cumhuriyet olarak ilan "
            "edilmiş (1919), ancak kısa süre sonra SSCB bünyesine dâhil edilmiştir (1920). "
            "Kolektivizasyon politikaları Başkurt halkını şiddetli şekilde etkilemiştir. "
            "Sovyet dönemi, Başkurt dilinin Kiril alfabesine çevirilmesi, eğitim sisteminin "
            "Rusçalaştırılması, dini yaşamın baskılanması, kültürel kurumların "
            "devletleştirilmesi şeklinde gerçekleşmiştir. Tarihçi Andreas Kappeler'in "
            "çok-uluslu Rusya İmparatorluğu üzerine yaptığı çalışmalar, Başkurtların bu "
            "süreçte bozkıra kademeli olarak nasıl entegre edildiğini ve bu entegrasyonun "
            "bedelini ayrıntılı biçimde ortaya koymaktadır. Ancak bu dönemde, Başkurt sanat "
            "ve edebiyat kurumları da kuruluş bulmuştur."
        ),
        pv=PV_WIDE,
        subject="a row of collective farm buildings on the steppe under a grey overcast sky, a red flag visible",
        environment="early Soviet-era rural settlement, muted cold-grey palette",
        lighting="overcast_soft",
        camera="static", lens="wide", motion="minimal, flag moving in wind",
    ),
    dict(
        n=13, title="Modern Başkurdistan", scene_type="explanation", visual="still",
        search_keywords="Ufa Bashkortostan",
        source_text=(
            "Sovyet Birliği'nin çöküşü (1991) sonrası, Başkurdistan Cumhuriyeti, Rusya "
            "Federasyonu'nda bir özerk cumhuriyet olarak konumlanmıştır. Başkurt Cumhuriyeti, "
            "Başkurt dilinin korunması, eğitimin geliştirilmesi, kültürel kurumların "
            "düzeltilmesi alanında çeşitli inisiyatif almıştır. Günümüzde Başkurdistan "
            "Cumhuriyeti, Ufa başkent olmak üzere, iktisadî açıdan gelişmiş bir bölgedir. Ufa "
            "Devlet Üniversitesi, Başkurt Bilimler Akademisi, Ufa Opera Balesi Tiyatrosu gibi "
            "kültürel kurumlar, Başkurt kültürünün yaşatılmasında rol oynamaktadır."
        ),
        pv=PV_WIDE,
        subject="the modern skyline of Ufa at dusk, river in foreground, historic and contemporary buildings mixed",
        environment="city skyline along a wide river, warm evening light on buildings",
        lighting="golden_hour",
        camera="pull_out.slow", lens="wide", motion="water moving, minimal",
    ),
    dict(
        n=14, title="Türk Dünyasındaki Yeri", scene_type="explanation", visual="reuse",
        reuse_ref=1,
        source_text=(
            "Başkurtlar, Tatarlar, Kazaklar, Nogaylar, Başkıpçaklar gibi diğer Türk "
            "halklarıyla tarihî ve kültürel bağlara sahiptir. Başkurt dili, Kıpçak dillerinin "
            "doğu kolunda Tatar ve Kazak dilleriyle ortaklık göstermektedir. Türkiye "
            "Cumhuriyeti ve Türk Dünyası örgütleri ile Başkurtlar arasında kültürel değişim "
            "ve işbirliği hareketleri bulunmaktadır. Türk Konseyi'nde Başkurdistan "
            "Cumhuriyeti temsil edilmektedir."
        ),
    ),
    dict(
        n=15, title="Miras ve Koruma", scene_type="montage", visual="reuse",
        reuse_ref=[5, 7, 10, 11],
        source_text=(
            "Başkurt kültürünün korunması için farklı uluslararası kurumlar farklı roller "
            "üstlenmiştir — ama burada dikkatli olmak gerekir. Ural Batır destanı, "
            "UNESCO'nun değil, Türk Kültür ve Miras Vakfı TURKSOY'un 2015'te yayımladığı "
            "Türk Dünyası Somut Olmayan Kültürel Miras Envanteri'nde yer almaktadır. Orman "
            "arıcılığı geleneği, UNESCO'nun kültürel miras listesinde değil, ama 2012'de "
            "Başkurt Ural Doğa Rezervi'nin UNESCO Dünya Biyosfer Rezervleri Ağı'na "
            "katılmasıyla dolaylı olarak koruma altına alınmıştır. Kuray ise 2018'de "
            "Başkurdistan'ın resmî bölgesel markası olarak tescillenmiştir. Bu üçü de gerçek "
            "ve doğrulanabilir koruma biçimleridir — sadece hepsinin UNESCO'nun Somut "
            "Olmayan Kültürel Miras listesinden geldiği iddiası doğrulanamamaktadır; Rusya "
            "Federasyonu bu sözleşmeye zaten taraf değildir."
        ),
    ),
    dict(
        n=16, title="Günümüzde Karşılaşılan Sorunlar", scene_type="emotional_pause", visual="still",
        search_keywords=None,  # staged/conceptual composition, not a real documentable subject
        ai_required=True,
        source_text=(
            "Başkurt dili, genç kuşaklarda öğrenilme oranının düşmesi nedeniyle tehlike "
            "altındadır. UNESCO'nun sınıflandırmasıyla 'Kırılgan' durumda olan dil, eğitim "
            "sisteminde Rusçanın dominantlığı nedeniyle güç kaybetmektedir. Kentleşme, "
            "asimilasyon, kültürel kurumların yetersizliği, geleneksel sanatların kaybı, "
            "genç kuşakların kültürel bağlarında zayıflama, Başkurtların karşılaştıkları "
            "temel sorunlardır. İş göçü, özellikle Sibirya ve Uzak Doğu bölgelerine göç, "
            "Başkurt nüfusunun dağılmasına yol açmıştır."
        ),
        pv=PV_WIDE,
        subject="a young Bashkir person in modern dress looking out over the city from the steppe's edge, traditional felt tent barely visible in the far distance",
        environment="transition point between open steppe and the edge of a modern city",
        lighting="overcast_soft",
        camera="static", lens="normal", motion="minimal, wind in grass",
    ),
    dict(
        n=17, title="Türk Dünyasına Katkılar", scene_type="montage", visual="reuse",
        reuse_ref=[7, 10],
        source_text=(
            "Rapor, Başkurtların Türk dünyasına yirmi başlıca katkısını sıralıyor. Dil "
            "biliminde, Kıpçak dilinin doğu kolunun incelenmesine kaynaklık ettiler. Ural "
            "Batır destanıyla Türk destan geleneğine önemli bir örnek kazandırdılar. Kuray "
            "müziğiyle Türk müzik geleneğini, orman arıcılığıyla Türk ekonomik geleneğini "
            "zenginleştirdiler. Sabantuy festivaliyle Türk medeniyetinin bahar şenlikleri "
            "geleneğini temsil ettiler; Başkurt balıyla Orta Asya ve Türk pazarında ün "
            "kazandılar. Göçebe yaşam mirasını belgelediler, şamanistik ve Tengrici "
            "inançların yaşayan örneklerini korudular. Keçe, dokuma ve ahşap oymacılığı gibi "
            "el sanatlarını, bal ve bitki tedavisine dayanan geleneksel tıp bilgisini "
            "geliştirdiler. Kabile sisteminin modernleşmesi üzerine sosyal yapı "
            "incelemelerine, Türk mitolojisi araştırmalarına folklor ve masallarla kaynaklık "
            "ettiler. Kendine özgü Başkurt at cinsini ve yetiştirme yöntemlerini "
            "geliştirdiler; Başkurdistan Bilimler Akademisi'yle akademik araştırmaların "
            "merkezi oldular. Modern Türk edebiyatına şiir ve edebiyatla katkıda bulundular; "
            "bölgede Türk medeniyeti merkezleri niteliğinde eğitim kurumları kurdular. "
            "Tatar-Başkurt sentezi, Kıpçak Türklerinin göçebe-yerleşik geçişine örnek oldu; "
            "bal ve doğal ürünler tıbbı kalp hastalığı araştırmalarına katkı sağladı. "
            "Demografik çalışmalarla Türk azınlık desteklerine model oldular ve Rusya "
            "Federasyonu içinde Türk kimliğinin korunmasında bir kültürel direniş örneği "
            "sundular. Tam liste ekranda."
        ),
    ),
    dict(
        n=18, title="Önemli Başkurt Şahsiyetleri", scene_type="discovery", visual="still",
        search_keywords="Salavat Yulayev monument",
        source_text=(
            "Salavat Yulayev, Başkurt tarihinin en bilinen isimlerinden biridir. 1774'te, "
            "henüz on dokuz yaşındayken, babası Yulay Aznalin ile birlikte Yemelyan "
            "Pugaçev'in Rus İmparatorluğu'na karşı büyük köylü isyanına katıldı; ailesinin "
            "çara hizmeti karşılığında aldığı toprakların mahkeme kararıyla fabrikatörlere "
            "devredilmesi, isyana katılım nedenlerinden biriydi. Üç bin kişilik bir "
            "müfrezeyle harekete geçen Yulayev, kısa sürede yetenekli bir askerî lider "
            "olarak öne çıktı; Pugaçev'in manifestolarını halka dağıttı, orduyu erzak ve "
            "askerle destekledi. 24 Kasım 1774'te yakalanan Yulayev, Baltık kıyısındaki "
            "Rogervik kalesine ömür boyu kürek cezasına gönderildi ve bugün Başkurdistan'ın "
            "millî kahramanı olarak anılmaktadır — heykeli Ufa'nın simgelerinden biridir. "
            "Rapor, Başkurt bilim ve kültür hayatından başka isimler de kaydeder: Gafur "
            "İlyasov, Başkurt dili ve edebiyatı araştırmacısı; Mustay Karim (1919-2005), "
            "Başkurt şair ve yazarı; Saliha Gimadeeva, Başkurt müzisyeni ve kuray sanatçısı; "
            "Bashir Niyasov, Başkurt halk müziği derlemecisi. Modern dönemden Murtaza "
            "Rahimov (1930-), Başkurdistan'ın 1990-2010 yılları arasındaki başkanı; Boris "
            "Hamidullin ise Başkurt tarihi araştırmacısı olarak anılır."
        ),
        pv=PV_CLOSEUP,
        subject="Salavat Yulayev, an 18th-century Bashkir rebel leader on horseback, determined expression, period dress and weapon",
        environment="open steppe at the edge of a river crossing, rebel encampment smoke in distance",
        lighting="overcast_soft",
        camera="static", lens="portrait", motion="horse and cloak moving in wind, minimal",
        notes=("Prefer the real equestrian monument to Salavat Yulayev in Ufa (search_keywords "
               "above) over an AI recreation - more accurate and copyright-safe. AI prompt kept "
               "as fallback only. No REF-CHR sheet created - single appearance in this documentary."),
    ),
    dict(
        n=19, title="Genç Kuşaklara Aktarılması Gereken Değerler", scene_type="montage", visual="reuse",
        reuse_ref=8,
        source_text=(
            "Rapor, genç kuşaklara aktarılması gereken yirmi beş kültürel değer sıralıyor: "
            "kuray sanatı ve müziği, Ural Batır destanı, Başkurt dilinin doğru kullanımı, "
            "Sabantuy geleneği, at yetiştiriciliği, orman arıcılığı. Düğün ritüelleri, "
            "destan anlatıcılığı — baytçılık —, geleneksel keçe yapımı, ahşap oymacılığı ve "
            "dokumacılık el sanatları zincirini tamamlıyor. Başkurt balı ve arı ürünleri, "
            "geleneksel giyim, ev mimarisinin tasarımı, pişirme teknikleri maddi kültürün "
            "taşıyıcıları. Yer-Su inançları ve Tengrici kozmoloji, sosyal davranış kuralları, "
            "koruma büyüleri ve semboller, atasözleri ve deyimler, şarkı ve marşlar manevi "
            "mirası oluşturuyor. Oyunlar ve sporlar, içki ve yemek sunumunun âdâbı, "
            "misafirperverlik değerleri ve doğa ile kurulan ilişki, çevre bilinci listeyi "
            "tamamlıyor. Tam liste ekranda."
        ),
    ),
    dict(
        n=20, title="Sonuç", scene_type="ending", visual="reuse",
        reuse_ref=1,
        source_text=(
            "Başkurtlar, Türk tarihinin ve kültüründe önemli bir yeri temsil ederler. Ural "
            "bölgesinin coğrafî konumu, Kıpçak dilinin doğu kolundaki yerleşimi, Tengricilik "
            "ile Hanefî İslam'ın sentezini yaşayan inanç sistemi, Ural Batır destanı, Kuray "
            "müziği, orman arıcılığı, geleneksel sanat ve zanaat, Başkurtları Türk dünyasında "
            "özgün ve değerli kılar. Günümüzde Başkurtlar, küreselleşme, Rusçalaşma ve "
            "asimilasyon baskıları altında kültürel miraslarını koruma çabasındadırlar. 'Kök "
            "bir. Sesler farklı.' ilkesiyle, Başkurt kültürü, Türk dünyasının geniş sesiyle "
            "bir parça olmaya devam edecektir."
        ),
    ),
]


def scene_id(n: int) -> str:
    return f"SC-{n:03d}"


def shot_id(n: int) -> str:
    return f"SH-{n:03d}-01"


# ElevenLabs (eleven_multilingual_v2) misreads bare digit dates/years and
# Turkish thousands-dot-grouped numbers in Turkish text (century ordinals
# like "10." read as "on nokta" instead of "onuncu", big numbers like
# "1.584.554" read digit-by-digit). Spelling every date/number out as
# Turkish words at generation time (not by hand-patching audio after the
# fact) keeps this deterministic and makes it survive script re-runs.
# Ordered longest-context-first so replacements can't partially clash.
NUMBER_FIXES: list[tuple[str, str]] = [
    ("10. yüzyıldan itibaren tarihî", "onuncu yüzyıldan itibaren tarihî"),
    (
        "2010 nüfus sayımına göre Başkurt nüfusu 1.584.554'tü; 2021 sayımına göre bu",
        "iki bin on nüfus sayımına göre Başkurt nüfusu bir milyon beş yüz seksen dört "
        "bin beş yüz elli dörttü; iki bin yirmi bir sayımına göre bu",
    ),
    ("1.570.000'e", "bir milyon beş yüz yetmiş bine"),
    ("1.080.000'e", "bir milyon seksen bine"),
    ("20. yüzyıl boyunca", "yirminci yüzyıl boyunca"),
    ("16. yüzyıldan itibaren Rusya Çarlığı'nın", "on altıncı yüzyıldan itibaren Rusya Çarlığı'nın"),
    ("9-10. yüzyıllardan itibaren burada", "dokuzuncu ve onuncu yüzyıllardan itibaren burada"),
    ("İbn Fadlan'ın 10. yüzyıl seyahatnâmesi", "İbn Fadlan'ın onuncu yüzyıl seyahatnâmesi"),
    ("19. yüzyılda Başkurtlar", "on dokuzuncu yüzyılda Başkurtlar"),
    ("1866 ile 1907 yılları arasında", "bin sekiz yüz altmış altı ile bin dokuz yüz yedi yılları arasında"),
    ("11. yüzyılda Başkurt dilini", "on birinci yüzyılda Başkurt dilini"),
    ("1910 yılında Başkurt folklorcu", "bin dokuz yüz on yılında Başkurt folklorcu"),
    ("10. yüzyıldan itibaren kademeli", "onuncu yüzyıldan itibaren kademeli"),
    ("1990'lardan itibaren dini canlanma", "bin dokuz yüz doksanlı yıllardan itibaren dini canlanma"),
    ("2018 yılında Rusya Federal", "iki bin on sekiz yılında Rusya Federal"),
    ("2012 yılında Başkurt Ural Doğa Rezervi", "iki bin on iki yılında Başkurt Ural Doğa Rezervi"),
    ("ilan edilmiş (1919), ancak", "ilan edilmiş (bin dokuz yüz on dokuz), ancak"),
    ("dâhil edilmiştir (1920).", "dâhil edilmiştir (bin dokuz yüz yirmi)."),
    ("çöküşü (1991) sonrası", "çöküşü (bin dokuz yüz doksan bir) sonrası"),
    ("TURKSOY'un 2015'te yayımladığı", "TURKSOY'un iki bin on beşte yayımladığı"),
    ("ama 2012'de Başkurt Ural Doğa Rezervi'nin", "ama iki bin on ikide Başkurt Ural Doğa Rezervi'nin"),
    ("Kuray ise 2018'de Başkurdistan'ın", "Kuray ise iki bin on sekizde Başkurdistan'ın"),
    ("biridir. 1774'te, henüz on dokuz yaşındayken", "biridir. Bin yedi yüz yetmiş dörtte, henüz on dokuz yaşındayken"),
    (
        "askerle destekledi. 24 Kasım 1774'te yakalanan Yulayev",
        "askerle destekledi. Yirmi dört Kasım bin yedi yüz yetmiş dörtte yakalanan Yulayev",
    ),
    (
        "Mustay Karim (1919-2005), Başkurt şair ve yazarı;",
        "Mustay Karim, bin dokuz yüz on dokuz ile iki bin beş yılları arasında yaşamış Başkurt şair ve yazarı;",
    ),
    (
        "Murtaza Rahimov (1930-), Başkurdistan'ın 1990-2010 yılları arasındaki başkanı;",
        "Murtaza Rahimov, bin dokuz yüz otuz doğumlu, Başkurdistan'ın bin dokuz yüz doksan ile "
        "iki bin on yılları arasındaki başkanı;",
    ),
]


def fix_tts_numbers(text: str) -> str:
    for old, new in NUMBER_FIXES:
        text = text.replace(old, new)
    return text


def word_count(text: str) -> int:
    return len(text.split())


def estimate_duration_s(text: str) -> float:
    return round(word_count(text) / WPM * 60, 1)


def build_flow_request(s: dict, kind: str) -> dict:
    """kind: 'image' or 'video'."""
    pv = s["pv"]
    duration_s = 6.0 if kind == "video" else estimate_duration_s(s["source_text"])
    slots = {
        "subject": s["subject"],
        "environment": s["environment"],
        "lighting": s["lighting"],
        "camera": s["camera"],
        "lens": {"wide": "28mm equivalent", "portrait": "85mm equivalent",
                  "normal": "50mm equivalent", "macro": "100mm macro"}.get(s.get("lens", "normal"), "50mm equivalent"),
        "motion": s["motion"] if kind == "video" else "none - still frame",
        "style": f"historical_epic_steppe: {GRADE}, {GRAIN}, {PALETTE}",
        "technical": "16:9, deep focus, period-accurate detail" if pv == PV_WIDE
                     else "16:9, shallow depth of field, stable framing",
    }
    req = {
        "task_ref": _task_id(STATE_DIR),
        "shot_id": shot_id(s["n"]),
        "prompt_version": pv,
        "slots": slots,
        "negative": NEGATIVE_VIDEO if kind == "video" else NEGATIVE_STILL,
        "references": [],
        "seed": 20260805000 + s["n"] * 10 + (1 if kind == "video" else 0),
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
        "version": 2,
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

    written_scenes = 0
    written_prompts = 0
    for s in SCENES:
        s["source_text"] = fix_tts_numbers(s["source_text"])
        sid = scene_id(s["n"])
        shid = shot_id(s["n"])
        visual_decision = "video" if s["visual"] == "video" else ("still" if s["visual"] == "still" else "reuse")
        reuse_ref = s.get("reuse_ref")
        reuse_scene_refs = None
        if reuse_ref is not None:
            reuse_scene_refs = (
                [scene_id(r) for r in reuse_ref] if isinstance(reuse_ref, list) else [scene_id(reuse_ref)]
            )

        scene_record = {
            "scene_id": sid,
            "act": 1,
            "title": s["title"],
            "summary": s["title"] + " — " + s["source_text"].split(".")[0] + ".",
            "source_text": s["source_text"],
            "duration_estimate_s": estimate_duration_s(s["source_text"]),
            "scene_type": s["scene_type"],
            "continuity_from": scene_id(s["n"] - 1) if s["n"] > 1 else None,
            "shots": [shid] if visual_decision != "reuse" else [],
            "qa_status": "pending",
            "visual_decision": visual_decision,
            "visual_reuse_of": reuse_scene_refs,
            "search_keywords": s.get("search_keywords"),
            "ai_required": bool(s.get("ai_required", False)),
        }
        (scenes_dir / f"{sid}.json").write_text(json.dumps(scene_record, indent=2, ensure_ascii=False) + "\n")
        written_scenes += 1

        if visual_decision == "reuse":
            continue

        shot_dir = prompts_dir / shid
        shot_dir.mkdir(parents=True, exist_ok=True)
        (shot_dir / "image.json").write_text(
            json.dumps(build_flow_request(s, "image"), indent=2, ensure_ascii=False) + "\n"
        )
        written_prompts += 1
        if visual_decision == "video":
            (shot_dir / "video.json").write_text(
                json.dumps(build_flow_request(s, "video"), indent=2, ensure_ascii=False) + "\n"
            )
            written_prompts += 1

    total_words = sum(word_count(s["source_text"]) for s in SCENES)
    print(f"{PROJECT_ID}: {written_scenes} scenes, {written_prompts} flow_shot_request files written")
    print(f"total narration words: {total_words}, estimated narration: {total_words / WPM:.1f} min at {WPM} wpm")


if __name__ == "__main__":
    main()
