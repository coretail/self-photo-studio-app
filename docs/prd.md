# PRD: Self-Photo Studio Selection Kiosk App

**Repo:** github.com/coretail/self-photo-studio-app
**Status:** Draft v1
**Terakhir diupdate:** 25 Agustus 2026

---

## 1. Problem Statement

Proses pemilihan foto dan frame secara manual sering bikin antrean menumpuk, rawan salah cetak, dan menyita waktu operator studio.

## 2. Product Objective

Menyediakan aplikasi self-service kiosk (berbasis web app) agar klien bisa input data sesi, memilih frame, memilih foto, mengatur posisi foto dalam frame, dan menghasilkan file cetak siap pakai secara mandiri — tanpa perlu bantuan operator di setiap langkah.

**MVP scope:** dijalankan di PC studio (browser kiosk mode), pembayaran masih manual, output berupa file JPEG hi-res (belum ada auto-print).

**Arahan arsitektur:** dibangun sebagai web app (bukan native desktop app), supaya di fase berikutnya bisa diakses langsung dari HP klien tanpa rewrite besar.

## 3. User Flow

1. **Landing/Start** — Klien scan QR code atau input Session ID foto mereka.
2. **Pilih Frame** — Klien memilih layout/template frame yang diinginkan (contoh: Strip, 4R, Polaroid).
3. **Pilih Foto** — Klien memilih foto dari gallery hasil foto sesuai kuota slot frame.
4. **Preview & Adjust** — Sistem memasukkan foto ke dalam frame. Klien bisa atur posisi (crop/drag/zoom).
5. **Confirmation/Finish** — Klien konfirmasi hasil akhir → sistem generate file JPEG hi-res dan menyimpannya ke folder lokal dengan reference/order ID, untuk dicocokkan admin secara manual dengan pembayaran dan dicetak.

## 4. Key Features & Requirements

### 4.1 Session Integration
- System membaca foto berdasarkan ID sesi/folder klien.
- Auto-reset session jika layar idle selama 3–5 menit tanpa aktivitas (dengan warning konfirmasi sebelum reset benar-benar terjadi, agar progress yang belum disimpan tidak hilang tiba-tiba).
- Session ID/QR sebaiknya punya masa berlaku (expiry) untuk mencegah akses ke folder foto klien lain.

### 4.2 Frame Selection & Rules
- Katalog pilihan template frame (Strip, 4R, Polaroid, dst).
- System mengunci (lock) batas maksimum/minimum foto yang wajib dipilih berdasarkan template frame yang aktif.
- Jika jumlah foto tersedia di sesi kurang dari minimum slot frame, sistem menampilkan pesan yang jelas (arahkan klien ke operator).

### 4.3 Photo Picker & Preview
- Grid tampilan gallery foto klien yang responsif.
- Real-time canvas preview yang menampilkan foto langsung terpasang di template frame.
- Fitur interaksi dasar pada canvas: reposition/drag dan zoom posisi foto di dalam frame slot.
- Guide crop otomatis saat rasio foto berbeda jauh dari rasio slot frame.

### 4.4 Output & Handoff ke Admin
- Generate file final cetak beresolusi tinggi (JPEG, 300 DPI) sesuai dimensi fisik template frame yang dipilih (Strip, 4R, Polaroid punya ukuran cetak berbeda — perlu dipetakan ke pixel dimension masing-masing).
- File disimpan ke folder lokal PC studio dengan naming convention yang jelas: `{session-id}_{order-id}_{timestamp}.jpg`.
- Setiap sesi menghasilkan **order ID/reference number** yang ditampilkan di layar akhir, untuk dicocokkan admin secara manual dengan pembayaran (payment masih manual di MVP ini).
- Tidak ada integrasi auto-print di MVP — pencetakan dilakukan manual oleh admin dari file yang tersimpan.

### 4.5 Data Retention
- Foto hasil sesi dan file JPEG hasil generate disimpan selama **30 hari**, lalu otomatis dihapus (scheduled cleanup/cron job di PC studio).

## 5. Technical Stack

- **Backend:** FastAPI (Python) — menangani session handling, frame/photo metadata, generate file JPEG hi-res, dan penyimpanan order/reference ID.
- **Database:** SQLite (file-based, lokal) — cukup untuk skala satu PC studio di MVP. Menyimpan metadata saja (session ID, order ID, path file, status, timestamp); foto asli dan file JPEG hasil generate tetap disimpan sebagai file di filesystem lokal, bukan di database.
- **Frontend:** Web app (browser-based), dijalankan dalam mode kiosk di PC studio. Interaksi canvas (drag/zoom foto dalam frame) sebaiknya ditangani sepenuhnya di sisi client (misal dengan Fabric.js atau Konva.js) agar render preview real-time tercapai tanpa round-trip ke server, sesuai target performa <1 detik.
- **Alasan pemilihan:** arsitektur ini selaras dengan arahan Fase 2 (akses dari HP klien) — backend FastAPI + database lokal bisa langsung diakses lewat jaringan tanpa rewrite besar, tinggal expose ke WiFi lokal studio atau URL publik.
- **Catatan migrasi ke depan:** jika Fase 2 melibatkan banyak kiosk/device yang mengakses satu server pusat secara bersamaan, SQLite sebaiknya dievaluasi ulang dan dipertimbangkan upgrade ke PostgreSQL untuk menghindari isu concurrency.

## 6. Non-Functional Requirements

- **UI/UX:** Desain clean, responsif untuk layar sentuh (PC/tablet kiosk mode di MVP; harus tetap mobile-friendly untuk kesiapan Fase 2 akses HP klien). Tombol besar dan mudah ditekan.
- **Performance:** Render preview cepat (< 1 detik setelah foto dipilih) agar tidak lag.
- **Platform:** Web app berbasis browser, dijalankan dalam mode kiosk di PC studio pada MVP.

## 7. Roadmap / Phase 2 (Out of Scope untuk MVP ini)

- Akses aplikasi langsung dari HP klien (via WiFi lokal studio atau URL publik), tanpa perlu berada di PC studio.
- Integrasi payment gateway (menggantikan proses payment manual).
- Integrasi auto-print / print queue system ke mesin cetak.
- Dashboard admin untuk monitoring antrean, retry, dan pencocokan order-payment secara otomatis.
- Dukungan multi-kiosk berjalan bersamaan (penanganan collision file name / race condition saat generate file jika lebih dari satu PC aktif ke folder yang sama).

## 8. Open Questions

- Apakah harga per frame ditampilkan di aplikasi, atau tetap dijelaskan manual oleh operator?
- Apakah satu sesi klien boleh menghasilkan lebih dari satu frame/output (misal Strip + Polaroid sekaligus)? Jika ya, bagaimana alur order ID-nya (satu ID gabungan atau per frame)?
- Selain drag & zoom, apakah dibutuhkan fitur rotate atau undo/redo di canvas untuk interaksi touch?
- Bagaimana penanganan error state: gallery gagal load, atau proses generate file JPEG gagal di tengah jalan?

## 9. Success Metrics (belum ditentukan)

- Rata-rata waktu penyelesaian per klien (dari scan QR sampai konfirmasi akhir).
- Error rate saat generate file cetak.
- Tingkat pengurangan waktu operator dibanding proses manual sebelumnya.