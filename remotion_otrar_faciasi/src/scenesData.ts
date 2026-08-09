// AUTO-GENERATED from measured audio durations (ffprobe). Do not hand-edit.
// Regenerate with scripts/generate_otrar_scenes_data.py whenever
// assets/audio/NAR-SC-*.wav or a scene's shot list changes.
import type { Caption } from "@remotion/captions";

export interface SceneVisual {
  type: "video" | "still";
  file: string;
  // Explicit slot length in frames - set for video shots (their own
  // ffprobe-measured clip duration, see file header). Omitted for
  // still shots, which split whatever frames remain evenly.
  durationFrames?: number;
}

export interface SceneData {
  id: string;
  title: string;
  audioFile: string | null;
  visuals: SceneVisual[];
  startFrame: number;
  durationFrames: number;
  captions?: Caption[];
}

export const TOTAL_FRAMES = 9760;
export const FPS = 30;

export const SCENES: SceneData[] = [
  { id: "SC-001", title: "Kervan Otrar'a Varıyor", audioFile: "../public/audio/NAR-SC-001.wav", visuals: [{"type": "still", "file": "../public/still/SH-001-01.jpeg"}, {"type": "still", "file": "../public/still/SH-001-02.jpeg"}, {"type": "still", "file": "../public/still/SH-001-03.jpeg"}], startFrame: 0, durationFrames: 607 }, // audio 20.245s
  { id: "SC-002", title: "İki İmparatorluk Sınır Komşusu Oluyor", audioFile: "../public/audio/NAR-SC-002.wav", visuals: [{"type": "still", "file": "../public/still/SH-002-01.jpeg"}, {"type": "still", "file": "../public/still/SH-002-02.jpeg"}, {"type": "still", "file": "../public/still/SH-002-03.jpeg"}, {"type": "still", "file": "../public/still/SH-002-04.jpeg"}], startFrame: 607, durationFrames: 582 }, // audio 19.409s
  { id: "SC-003", title: "İnalcık'ın Kararı", audioFile: "../public/audio/NAR-SC-003.wav", visuals: [{"type": "video", "file": "../public/video/SH-003-01.mp4", "durationFrames": 180}, {"type": "still", "file": "../public/still/SH-003-02.jpeg"}, {"type": "still", "file": "../public/still/SH-003-03.jpeg"}, {"type": "still", "file": "../public/still/SH-003-04.jpeg"}], startFrame: 1189, durationFrames: 546 }, // audio 18.207s
  { id: "SC-004", title: "Neden? Üç Rakip Açıklama", audioFile: "../public/audio/NAR-SC-004.wav", visuals: [{"type": "still", "file": "../public/still/SH-004-01.jpeg"}, {"type": "still", "file": "../public/still/SH-004-02.jpeg"}, {"type": "still", "file": "../public/still/SH-004-03.jpeg"}], startFrame: 1735, durationFrames: 776 }, // audio 25.861s
  { id: "SC-016", title: "Sessiz Mola I", audioFile: null, visuals: [{"type": "still", "file": "../public/still/SH-002-03.jpeg"}], startFrame: 2511, durationFrames: 300 }, // audio 10.0s
  { id: "SC-005", title: "Bir Aile Sırrı", audioFile: "../public/audio/NAR-SC-005.wav", visuals: [{"type": "still", "file": "../public/still/SH-005-01.jpeg"}, {"type": "still", "file": "../public/still/SH-005-02.jpeg"}, {"type": "still", "file": "../public/still/SH-005-03.jpeg"}], startFrame: 2811, durationFrames: 292 }, // audio 9.744s
  { id: "SC-013", title: "İki Tarihçi, İki Farklı Suçlu", audioFile: "../public/audio/NAR-SC-013.wav", visuals: [{"type": "still", "file": "../public/still/SH-005-01.jpeg"}, {"type": "still", "file": "../public/still/SH-005-02.jpeg"}, {"type": "still", "file": "../public/still/SH-005-03.jpeg"}], startFrame: 3103, durationFrames: 708 }, // audio 23.589s
  { id: "SC-006", title: "Elçilerin Küçük Düşürülmesi", audioFile: "../public/audio/NAR-SC-006.wav", visuals: [{"type": "video", "file": "../public/video/SH-006-01.mp4", "durationFrames": 180}, {"type": "still", "file": "../public/still/SH-006-02.jpeg"}, {"type": "still", "file": "../public/still/SH-006-03.jpeg"}], startFrame: 3811, durationFrames: 647 }, // audio 21.551s
  { id: "SC-007", title: "Kışkırtma mı, Bahane mi?", audioFile: "../public/audio/NAR-SC-007.wav", visuals: [{"type": "still", "file": "../public/still/SH-007-01.jpeg"}, {"type": "still", "file": "../public/still/SH-007-02.jpeg"}, {"type": "still", "file": "../public/still/SH-007-03.jpeg"}, {"type": "still", "file": "../public/still/SH-007-04.jpeg"}, {"type": "still", "file": "../public/still/SH-007-05.jpeg"}], startFrame: 4458, durationFrames: 1050 }, // audio 35.004s
  { id: "SC-014", title: "Bu Hikâye Nereden Biliniyor?", audioFile: "../public/audio/NAR-SC-014.wav", visuals: [{"type": "still", "file": "../public/still/SH-007-04.jpeg"}, {"type": "still", "file": "../public/still/SH-007-05.jpeg"}, {"type": "still", "file": "../public/still/SH-007-02.jpeg"}], startFrame: 5508, durationFrames: 733 }, // audio 24.424s
  { id: "SC-008", title: "Sefer Başlıyor", audioFile: "../public/audio/NAR-SC-008.wav", visuals: [{"type": "video", "file": "../public/video/SH-008-01.mp4", "durationFrames": 180}, {"type": "still", "file": "../public/still/SH-008-02.jpeg"}, {"type": "still", "file": "../public/still/SH-008-03.jpeg"}], startFrame: 6241, durationFrames: 339 }, // audio 11.311s
  { id: "SC-009", title: "Beş Aylık Direniş", audioFile: "../public/audio/NAR-SC-009.wav", visuals: [{"type": "still", "file": "../public/still/SH-009-01.jpeg"}, {"type": "still", "file": "../public/still/SH-009-02.jpeg"}, {"type": "still", "file": "../public/still/SH-009-03.jpeg"}], startFrame: 6580, durationFrames: 472 }, // audio 15.726s
  { id: "SC-017", title: "Sessiz Mola II", audioFile: null, visuals: [{"type": "still", "file": "../public/still/SH-012-02.jpeg"}], startFrame: 7052, durationFrames: 300 }, // audio 10.0s
  { id: "SC-010", title: "Efsane mi, Gerçek mi: Gümüş İdamı", audioFile: "../public/audio/NAR-SC-010.wav", visuals: [{"type": "still", "file": "../public/still/SH-010-01.jpeg"}, {"type": "still", "file": "../public/still/SH-010-02.jpeg"}, {"type": "still", "file": "../public/still/SH-010-03.jpeg"}, {"type": "still", "file": "../public/still/SH-010-04.jpeg"}], startFrame: 7352, durationFrames: 638 }, // audio 21.264s
  { id: "SC-011", title: "Toprağın Söyledikleri", audioFile: "../public/audio/NAR-SC-011.wav", visuals: [{"type": "still", "file": "../public/still/SH-011-01.jpeg"}, {"type": "still", "file": "../public/still/SH-011-02.jpeg"}, {"type": "still", "file": "../public/still/SH-011-03.jpeg"}], startFrame: 7990, durationFrames: 603 }, // audio 20.088s
  { id: "SC-015", title: "Anlatılmamış Yarısı", audioFile: "../public/audio/NAR-SC-015.wav", visuals: [{"type": "still", "file": "../public/still/SH-011-01.jpeg"}, {"type": "still", "file": "../public/still/SH-011-02.jpeg"}, {"type": "still", "file": "../public/still/SH-011-03.jpeg"}], startFrame: 8593, durationFrames: 570 }, // audio 18.991s
  { id: "SC-012", title: "Bir Kervanın Gölgesi", audioFile: "../public/audio/NAR-SC-012.wav", visuals: [{"type": "still", "file": "../public/still/SH-012-01.jpeg"}, {"type": "still", "file": "../public/still/SH-012-02.jpeg"}, {"type": "still", "file": "../public/still/SH-012-03.jpeg"}], startFrame: 9163, durationFrames: 597 }, // audio 19.905s
];
