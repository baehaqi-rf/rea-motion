# Implementation Plan
## HyperFrames Pro — Local Edition (REA + Google Flow Pipeline)

Dokumen ini merinci langkah implementasi teknis dari nol hingga siap produksi di **Windows 11 + Google Antigravity**. Rencana dibagi menjadi **5 Fase Utama (MVP 7 Hari Kerja)** ditambah **Track B Opsional** jika di kemudian hari ingin memutus ketergantungan total dari HyperFrames Core.

---

## 1. Prasyarat Lingkungan (*Environment Prerequisites*)

Pastikan seluruh komponen berikut sudah terpasang dan dapat dipanggil dari PowerShell Windows 11:

- **Node.js (v20 LTS atau lebih baru)** & `npm` / `npx`
- **FFmpeg & FFprobe** tersedia di system `PATH` (instalasi cepat: `winget install Gyan.FFmpeg`)
- **Git** untuk *white-box audit* repositori upstream
- **Google Antigravity (Desktop Windows 11)** sebagai *orchestrator* AI agent
- **Akses Google Flow** untuk STT, generasi video (Veo/Omni), gambar (Imagen/Nano Banana), dan audio/SFX

---

## 2. Struktur Direktori Proyek Standar

Seluruh komponen lokal disatukan dalam satu struktur workspace yang bersih agar mudah dibaca agent:

```text
local-video-studio/
├── docs/
│   ├── PRD_HyperFrames_Local_Pro.md
│   ├── IMPLEMENTATION_PLAN_HyperFrames_Local_Pro.md
│   └── HYPERFRAMES_WHITEBOX_SPEC.md     # Hasil audit Phase 0
├── scripts/
│   ├── Invoke-ReaVideoInspect.ps1       # Layer 1: FFprobe + FFmpeg + WAV
│   ├── Build-BeatSheet.mjs              # Layer 2/3: Gabung Scene + Google Flow STT
│   └── Run-ParityCheck.ps1              # Layer 4: Render still frames untuk QA
├── presets/
│   └── minimalist_editorial.json        # Pustaka Style Presets tak terbatas
├── skills/
│   └── local-hyperframes-pro/
│       └── SKILL.md                     # Skill kustom Antigravity
├── projects/
│   └── <nama_proyek>/
│       ├── .rea_inspect/                # Keyframes, metadata, WAV, transcript_words.json
│       ├── assets/flow/                 # Aset lokal dari Google Flow (video, images, audio)
│       ├── evidence.json                # Epistemic Motion Ledger
│       ├── beat_sheet.json              # Master Timeline tersinkronisasi STT
│       └── composition/                 # Output proyek HyperFrames Free -> render MP4
└── upstream/
    └── hyperframes-upstream/            # Clone baca-saja untuk referensi white-box
```

---

## 3. Rencana Eksekusi Bertahap (MVP — Jalur Hybrid)

### Phase 0: Sandbox Setup & White-Box Audit (Hari 1)
**Tujuan:** Memverifikasi kontrak teknis asli `heygen-com/hyperframes` dan memastikan render lokal berjalan mulus di Windows 11 tanpa error.

| No | Tugas Teknis | Perintah / Aksi | Output Terverifikasi |
|---|---|---|---|
| 0.1 | Clone repositori upstream untuk inspeksi *white-box* | `git clone https://github.com/heygen-com/hyperframes.git upstream/hyperframes-upstream` | Folder `upstream/` siap dibaca |
| 0.2 | Jalankan audit arsitektur via Antigravity | Petakan *Composition Schema*, *Virtual Clock*, struktur blok Registry, perintah CLI *still frame*, dan batas Free vs Pro | `docs/HYPERFRAMES_WHITEBOX_SPEC.md` |
| 0.3 | Instalasi minimalis (3 skill inti gratis saja) | Pasang hanya `/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry` di workspace uji | Tidak ada skill Pro berbayar yang aktif |
| 0.4 | Uji coba *Hello World* render MP4 lokal | Inisialisasi proyek tes 5 detik, render ke MP4 di Windows 11 | File MP4 $1080\text{p}$ tajam, $0\text{ watermark}$, bebas *flicker* |

**Exit Gate Phase 0:** Mesin HyperFrames Free terbukti merender MP4 dan *still frame* secara deterministik di Windows 11.

---

### Phase 1: Layer 1 — REA Video Extractor & STT Pipeline (Hari 2)
**Tujuan:** Menggantikan tahap ekstraksi `/reverse-any-video` dengan pipeline lokal nol biaya.

| No | Tugas Teknis | Detail Implementasi | Output Terverifikasi |
|---|---|---|---|
| 1.1 | Finalisasi `scripts/Invoke-ReaVideoInspect.ps1` | Jalankan `ffprobe`, FFmpeg `select='eq(n,0)+gt(scene,T)'` + `showinfo`, fallback sampling `1 fps`, dan ekstraksi WAV 16kHz Mono | Folder `.rea_inspect/` lengkap dengan `inspect_manifest.json` |
| 1.2 | Uji *edge cases* Windows 11 | Tes dengan video berisi spasi pada nama file, video tanpa audio, dan rasio vertikal ($9:16$) maupun lanskap ($16:9$) | Skrip bebas error *locale* koma & UTF-8 BOM |
| 1.3 | Validasi alur Google Flow STT | Unggah `audio/stt_input_16k_mono.wav` ke Google Flow STT, simpan hasilnya ke `flow_stt/transcript_words.json` | JSON berisi `word`, `start_sec`, dan `end_sec` yang valid |

**Exit Gate Phase 1:** Satu video referensi berdurasi 15–30 detik berhasil dipecah menjadi *keyframes* bertimestamp + *word-level STT JSON*.

---

### Phase 2: Layer 2 & 3 — Beat-Sheet, Motion Evidence & Style Sampler (Hari 3–4)
**Tujuan:** Mengubah data mentah (gambar + STT) menjadi spesifikasi deterministik (*engine-agnostic*) dan pustaka *Style Preset*.

| No | Tugas Teknis | Detail Implementasi | Output Terverifikasi |
|---|---|---|---|
| 2.1 | Buat skrip `scripts/Build-BeatSheet.mjs` | Node.js script yang mencocokkan timestamp setiap *scene cut* (`inspect_manifest.json`) dengan kata kunci di `transcript_words.json` | `beat_sheet.json` otomatis |
| 2.2 | Susun protokol Vision-to-Ledger | Template prompt terstruktur bagi agent Antigravity untuk membaca `keyframes_scene/` + `beat_sheet.json` lalu mengisi `evidence.json` (pemisahan tegas `observed` vs `inferred`) | `evidence.json` tervalidasi |
| 2.3 | Bangun `local-style-sampler` | Ekstraktor token gaya (Hex palette, font stack, *pacing*, *easing*, *overlay rules*) ke folder `presets/` | Minimal 2 preset awal (`minimalist_saas.json` & `editorial_explainer.json`) |
| 2.4 | Uji Mode REA Web/DOM (Bonus Keunggulan) | Tambahkan jalur ekstraksi langsung dari URL *live website* ke format `presets/*.json` | Preset gaya dari website asli siap dipakai di video |

**Exit Gate Phase 2:** Agent mampu menghasilkan `evidence.json` dan `presets/*.json` yang konsisten dan dapat dipakai ulang untuk membuat episode baru dengan skrip berbeda.

---

### Phase 3: Layer 4 — Google Flow Asset Bridge & Render Adapter (Hari 5)
**Tujuan:** Menghubungkan aset generatif dari Google Flow ke komposisi HyperFrames Free + Registry.

| No | Tugas Teknis | Detail Implementasi | Output Terverifikasi |
|---|---|---|---|
| 3.1 | Standarisasi folder `assets/flow/` | Struktur baku untuk menempatkan B-roll (Veo/Omni), gambar (Imagen/Nano Banana), *voice-over*, dan SFX dari Google Flow | Manifest aset lokal tersinkronisasi |
| 3.2 | Pemetaan Blok HyperFrames Registry | Buat daftar kurasi 25–40 blok Registry paling estetik (*kinetic typography*, transisi, *device mockup*, *data callout*, caption) berdasarkan hasil Phase 0 | `docs/CURATED_REGISTRY_MAP.md` (mencegah *AI slop*) |
| 3.3 | Bangun alur kompilasi komposisi | Agent mengonversi `evidence.json` + `beat_sheet.json` + aset Google Flow menjadi proyek HTML/CSS/JS HyperFrames dengan injeksi token dari `presets/` | Proyek di `composition/` siap preview & render |

**Exit Gate Phase 3:** Video komposisi pertama yang menggabungkan aset Google Flow + blok HyperFrames Registry berhasil dirender lokal ke MP4.

---

### Phase 4: Closed-Loop Visual Parity QA, Skill Packaging & Benchmark (Hari 6–7)
**Tujuan:** Membungkus seluruh alur menjadi satu skill Antigravity yang rapi, aman dari konflik workspace, dan terukur performanya.

| No | Tugas Teknis | Detail Implementasi | Output Terverifikasi |
|---|---|---|---|
| 4.1 | Bangun `scripts/Run-ParityCheck.ps1` | Otomatis merender 4–6 *still frames* dari komposisi pada titik waktu kritis di `beat_sheet.json` | Folder `qa_stills/` untuk inspeksi visual agent |
| 4.2 | Paketkan `skills/local-hyperframes-pro/SKILL.md` | Tulis instruksi *end-to-end* (Inspect → Flow Bridge → Ledger → Render → Parity QA) beserta aturan *trigger boundary* eksplisit | Skill siap aktif di Antigravity tanpa bentrok dengan Remotion |
| 4.3 | *Head-to-Head Benchmark* (Video 15 Detik) | Bandingkan waktu produksi, kemudahan iterasi, dan kehalusan animasi untuk skenario yang sama: HyperFrames Local Pro vs Remotion | Laporan metrik keputusan penggunaan harian |

**Exit Gate Phase 4 (Definition of Done MVP):**
- Satu perintah/workflow di Antigravity mampu mereplikasi gaya video referensi 15 detik menggunakan aset Google Flow dan menghasilkan MP4 $1080\text{p}$ lolos *Visual Parity QA* dengan biaya HeyGen **$0**.

---

## 4. Aturan *Trigger Boundary* di Google Antigravity

Untuk mencegah *context bloat* dan kebingungan pemilihan mesin render di workspace Antigravity, terapkan aturan routing berikut:

1. **Default Demo UI / Produk Interaktif Kompleks:** Tetap arahkan ke alur kerja **Remotion** (komponen React/TypeScript, *spring physics* presisi).
2. **Trigger Eksplisit Local HyperFrames Pro:** Aktifkan skill `local-hyperframes-pro` hanya ketika prompt menyebut kata kunci **`hyperframes`**, **`reverse video`**, **`style preset`**, atau **`registry`**.
3. **Pemisahan Tugas Inferensi:** Seluruh permintaan aset video sinematik, gambar, *voice-over*, dan STT selalu dirutekan ke **Google Flow** (tidak pernah memanggil endpoint cloud HeyGen).

---

## 5. Track B (Opsional — Evolusi Masa Depan): 100% Standalone Engine

Jika di masa depan diperlukan kepemilikan kode 100% independen tanpa instalasi paket HyperFrames sama sekali, hanya **Layer 4 (Render Adapter)** yang perlu diganti melalui 3 langkah:

1. **Deterministic Frame Capture Engine:** Bangun *runner* Node.js berbasis **Playwright (Chromium)** yang menginjeksi *virtual timeline clock* (`window.__setFrame(n, fps)`), menonaktifkan timer *real-time*, lalu menangkap tangkapan layar *frame-by-frame* secara paralel.
2. **FFmpeg Pipe Muxer:** Alirkan *raw frame stream* langsung ke `stdin` FFmpeg (`-f image2pipe`) sambil menggabungkan *audio tracks* dari Google Flow menjadi MP4 H.264/AAC.
3. **Curated Internal Block Library:** Pindahkan 25–40 pola animasi paling sering dipakai menjadi pustaka komponen HTML/CSS/SVG internal milik sendiri.

Karena `inspect_manifest.json`, `transcript_words.json`, `evidence.json`, `beat_sheet.json`, dan `presets/*.json` sudah dirancang *engine-agnostic* sejak Phase 1–2, seluruh investasi kerja pada lapisan REA dan Google Flow tetap terpakai 100%.

---

## 6. Checklist Verifikasi Cepat Sebelum Go-Live

- [ ] `ffmpeg` dan `ffprobe` terdeteksi di PowerShell Windows 11.
- [ ] `docs/HYPERFRAMES_WHITEBOX_SPEC.md` selesai dan skema *virtual clock* terkonfirmasi.
- [ ] `Invoke-ReaVideoInspect.ps1` lolos uji pada video lanskap ($16:9$) dan vertikal ($9:16$).
- [ ] Hasil Google Flow STT (`transcript_words.json`) berhasil menyinkronkan `beat_sheet.json`.
- [ ] Minimal 2 file di `presets/` berhasil dipakai untuk menghasilkan video baru tanpa menjiplak mentah.
- [ ] *Closed-loop QA* berhasil mendeteksi dan memperbaiki *overflow* teks sebelum render MP4 final.
- [ ] Aturan *trigger boundary* terpasang agar workspace Antigravity tetap ringan dan bebas konflik.