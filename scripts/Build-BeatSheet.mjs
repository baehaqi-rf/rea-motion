#!/usr/bin/env node
/**
 * Layer 2 & 3: Beat-Sheet Synchronizer (Scene Cuts x Google Flow Word-Level STT)
 * Produces deterministic `beat_sheet.json` (UTF-8 without BOM) with frame-accurate cues.
 */
import fs from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const key = argv[i];
    if (key.startsWith("--")) {
      args[key.slice(2)] = argv[i + 1];
      i++;
    }
  }
  return args;
}

const args = parseArgs(process.argv);
const projectDir = args.project || process.cwd();
const inspectManifestPath =
  args.manifest || path.join(projectDir, ".rea_inspect", "inspect_manifest.json");
const sttPath =
  args.stt || path.join(projectDir, ".rea_inspect", "flow_stt", "transcript_words.json");
const outPath = args.out || path.join(projectDir, "beat_sheet.json");

if (!fs.existsSync(inspectManifestPath)) {
  console.error(`Missing inspect_manifest.json at: ${inspectManifestPath}`);
  process.exit(1);
}

const manifest = JSON.parse(fs.readFileSync(inspectManifestPath, "utf8"));
const fps = Number(manifest.metadata?.fps || 30);
const durationSec = Number(manifest.metadata?.duration_sec || 10);

let words = [];
if (fs.existsSync(sttPath)) {
  const sttData = JSON.parse(fs.readFileSync(sttPath, "utf8"));
  words = Array.isArray(sttData.words) ? sttData.words : [];
}

// Build shot boundaries from hyperframes_measure.shots or scene_keyframes
let rawShots = [];
if (manifest.hyperframes_measure?.shots?.length) {
  rawShots = manifest.hyperframes_measure.shots.map((s, idx) => ({
    scene_id: `sc_${String(idx + 1).padStart(2, "0")}`,
    start_sec: Number(s.start),
    end_sec: Number(s.end),
    duration_sec: Number((s.end - s.start).toFixed(3)),
  }));
} else {
  const cuts = manifest.scene_keyframes || [{ timestamp_sec: 0 }];
  for (let i = 0; i < cuts.length; i++) {
    const start = Number(cuts[i].timestamp_sec || 0);
    const end = i + 1 < cuts.length ? Number(cuts[i + 1].timestamp_sec) : durationSec;
    if (end > start) {
      rawShots.push({
        scene_id: `sc_${String(i + 1).padStart(2, "0")}`,
        start_sec: Number(start.toFixed(3)),
        end_sec: Number(end.toFixed(3)),
        duration_sec: Number((end - start).toFixed(3)),
      });
    }
  }
}

const scenes = rawShots.map((shot) => {
  const startFrame = Math.floor(shot.start_sec * fps);
  const endFrame = Math.floor(shot.end_sec * fps);
  // Words falling within [start_sec - 0.08, end_sec + 0.05]
  const shotWords = words
    .filter((w) => w.start_sec >= shot.start_sec - 0.08 && w.start_sec < shot.end_sec)
    .map((w) => ({
      word: w.word,
      abs_start_sec: Number(w.start_sec),
      abs_end_sec: Number(w.end_sec),
      local_start_sec: Number(Math.max(0, w.start_sec - shot.start_sec).toFixed(3)),
      local_duration_sec: Number(Math.max(0.08, w.end_sec - w.start_sec).toFixed(3)),
    }));

  return {
    ...shot,
    start_frame: startFrame,
    end_frame: endFrame,
    duration_frames: Math.max(1, endFrame - startFrame),
    hyperframes_start_attr: Number((startFrame / fps).toFixed(6)),
    hyperframes_duration_attr: Number(((endFrame - startFrame) / fps).toFixed(6)),
    transcript_segment: shotWords.map((w) => w.word).join(" "),
    word_cues: shotWords,
  };
});

const beatSheet = {
  schema_version: "1.1.0",
  generated_at: new Date().toISOString(),
  canvas: {
    width: manifest.metadata.width,
    height: manifest.metadata.height,
    fps,
    fps_rational: manifest.metadata.fps_rational,
    duration_sec: durationSec,
  },
  total_scenes: scenes.length,
  total_words: words.length,
  scenes,
};

fs.writeFileSync(outPath, JSON.stringify(beatSheet, null, 2), { encoding: "utf8" });
console.log(`Beat sheet generated (${scenes.length} scenes, ${words.length} words) -> ${outPath}`);
