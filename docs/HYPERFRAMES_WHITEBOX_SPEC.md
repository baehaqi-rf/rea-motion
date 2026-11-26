# HyperFrames White-Box Architecture & Audit Specification (Phase 0)

- **Audited Repository:** `heygen-com/hyperframes` (Apache-2.0 Open Source)
- **Target OS:** Windows 11 + PowerShell + Node.js v24 + FFmpeg 8.x
- **Audit Scope:** Composition Schema, Virtual Timeline Clock, Registry Structure, Free vs. Pro CLI Boundaries, and Motion Blur / Parity Verification.

---

## 1. Executive Discovery from White-Box Source Code Audit

Hasil audit langsung pada source code `packages/cli/src/commands/` di repositori `heygen-com/hyperframes` mengungkap fakta penting yang **jauh lebih menguntungkan** daripada asumsi awal di PRD:

### 1.1 Fakta Sebenarnya tentang Batas Free (Apache-2.0) vs. Pro ($25/bln)
Dalam PRD diasumsikan bahwa seluruh fitur `/reverse-any-video` perlu dibangun ulang dengan skrip `ffprobe` dasar karena dikunci di paket Pro. Hasil audit source code menunjukkan:
- **Yang dikunci oleh server HeyGen Pro HANYA 3 perintah pintu masuk/cloud:**
  1. `hyperframes reverse start` (`packages/cli/src/commands/reverse/start.ts` -> mencatat session ID ke server HeyGen dan memeriksa status langganan).
  2. `hyperframes templates pull <slug>` (`packages/cli/src/commands/templates.ts` -> mengunduh 5 template series dari server HeyGen).
  3. `hyperframes media-use generate` / `cloud render` (ketika memanggil model cloud HeyGen).
- **Seluruh 12 Sub-Perintah Computer Vision & Pengukuran (`hyperframes measure`) serta SSIM Visual Diff (`hyperframes diff`) adalah 100% LOKAL, GRATIS (Apache-2.0), dan TANPA AUTH:**
  - `npx hyperframes measure probe <video> [--normalize <out.mp4>]` — mendeteksi resolusi, FPS rasional (`30000/1001`), VFR, HDR, dan menormalisasi ke Constant Frame Rate (CFR) SDR.
  - `npx hyperframes measure cuts <video>` — deteksi *hard cut* berbasis selisih piksel *frame-to-frame* (jauh lebih akurat daripada `gt(scene,T)` FFmpeg biasa; memisahkan `cuts`, `not_cuts` seperti *light flash* / *whip pan*, dan `continues`).
  - `npx hyperframes measure events <video> --map` — mendeteksi setiap peristiwa visual & sinkronisasi hit audio.
  - `npx hyperframes measure frames <video> --range a,b --roi x,y,w,h` — ekstraksi strip frame berurutan pada titik transisi.
  - `npx hyperframes measure curve <video>` — mengestimasi kurva easing pergerakan elemen.
  - `npx hyperframes measure ink <video>` & `measure look <video>` — mengukur ukuran tipografi dari tinta piksel dan palet visual.
  - `npx hyperframes diff <original.mp4> <render.mp4>` — menghitung skor **SSIM** (`mean`, `p05`, `worst cell`), mendeteksi *missing content*, memeriksa kecocokan *cuts*, dan menghitung *audio offset* dalam milidetik!
  - `npx hyperframes beats <audio/video> --json` — deteksi *beat grid* audio secara lokal.
  - `npx hyperframes capture <url> --json` — ekstraksi *design tokens* (`tokens.json`, `design-styles.json`, font, screenshot, teks) langsung dari URL website aktif.

---

## 2. Kontrak Komposisi & Virtual Timeline Clock (`@hyperframes/core` & `@hyperframes/producer`)

### 2.1 Struktur DOM & Sub-Composition
1. **Root Document (`index.html`):**
   - Mendeklarasikan variabel re-brandable pada `<html data-composition-variables='[...]'>`.
   - Memiliki kontainer utama `<div id="root" data-composition-id="main" data-start="0" data-duration="12" data-width="1920" data-height="1080" data-motion-blur="on">`.
   - Memasang sub-komposisi per adegan dengan `data-composition-id="<scene_id>"` dan `data-composition-src="compositions/<scene_id>.html"`.
2. **Sub-Composition (`compositions/<scene_id>.html`):**
   - Seluruh `<style>`, `<div id="root" data-composition-id="<scene_id>">`, dan `<script>` **wajib dibungkus di dalam `<template>`**.
   - `data-composition-id` pada host di `index.html`, `#root` di file scene, dan key pada `window.__timelines["<scene_id>"]` **wajib 100% identik**.
3. **Kontrak Virtual Clock Deterministik:**
   - Setiap komposisi mendaftarkan **satu** timeline GSAP dalam kondisi paused:
     ```javascript
     const tl = gsap.timeline({ paused: true });
     // Gunakan tl.fromTo(...) BUKAN tl.from(...) agar seek-back deterministik
     window.__timelines["intro"] = tl;
     ```
   - **Dilarang keras:** `Date.now()`, `Math.random()` tanpa seed, `requestAnimationFrame` bebas, `setInterval`, `repeat: -1`, atau menganimasikan `display`/`visibility`/`autoAlpha` langsung pada elemen `.clip` (animasikan child di dalamnya).

### 2.2 Standar Kualitas Setara After Effects (AE-Grade Motion Craft)
- **Render-Time Motion Blur:** Tambahkan `data-motion-blur="on"` dan `data-motion-blur-shutter="360"` pada root komposisi untuk menghasilkan *directional motion blur* sejati pada elemen 2D/teks yang bergerak cepat.
- **Role-Based Easing:**
  - *Arrivals (Masuk):* Long-tail ease-out (`expo.out` atau `power4.out`), durasi `0.3s–0.6s`.
  - *Camera Moves / Color Floods:* Symmetrical ease (`power2.inOut`).
  - *Exits / Zoom-Through:* Accelerating ease (`power3.in`), durasi 40–50% lebih singkat dari entrance.
- **Overlap & Stagger:** Elemen berikutnya mulai saat elemen sebelumnya selesai 30–50% (hindari animasi berurutan kaku atau serentak bersamaan). Stagger per huruf `1 frame (0.033s)`, per kata `60–120ms`.
- **Dead-Still Landed Titles:** Setelah judul mendarat, tahan **100% diam** selama waktu baca (`0.5s + 0.3s per kata`), pindahkan gerakan ke kamera atau objek latar.
- **Anti-Banding H.264:** Hindari linear gradient gelap satu layar penuh; gunakan radial gradient + film grain (`grain-overlay` atau `npx hyperframes media-treatment`).

---

## 3. Arsitektur Registry Lokal (456 Item Apache-2.0)

Repositori `upstream/hyperframes-upstream/registry/` menyediakan **456 aset kode sumber terbuka**:
- **8 Full Examples** (`kinetic-type`, `product-promo`, `swiss-grid`, `vignelli`, `warm-grain`, `nyt-graph`, `play-mode`, `decision-tree`)
- **211 Scene Blocks** (`registry/blocks/<name>/`) — adegan utuh dengan timeline sendiri, dipasang ke `compositions/<name>.html`.
- **237 Motion Components** (`registry/components/<name>/`) — primitif animasi, caption skin, gerakan kamera, dan efek shader/tekstur yang dapat disisipkan ke dalam adegan mana pun.
- **Offline Copy Capability:** Selain `npx hyperframes add <name>`, seluruh blok dapat disalin secara *offline* langsung dari `upstream/hyperframes-upstream/registry/` tanpa koneksi jaringan.
