#!/usr/bin/env python3
"""
Generates remotion_atlas/src/data/vN.ts from measured audio durations for a
given Atlas video. Narration is the clock: each scene's timeline duration is
derived from its own narration file's real length via ffprobe. Seconds are
converted to frames once, at this timeline boundary (round(seconds * fps)).

Usage: generate_atlas_scenes_data.py <video_number>
Edit VIDEOS below to add/adjust a video's figure list, display names, and subtitle.
"""
import json
import subprocess
import sys

FPS = 30
REPO_ROOT = "/home/user/Sesli-kitap-st-dyosu"
PROJECT = "PRJ-gok-umay-atlasi"

VIDEOS = {
    1: {
        "subtitle": "GÖK UMAY MİTOLOJİK ATLASI — I. KOZMOLOJİ VE MİTOLOJİK FİGÜRLER",
        "figures": [
            ("TENGRI", "Tengri"),
            ("TURUL", "Turul"),
            ("KONRUL", "Konrul"),
            ("GUN-ANA", "Gün Ana"),
            ("AY-ATA", "Ay Ata"),
            ("ULGEN", "Ülgen"),
            ("ERLIK-HAN", "Erlik Han"),
            ("KAYRA-HAN", "Kayra Han"),
            ("UMAY-ANA", "Umay Ana"),
        ],
    },
    2: {
        "subtitle": "GÖK UMAY MİTOLOJİK ATLASI — II. İYELER (DOĞA RUHLARI)",
        "figures": [
            ("EV-IYESI", "Ev İyesi"),
            ("OCAK-IYESI-ALTAY", "Ocak İyesi (Altay)"),
            ("OCAK-IYESI-TUVA", "Tuva Ocak İyesi"),
            ("OCAK-IYESI-HAKAS", "Habın İyezi (Hakas)"),
            ("OCAK-IYESI-SAHA", "Uot İye (Saha)"),
            ("SU-IYESI", "Su İyesi"),
            ("YER-SU-IYESI", "Yer-Su İyesi"),
            ("ORMAN-IYESI", "Orman İyesi"),
            ("DAG-IYESI", "Dağ İyesi"),
        ],
    },
    3: {
        "subtitle": "GÖK UMAY MİTOLOJİK ATLASI — III. BOZKIRIN KADINLARI",
        "figures": [
            ("BAYANAY", "Bayanay"),
            ("ASINA-SOYU", "Kurt Ana ve Aşina Soyu"),
            ("ASINA", "Aşina"),
            ("HATUNLAR", "Hatunlar"),
            ("TOMRIS-HATUN", "Tomris Hatun"),
            ("ASINA-HANEDANI", "Aşina Hanedanı Kadınları"),
            ("CING-HATUN", "Çing Hatun"),
            ("TAIDULA-HATUN", "Taidula Hatun"),
            ("TERKEN-HATUN", "Terken Hatun"),
            ("SARA-HATUN", "Sara Hatun"),
            ("SUYUMBIKE-HATUN", "Süyümbike Hatun"),
            ("BACIYAN-I-RUM", "Bacıyan-ı Rum"),
            ("UKOK-PRENSESI", "Ukok Prensesi"),
            ("BEREL-KADINI", "Berel Kadını"),
            ("SUBESHI-KADINLARI", "Subeshi Kadınları"),
            ("LOULAN-GUZELI", "Loulan Güzeli"),
        ],
    },
    4: {
        "subtitle": "GÖK UMAY MİTOLOJİK ATLASI — IV. DEVLET KURAN HÜKÜMDARLAR I",
        "figures": [
            ("METE-HAN", "Mete Han"),
            ("KUL-TIGIN", "Kül Tigin"),
            ("BILGE-KAGAN", "Bilge Kağan"),
            ("BUMIN-KAGAN", "Bumin Kağan"),
            ("ISTEMI-YABGU", "İstemi Yabgu"),
            ("EMIR-TIMUR", "Emir Timur"),
            ("ALP-ARSLAN", "Alp Arslan"),
            ("SUBUTAY-BAATUR", "Subutay Baatur"),
            ("SULTAN-BAYBARS", "Sultan Baybars"),
        ],
    },
    5: {
        "subtitle": "GÖK UMAY MİTOLOJİK ATLASI — V. DEVLET KURAN HÜKÜMDARLAR II",
        "figures": [
            ("CENGIZ-HAN", "Cengiz Han"),
            ("YILDIRIM-BAYEZID", "Yıldırım Bayezid"),
            ("GAZNELI-MAHMUT", "Gazneli Mahmut"),
            ("KANUNI-SULEYMAN", "Kanuni Sultan Süleyman"),
            ("FATIH-SULTAN-MEHMED", "Fatih Sultan Mehmed"),
            ("KAZIM-KARABEKIR", "Kâzım Karabekir"),
            ("ATATURK", "Gazi Mustafa Kemal Atatürk"),
            ("MELIKSAH", "Melikşah"),
            ("ATTILA-HAN", "Attila Han"),
        ],
    },
    6: {
        "subtitle": "GÖK UMAY MİTOLOJİK ATLASI — VI. KAPANIŞ",
        "figures": [
            ("ADSIZ-BOZKIR-ERLERI", "Adsız Bozkır Erleri"),
            ("TURKLUK-SOZLERI", "Türklük Adına Söylenmiş Sözler"),
            ("GENCLIGE-MESAJLAR", "Tarihten Gençliğe"),
            ("SON-SOZ", "Son Söz"),
        ],
    },
}


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def main():
    if len(sys.argv) != 2:
        print("Usage: generate_atlas_scenes_data.py <video_number>")
        sys.exit(1)
    video_num = int(sys.argv[1])
    config = VIDEOS[video_num]
    figures = config["figures"]
    if not figures:
        print(f"No figures configured for video {video_num} yet.")
        sys.exit(1)

    scenes = []
    cumulative_frame = 0
    for name, _display in figures:
        audio_path = f"{REPO_ROOT}/projects/{PROJECT}/assets/audio/NAR-{name}.wav"
        audio_duration_s = probe_duration(audio_path)
        duration_frames = round(audio_duration_s * FPS)
        scenes.append({
            "id": name,
            "audioFile": f"../public/audio/NAR-{name}.wav",
            "visualFile": f"../public/still/{name}.png",
            "startFrame": cumulative_frame,
            "durationFrames": duration_frames,
            "audioDurationS": round(audio_duration_s, 3),
        })
        cumulative_frame += duration_frames

    total_frames = cumulative_frame
    print(f"Video {video_num} total frames: {total_frames}  Total seconds: {total_frames / FPS:.2f}  ({total_frames / FPS / 60:.2f} min)")

    lines = [
        "// AUTO-GENERATED from measured audio durations (ffprobe). Do not hand-edit.",
        "// Regenerate with scripts/generate_atlas_scenes_data.py whenever audio assets change.",
        "export interface SceneData {",
        "  id: string;",
        "  audioFile: string;",
        "  visualFile: string;",
        "  startFrame: number;",
        "  durationFrames: number;",
        "}",
        "",
        f"export const TOTAL_FRAMES = {total_frames};",
        f"export const FPS = {FPS};",
        f'export const SUBTITLE = "{config["subtitle"]}";',
        "export const DISPLAY_NAMES: Record<string, string> = {",
    ]
    for name, display in figures:
        lines.append(f'  "{name}": "{display}",')
    lines.append("};")
    lines.append("")
    lines.append("export const SCENES: SceneData[] = [")
    for s in scenes:
        lines.append(
            f'  {{ id: "{s["id"]}", audioFile: "{s["audioFile"]}", '
            f'visualFile: "{s["visualFile"]}", startFrame: {s["startFrame"]}, durationFrames: {s["durationFrames"]} }}, '
            f'// audio {s["audioDurationS"]}s'
        )
    lines.append("];")

    out_path = f"{REPO_ROOT}/remotion_atlas/src/data/v{video_num}.ts"
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {out_path}")

    # JSON sidecar, same scene list, for scripts/render_scene_clips.py to
    # consume without needing a TypeScript parser. Not used by Remotion itself.
    json_path = f"{REPO_ROOT}/remotion_atlas/src/data/v{video_num}.json"
    with open(json_path, "w") as f:
        json.dump({
            "composition": f"atlas-video-{video_num}",
            "project": PROJECT,
            "remotion_dir": "remotion_atlas",
            "total_frames": total_frames,
            "fps": FPS,
            "scenes": scenes,
        }, f, indent=2, ensure_ascii=False)
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
