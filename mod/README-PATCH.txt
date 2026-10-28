FURIGANA TOGGLE — AIKAGI / ARTEMIS

Ini patch awal. Pengujian Lua dan integritas arsip lulus (11 tes).
Tampilan di game belum terverifikasi: lingkungan pengujian tidak memiliki
klien Steam yang diperlukan executable asli.

PAKET HASIL BUILD LOKAL
Paket ini dibuat dari berkas game pengguna, bukan untuk disertakan dalam release.
Untuk source release publik, ikuti README.md dan installer di folder utama.

WINDOWS
1. Tutup game.
2. Ekstrak seluruh isi folder furigana_patch ke folder yang berisi Aikagi_en.exe.
   Boleh juga membiarkannya sebagai subfolder furigana_patch di folder game.
   Sertakan folder payload, pc, dan build-report.json; jangan salin file .ps1 saja.
3. Jalankan Install-Furigana.cmd.
4. Buka game melalui Steam, pilih bahasa Japanese, lalu mulai/lanjutkan cerita.
5. Klik "Furigana: OFF / ON" di kiri bawah kotak dialog.

Untuk lokasi game lain, buka PowerShell dan jalankan:
  .\Install-Furigana.ps1 -GameDirectory "C:\lokasi\Aikagi"

PEMULIHAN
Tutup game dan jalankan Restore-Furigana.cmd.
Arsip asli disimpan sebagai Aikagi_en.pfs.before-furigana.
Save data tidak diubah. Installer menolak versi arsip yang berbeda.
Folder game dideteksi dari lokasi installer, bukan folder kerja PowerShell.
File patch ada di payload agar ekstraksi tidak menimpa arsip game asli.
Installer diperiksa dengan PowerShell di Linux; belum dijalankan di Windows.

CATATAN
Furigana mengikuti kata/okurigana; gabungan kanji tertentu memakai ruby kelompok.
Nama tokoh memiliki koreksi khusus. Pembacaan otomatis masih dapat keliru.
Periksa posisi tombol, jarak antarbaris, backlog, dan save/load di game.
Keadaan awal OFF; pilihan disimpan melalui konfigurasi game.
