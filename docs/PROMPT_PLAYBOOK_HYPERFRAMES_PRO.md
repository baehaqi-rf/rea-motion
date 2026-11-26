# Master Prompting Playbook — HyperFrames Pro v2.0 (REA × Brain Autopilot × Google Flow)

Panduan dan kumpulan prompt efektif siap pakai (*copy-paste*) untuk memproduksi berbagai jenis video motion graphics sekelas studio **After Effects & Cinema 4D** di Antigravity.

---

## 1. Anatomi Prompt Efektif (Formula 5-Elemen)

Agar agent langsung mengaktifkan seluruh pipeline **HyperFrames Pro v2.0 (`GSAP 3.15 + Three.js + REA + Brain Autopilot + Google Flow`)** tanpa hasil generik (*AI Slop*), sertakan 5 elemen kunci berikut:

1. **Trigger Engine:** Sebutkan **`gunakan local-hyperframes-pro`** (atau `hyperframes`).
2. **Format & Durasi:** Resolusi (`1920x1080` lanskap atau `1080x1920` vertikal Reels/TikTok), FPS (`30fps` atau `60fps`), dan durasi (`15s`, `30s`, dsb.).
3. **Style Preset / Referensi Visual:** Pilih dari preset (`minimalist_saas`, `editorial_explainer`, `aslaniedits_kinetic_editorial`, `calm_3d_editorial`), atau berikan **file video referensi (`.mp4`)** / **URL website aktif**.
4. **Teknologi Animasi & 3D:** Sebutkan elemen spesifik bila diinginkan: **GSAP 360° Shutter Motion Blur**, **Three.js 3D WebGL / Path-Tracing**, atau **Google Flow Omni 1.2 Flash B-Roll / STT**.
5. **Quality Gate:** Minta **"verifikasi dengan Brain Autopilot & render ke MP4 tanpa stop"**.

---

## 2. Kumpulan Prompt Siap Pakai per Kondisi / Kebutuhan

### Kondisi A: Video Lirik Lagu / Kinetic Music Video (Beat-Synced After Effects Style)
**Karakteristik:** Menggunakan analisis struktur musik (`npx hyperframes audio <track> --only sections,onsets,moments --json` & `beats`) + STT kata-demi-kata untuk mengeksekusi tipografi kinetik yang terkunci tepat pada ketukan *beat* dan perubahan *section* (verse vs. chorus).

> **Prompt Copy-Paste:**
> ```text
> Gunakan local-hyperframes-pro untuk membuat video lirik lagu motion graphics kelas After Effects dari file audio @[path/ke/lagu.mp3] (durasi 30 detik, 1920x1080, 30fps).
> 
> Instruksi eksekusi:
> 1. Analisa beat, onset, dan section lagu dengan `hyperframes audio` / `hyperframes beats` serta ekstrak timestamp lirik per kata (STT).
> 2. Gunakan tipografi kinetik GSAP dengan `data-motion-blur="on"` (shutter 360°):
>    - Verse: per-word blur reveal (`blur(10px) -> 0`, `power4.out`) di atas stage atmosferik dengan elemen 3D Three.js yang bergerak lambat mengikuti `hf-seek`.
>    - Chorus: tingkatkan kepadatan cut tepat di ketukan beat, gunakan blok registry `kinetic-center-build`, `slot-machine-roll`, dan `whip-pan-cut` dengan aksen warna kontras tinggi pada kata kunci utama.
> 3. Jangan tampilkan lirik seperti subtitle biasa—jadikan tipografi sebagai hero visual di layar, tahan dead-still saat dibaca, dan tambahkan `grain-overlay` 35mm.
> 4. Jalankan verifikasi tertutup dengan Brain Autopilot (`Run-BrainAutopilotVerify.ps1`) hingga 0 error, lalu render final ke MP4.
> ```

---

### Kondisi B: Video Iklan SaaS / Product Launch (Apple / Linear Style)
**Karakteristik:** Mengambil *design tokens* dan UI asli dari URL website atau screenshot produk (`npx hyperframes capture <url>`), lalu menampilkan alur *Establish Workspace → Isolate Action (1.8x Zoom) → Morph Container → Return Result → End Card Lockup*.

> **Prompt Copy-Paste:**
> ```text
> Gunakan local-hyperframes-pro dengan preset `minimalist_saas` untuk membuat video iklan peluncuran produk SaaS berdurasi 25 detik (1920x1080, 30fps) untuk website [https://url-produk-anda.com] (atau dari screenshot @[path/ke/ui.png]).
> 
> Instruksi eksekusi:
> 1. Jalankan `npx hyperframes capture` pada URL untuk mengekstrak palet warna asli, font, logo, dan komponen UI nyata (jangan mengarang dashboard palsu).
> 2. Struktur cerita 5-babak:
>    - [0-4s] Hook: Kinetic headline masalah utama (`per-word-rise` + `expo.out`).
>    - [4-11s] Establish & Isolate: Tampilkan UI produk di `browser-device-stage`, gerakkan kursor besar (`agent-cursor`) klik tombol utama, lalu camera punch-in 1.8x dengan motion blur 360° saat data/chart beranimasi.
>    - [11-18s] Morph & Payoff: Gunakan transisi `zoom-through-transition` ke fitur unggulan kedua dengan kartu metrik real-time (`count-up`) dan objek aksen 3D Three.js.
>    - [18-25s] End Card: Animasi logo lockup di tengah + tombol CTA yang ditahan tajam selama 2 detik terakhir.
> 3. Verifikasi setiap beat dengan Brain Autopilot (`WebGL3DEngine`, 0 console/network/layout error) dan render MP4 kualitas `delivery`.
> ```

---

### Kondisi C: Reels / TikTok / Shorts High-Retention (`@aslaniedits` Rotoscoped 9:16)
**Karakteristik:** Format vertikal `1080x1920`, patuh *TikTok/Reels Safe Zone* (`288–1248px` vertikal, `120–888px` horizontal), menggunakan teknik **Subject Sandwich (3 Z-Layers)**: latar studio → teks raksasa + objek 3D di *belakang* bahu presenter → cutout presenter (`hyperframes remove-background`) di tengah → kartu glassmorphic di *depan*.

> **Prompt Copy-Paste:**
> ```text
> Gunakan local-hyperframes-pro dengan preset `aslaniedits_kinetic_editorial` untuk membuat video vertikal Reels/TikTok (1080x1920, 30fps, durasi 18 detik) dari rekaman pembicara @[path/ke/footage.mp4] (atau topik: "[Topik Anda]").
> 
> Instruksi eksekusi:
> 1. Jalankan `npx hyperframes remove-background` pada footage pembicara untuk menghasilkan layer cutout transparan (VP9 alpha), lalu susun Z-depth "Subject Sandwich":
>    - Layer Z0: Cyclorama gelap `#121214` dengan radial glow & grid tipis.
>    - Layer Z1 (di belakang kepala/bahu): Giant condensed headline Oswald (`#CCFF00` Electric Lime) + objek 3D Three.js yang berputar halus.
>    - Layer Z2 (tengah): Cutout pembicara.
>    - Layer Z3 (depan): Kartu glassmorphic (`vfx-liquid-glass`), anotasi vektor, dan `caption-kinetic-slam` di dalam safe-zone vertikal (`--safe-zone reels`).
> 2. Gunakan `back.out(1.4)` overshoot dan snap-zoom `1.0x -> 1.08x` pada setiap penekanan kata kunci STT.
> 3. Pastikan Frame 0 langsung menampilkan hook visual penuh (tanpa fade-in hitam), audit dengan Brain Autopilot, dan render ke MP4.
> ```

---

### Kondisi D: Replikasi 1:1 Gaya Video Referensi (REA Reverse Video + Remake Topik Baru)
**Karakteristik:** Membedah video referensi (`.mp4`) secara *frame-by-frame* menggunakan `Invoke-ReaVideoInspect.ps1` + `hyperframes measure (probe, cuts, curve, look)` + `Build-BeatSheet.mjs`, lalu membangun ulang komposisinya dengan topik/brand Anda sendiri dan menguji kemiripannya dengan `hyperframes diff`.

> **Prompt Copy-Paste:**
> ```text
> Gunakan local-hyperframes-pro untuk mereplikasi 1:1 ritme editing, kurva gerakan, palet visual, dan transisi dari video referensi @[path/ke/referensi.mp4], lalu terapkan ke topik/brand baru saya: "[Jelaskan Topik / Brand Baru Anda]".
> 
> Instruksi eksekusi:
> 1. Jalankan `Invoke-ReaVideoInspect.ps1` serta `npx hyperframes measure probe`, `measure cuts`, `measure curve`, dan `measure look` pada video referensi.
> 2. Susun `evidence.json` (pisahkan `observed` vs `inferred`) dan simpan profil gayanya ke `presets/custom_ref_style.json`.
> 3. Bangun komposisi HTML/GSAP/Three.js yang merekonstruksi setiap shot, timing cut (presisi frame ÷ fps), easing, dan tipografi dari referensi.
> 4. Jalankan `Run-ParityCheck.ps1` (`hyperframes snapshot --against`) dan `Run-BrainAutopilotVerify.ps1` untuk memverifikasi paritas visual sebelum merender MP4 final.
> ```

---

### Kondisi E: Video Explainer Dokumenter / Data Storytelling (Vox / Kurzgesagt Style)
**Karakteristik:** Mengubah topik/data kompleks menjadi satu diagram/mesin visual yang tumbuh bertahap (*One Diagram That Grows*) dengan transisi *continuous transformation* (grafik berubah menjadi peta/populasi tanpa hard cut yang memutus alur).

> **Prompt Copy-Paste:**
> ```text
> Gunakan local-hyperframes-pro dengan preset `editorial_explainer` untuk membuat video explainer dokumenter berdurasi 30 detik (1920x1080, 30fps) tentang: "[Topik / Data yang Ingin Dijelaskan]".
> 
> Instruksi eksekusi:
> 1. Gunakan tekstur kertas editorial (`#F2EFE9`), tipografi `Playfair Display` + `IBM Plex Mono`, serta komponen registry `paper-collage-reveal`, `pan-stations`, `vox-annotate`, `hw-callout-circle`, dan `data-chart`.
> 2. Terapkan prinsip "One Diagram That Grows": mulai dari satu pertanyaan konkret, lalu kamera melakukan pan/zoom di atas satu kanvas besar (`pan-stations`) sambil memunculkan anotasi garis dan angka tepat saat narasi menyebutkannya.
> 3. Gunakan Google Flow untuk menghasilkan voice-over narasi & aset ilustrasi pendukung, sinkronkan ke `beat_sheet.json`, verifikasi via Brain Autopilot, dan render MP4 final.
> ```

---

### Kondisi F: Hybrid 3D Cinema & AI VFX (HyperFrames 3D + Google Flow Omni 1.2 Flash Sandwich)
**Karakteristik:** Menggabungkan ketajaman tipografi & 3D WebGL/Path-Tracing di HyperFrames dengan *Start-to-End Frame Interpolation* sinematik dari **Google Flow (Gemini Omni 1.2 Flash)**.

> **Prompt Copy-Paste:**
> ```text
> Gunakan local-hyperframes-pro dan google-flow-motion-director (mode Hybrid Sandwich Reveal) untuk membuat bumper/trailer sinematik 3D berdurasi 15 detik (1920x1080, 30fps) untuk brand "[Nama Brand]".
> 
> Instruksi eksekusi:
> 1. Render anchor frame deterministik (`reveal_start.png` dan `reveal_end.png`) menggunakan HyperFrames (`npx hyperframes snapshot`) dengan tipografi brand yang tajam dan objek 3D Three.js.
> 2. Gunakan Google Flow (`Frames` mode di browser internal Antigravity) untuk menginterpolasi transisi VFX 3D sinematik di antara kedua anchor frame tersebut, lalu simpan klip MP4-nya ke `assets/flow/video/`.
> 3. Lakukan seamless handoff di komposisi HyperFrames: putar klip Google Flow hingga frame handoff, lalu sambung mulus ke komposisi live GSAP + Three.js untuk animasi UI/tipografi interaktif dan end-card.
> 4. Audit seam handoff dengan Brain Autopilot & `hyperframes snapshot`, lalu render MP4 final.
> ```
