# Product Requirements Document (PRD)
## HyperFrames Pro — Local Edition (REA + Google Flow Pipeline)

- **Versi Dokumen:** 1.0
- **Status:** Draft Siap Eksekusi
- **Target Lingkungan:** Windows 11, PowerShell, Node.js, FFmpeg, Google Antigravity, Google Flow
- **Prinsip Lisensi & Biaya:** $0 biaya langganan HeyGen Pro (memanfaatkan inti *open-source* Apache-2.0 + inferensi penuh di Google Flow)

---

## 1. Ringkasan Eksekutif & Analisa Ulang Arsitektur

Membangun ulang kemampuan **HyperFrames Pro** secara lokal menghadapi satu keputusan arsitektur utama: **apakah kita memasang inti *open-source* gratisnya lalu membangun ulang lapisan Pro-nya (Opsi A — Hybrid)**, atau **membangun ulang 100% mesin render dari nol tanpa paket HyperFrames sama sekali (Opsi B — Full Rebuild)**?

### 1.1 Matriks Analisa Trade-Off

| Dimensi Evaluasi | Opsi A: Hybrid (Free Core + Custom Pro Layer) | Opsi B: Full Rebuild (100% Standalone Engine) |
|---|---|---|
| **Kecepatan Sampai Produksi (MVP)** | **Sangat Cepat (3–7 hari)** | Lambat (2–4 minggu) |
| **Biaya Operasional Bulanan** | **$0** (Core & ~450 blok Registry gratis Apache-2.0) | **$0** |
| **Kualitas Pustaka Animasi Awal** | Langsung tersedia ~450 blok siap edit | Harus membangun komponen animasi dari nol |
| **Risiko Teknis Render** | Rendah (mesin *HTML-to-MP4* sudah teruji) | Tinggi (*virtual clock*, *frame jitter*, sinkronisasi audio) |
| **Ketergantungan Upstream** | Sedang (bergantung pada CLI/Core gratis HyperFrames) | Nol (100% independen & kepemilikan IP penuh) |

### 1.2 Keputusan Arsitektur yang Direkomendasikan: *Phased Engine-Agnostic Architecture*

Alih-alih terjebak memilih salah satu secara kaku, PRD ini mengunci strategi **dua tahap berbasis *Adapter Pattern***:

1. **Fase 1 (MVP — Jalur Hybrid):** Memasang **HyperFrames Core + CLI + Registry (versi gratis Apache-2.0)** sebagai *rendering target* pertama, sambil membangun **100% lapisan Pro secara lokal** (ekstraktor REA, *Style Sampler*, jembatan **Google Flow**, dan *Visual Parity QA*).
2. **Fase 2 (Opsional — Decoupling Penuh):** Karena seluruh otak sistem (REA Extractor, Motion Evidence Ledger, dan Google Flow Bridge) menghasilkan spesifikasi JSON yang **independen dari mesin render (*engine-agnostic*)**, *render engine* di bagian hilir dapat diganti kapan saja ke mesin *standalone* buatan sendiri (Playwright *virtual-clock* + FFmpeg atau Remotion) tanpa menulis ulang modul Pro sedikit pun.

---

## 2. Pernyataan Masalah & Tujuan Produk

### 2.1 Masalah yang Diselesaikan
- **Paywall Fitur Otomatisasi:** Fitur paling bernilai dari HyperFrames (`/reverse-any-video` dan `/style-sampling`) dikunci di paket Pro ($25/bulan).
- **Vendor Lock-in Media Cloud:** Penggunaan `/media-use` versi Pro memaksa pemakaian kredit HeyGen untuk avatar, video AI, dan audio, padahal **Google Flow** sudah menyediakan seluruh kebutuhan inferensi (*video, image, audio, voice-over, dan STT*).
- **Keterbatasan Preset:** `/style-sampling` bawaan hanya menyediakan 5 gaya *explainer* baku, yang rawan memicu tampilan seragam (*template fatigue*).
- **Risiko Konflik Workspace:** Instalasi massal seluruh skill bawaan berisiko memicu *context bloat* dan tabrakan *routing* dengan alur kerja produksi video yang sudah ada di Google Antigravity.

### 2.2 Target & Metrik Keberhasilan (KPI)
1. **Feature Parity 100%:** Mampu merekonstruksi struktur visual dan ritme video referensi menjadi proyek *HTML-to-MP4* yang dapat diedit sepenuhnya secara lokal.
2. **Zero HeyGen Cloud Spend:** 100% generasi media dan transkripsi STT berjalan melalui **Google Flow**.
3. **Word-Level Beat Sync:** Akurasi sinkronisasi teks kinetik dan perpindahan adegan terhadap audio narasi dengan presisi $\le 100\text{ ms}$ menggunakan *timestamps* STT Google Flow.
4. **Render Determinism:** Output MP4 lokal $1080\text{p}$ ($30\text{ fps}$ atau $60\text{ fps}$) bebas *watermark*, bebas *flicker*, dan lolos pemeriksaan *Visual Parity QA*.

---

## 3. Arsitektur Sistem (*Separation of Concerns*)

Sistem dibagi menjadi **4 Lapisan Terisolasi**:

```text
[Input: Video MP4 / Live URL / Brief]
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│ LAYER 1: REA Local Inspection Engine (Windows 11)      │
│ - ffprobe metadata & FFmpeg scene-cut + fallback FPS   │
│ - Audio extraction (WAV 16kHz Mono PCM)                │
│ - Opsional: DOM/CSS Inspection untuk input Live URL    │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ LAYER 2: Google Flow Inference Bridge (Cloud GPU Only) │
│ - STT (Speech-to-Text) -> word-level timestamps JSON   │
│ - Video B-Roll (Veo / Omni)                            │
│ - Keyframes & Ilustrasi (Imagen / Nano Banana)         │
│ - Voice-Over, Musik & SFX                              │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ LAYER 3: Motion Evidence & Style Ledger (Engine-Agnostic)
│ - evidence.json (Observed vs Inferred per adegan)      │
│ - beat_sheet.json (Sinkronisasi STT x Scene Cut)       │
│ - STYLE_PRESETS/*.json (Pustaka gaya tak terbatas)     │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ LAYER 4: Render Adapter & Closed-Loop Parity QA        │
│ - Adapter A (MVP): HyperFrames Free Core + Registry    │
│ - Adapter B (Future): Custom Playwright+FFmpeg / React │
│ - Still-frame render -> Visual Parity Audit -> MP4     │
└────────────────────────────────────────────────────────┘
```

---

## 4. Persyaratan Fungsional (*Functional Requirements*)

### FR-01: Modul `local-reverse-any-video` (Pengganti `/reverse-any-video` Pro)
- **FR-01.1:** Menerima input berupa file video lokal (`.mp4`, `.mov`, `.webm`) atau URL *live website* (Mode REA DOM).
- **FR-01.2:** Mengekstrak metadata stream (`width`, `height`, `fps`, `duration`, `codec`) melalui `ffprobe`.
- **FR-01.3:** Menangkap *keyframes* secara otomatis pada frame ke-0 dan setiap titik perpindahan adegan (*scene-change detection*) lengkap dengan `pts_time` presisi.
- **FR-01.4:** Menyediakan *baseline interval sampling* (default $1\text{ fps}$, dapat diubah) agar animasi mulus tanpa *hard-cut* tetap terekam.
- **FR-01.5:** Mengekstrak jalur audio bersih (`WAV 16kHz, Mono, PCM 16-bit`) sebagai input siap pakai untuk Google Flow STT.

### FR-02: Modul `flow-inference-bridge` (Pengganti 100% Cloud GPU HeyGen)
- **FR-02.1 (STT Alignment):** Mengonsumsi output transkripsi Google Flow STT ke dalam format standar `transcript_words.json` berisi `word`, `start_sec`, `end_sec`, dan `confidence`.
- **FR-02.2 (Asset Manifest):** Mengelola seluruh aset yang dihasilkan Google Flow (video B-roll, gambar *keyframe*, *voice-over*, SFX) dalam direktori proyek terstruktur (`/assets/flow/{video,images,audio}`) dengan pemetaan ID aset yang dapat direferensikan oleh kode HTML.
- **FR-02.3 (Beat-Sheet Generator):** Menggabungkan daftar *scene timestamps* (FR-01) dan *word-level timestamps* (FR-02.1) menjadi satu *master timeline* (`beat_sheet.json`) untuk memicu masuk/keluarnya elemen teks dan transisi.

### FR-03: Modul `local-style-sampler` (Pengganti `/style-sampling` Pro)
- **FR-03.1:** Mengekstrak *Design & Pacing Tokens* dari hasil inspeksi video/URL: palet warna (Hex), hierarki tipografi, skala *border-radius*, kepadatan *cut* rata-rata per detik, kurva *easing*, dan pola *camera movement*.
- **FR-03.2:** Menyimpan profil gaya ke dalam file JSON yang dapat dipakai ulang (`presets/<nama_gaya>.json`) tanpa batas jumlah preset.
- **FR-03.3:** Mampu menerapkan satu *style preset* ke skrip/brief baru sepenuhnya untuk memproduksi episode baru yang konsisten secara visual.

### FR-04: Compiler Komposisi & Registry Mapper (Render Adapter)
- **FR-04.1:** Membaca `evidence.json` + `beat_sheet.json` + `assets` lokal, lalu memetakan setiap adegan ke komponen terdekat di **HyperFrames Registry** (seperti *kinetic typography*, *overlay*, grafik, 3D, transisi).
- **FR-04.2:** Melakukan injeksi token warna, teks, durasi frame, dan path media lokal ke dalam file proyek HTML/CSS/JS yang valid terhadap skema HyperFrames Core.
- **FR-04.3:** Mengisolasi logika spesifik HyperFrames di dalam modul adapter sehingga struktur `evidence.json` tetap netral terhadap mesin render.

### FR-05: Closed-Loop Visual Parity QA
- **FR-05.1:** Merender 4–6 *still frames* pada *timestamps* kritis (pembukaan, puncak animasi, titik transisi, penutupan) menggunakan CLI lokal sebelum render video penuh.
- **FR-05.2:** Memeriksa cacat visual: teks terpotong (*overflow*), kontras teks terhadap latar belakang rendah, aset gagal muat (*broken path*), atau pergeseran layout.
- **FR-05.3:** Menjalankan siklus perbaikan otomatis maksimal 2 iterasi sebelum mengeksekusi render MP4 final bebas *watermark*.

---

## 5. Persyaratan Non-Fungsional (*Non-Functional Requirements*)

- **Kompatibilitas Windows 11:** Seluruh skrip PowerShell wajib memaksa `InvariantCulture` (mencegah error tanda koma desimal pada *locale* Indonesia), menulis seluruh JSON sebagai **UTF-8 tanpa BOM**, dan mendeteksi otomatis versi flag FFmpeg (`-fps_mode vfr` vs `-vsync vfr`).
- **Higienitas Workspace Antigravity:** Instalasi skill dibatasi seminimal mungkin (hanya 3 skill inti gratis + 1 skill kustom lokal) dengan aturan *trigger boundary* eksplisit agar tidak bentrok dengan alur kerja berbasis Remotion.
- **Kualitas Estetika (*Anti-Slop Guardrail*):** Setiap komposisi wajib mengikuti *design tokens* bersih (tipografi tajam, hierarki kontras jelas, *easing* natural) dan menghindari efek visual generik yang berlebihan.
- **Keamanan & Kepatuhan:** Seluruh proses replikasi berjalan secara *clean-room* di atas inti *open-source* Apache-2.0 tanpa memodifikasi, membobol, atau melewati *endpoint* berbayar HeyGen.

---

## 6. Kontrak Data Inti (*Core Data Contracts*)

Agar seluruh modul bekerja deterministik dan *engine-agnostic*, sistem menggunakan 3 skema JSON utama:

### 6.1 `inspect_manifest.json` (Output Layer 1)
Menyimpan metadata `ffprobe`, daftar `scene_keyframes` beserta `timestamp_sec` dan `frame_estimate`, daftar `interval_keyframes`, serta path file WAV siap kirim ke Google Flow STT.

### 6.2 `transcript_words.json` (Output Layer 2 — Google Flow STT)
```json
{
  "language": "id-ID",
  "duration_sec": 18.4,
  "words": [
    { "word": "Otomatisasi", "start_sec": 0.12, "end_sec": 0.78 },
    { "word": "workflow", "start_sec": 0.80, "end_sec": 1.25 }
  ]
}
```

### 6.3 `evidence.json` (Output Layer 3 — Epistemic Ledger)
```json
{
  "canvas": { "width": 1920, "height": 1080, "fps": 30, "duration_sec": 18.4 },
  "style_preset_ref": "presets/minimalist_saas_editorial.json",
  "scenes": [
    {
      "scene_id": "sc_01",
      "start_sec": 0.0,
      "end_sec": 3.2,
      "observed": {
        "bg_hex": "#F7F5F0",
        "primary_text_hex": "#111827",
        "layout_type": "centered_kinetic_headline"
      },
      "inferred": {
        "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
        "transition_out": "blur_zoom_cut"
      },
      "stt_trigger_words": ["Otomatisasi", "workflow"],
      "registry_component_hint": "kinetic-typography/split-reveal",
      "flow_media_ref": "assets/flow/video/broll_01.mp4"
    }
  ]
}
```

---

## 7. Manajemen Risiko & Mitigasi

| Risiko | Dampak | Mitigasi Teknis |
|---|---|---|
| **Template Fatigue (tampilan generik)** | Video terasa seperti template murahan | Wajib menimpa variabel CSS/token pada blok Registry dengan `STYLE_PRESET` lokal sebelum render. |
| **Perubahan Upstream HyperFrames** | Perintah CLI atau skema proyek berubah | Isolasi pemanggilan CLI di Layer 4 (*Render Adapter*); kunci versi paket (`package-lock.json`). |
| **Context Bloat di Antigravity** | Agent melambat atau salah pilih engine | Hanya pasang 3 skill gratis (`/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`) + aturan *explicit trigger*. |
| **Jitter / Flicker pada Render HTML** | Animasi patah saat dirender ke MP4 | Validasi mekanisme *virtual clock* saat Phase 0 (*White-Box Audit*) dan larang animasi berbasis `Date.now()` atau `requestAnimationFrame` tak terkunci. |

---

## 8. Batasan Ruang Lingkup (*Out of Scope untuk MVP*)
- Pembangunan GUI *timeline editor* berbasis web/desktop dari nol (MVP menggunakan CLI + preview bawaan HyperFrames Free).
- Pembuatan ulang model AI generatif lokal berbasis GPU (100% inferensi didelegasikan ke **Google Flow**).
- Integrasi langsung ke server/API berbayar HeyGen Pro.