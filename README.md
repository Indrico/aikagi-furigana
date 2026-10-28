# Aikagi Furigana

Tombol **Furigana: OFF / ON** untuk teks Jepang di Aikagi (Artemis Engine).
Tombol berada di kiri bawah kotak dialog. Pilihan disimpan melalui konfigurasi
game; keadaan awal OFF. Furigana ditambahkan ketika dialog, nama pembicara, dan
teks dialog backlog digambar.

## Instalasi Windows

1. Tutup game dan pasang **Python 3.12 64-bit** dari [python.org](https://www.python.org/downloads/windows/).
2. Unduh ZIP dari [GitHub Releases](https://github.com/Indrico/aikagi-furigana/releases).
3. Ekstrak folder `aikagi-furigana` ke dalam folder yang berisi `Aikagi_en.exe`.
   Seluruh isinya juga boleh langsung diletakkan di folder game.
4. Jalankan `Install-Furigana.cmd`. Instalasi pertama memerlukan internet untuk
   dependensi Python dan dapat berlangsung beberapa menit.
5. Jalankan game melalui Steam, pilih bahasa **Japanese**, lalu coba tombolnya
   saat dialog tampil.

Installer mendeteksi lokasi game dari lokasi berkasnya, termasuk nama folder
yang memakai spasi. Tidak perlu mengubah path `D:\SteamLibrary` atau folder kerja
PowerShell. Lokasi lain dapat diberikan secara eksplisit:

```powershell
.\Install-Furigana.cmd -GameDirectory "D:\SteamLibrary\steamapps\common\Aikagi"
```

Release berisi source dan installer. Patch dibuat **secara lokal** dari salinan
game pengguna; executable, arsip, font, dan naskah game tidak disertakan dalam
repo maupun ZIP. Virtual environment disimpan di `.venv`, dan hasil build di
`.build/furigana`.

## Pemulihan

Tutup game lalu jalankan `Restore-Furigana.cmd`. Arsip asli dicadangkan sebagai
`Aikagi_en.pfs.before-furigana`. Save data tidak diubah. Jangan hapus folder
`.build` sebelum memulihkan patch. Installer menolak arsip versi lain dan backup
yang berbeda.

Jika patch sebelumnya sudah terpasang, builder dapat menggunakan backup asli
tersebut. Jika arsip asli sudah tertimpa dan backup tidak tersedia, pulihkan
berkas game melalui Steam sebelum membangun patch.

## Cakupan dan status

- Build referensi mencakup **3.505 blok dialog Jepang** dan **10.692 ruby spans**.
- Okurigana tetap terpisah. Gabungan seperti 部屋（へや） dan 汐栞（しおり）
  memakai ruby kelompok. Kana biasa tidak diberi anotasi tambahan.
- Pembacaan otomatis menggunakan MeCab/UniDic; koreksi nama dan kata ada di
  `mod/readings.json`. Kata ambigu masih dapat dibaca keliru.
- Dukungan arsip asli: SHA-256
  `45a744e4b22e4248b8af545340dfccd6cca0275dbef9b6c3279a08ef28016b24`.
- Hanya dua entri Lua yang diganti. Semua 117 entri hasil repack diverifikasi;
  executable dan arsip `.pfs.000` sampai `.pfs.002` tidak diganti.
- Perbaikan direktori installer telah dikonfirmasi pengguna. Pengujian Lua,
  integritas arsip, dan installer PowerShell telah lulus di Linux.
- **Tampilan furigana dan save/load dalam game Steam belum diverifikasi oleh
  pengembang.** Ini rilis awal untuk pengujian.

## Build manual

```sh
python -m venv .venv
# Windows: .venv\Scripts\python.exe
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python tools/build_furigana.py --game /path/to/Aikagi --output .build/furigana
.venv/bin/python tools/manage_patch.py install --game /path/to/Aikagi --package .build/furigana
```

Gunakan aksi `restore` sebagai pengganti `install` untuk memulihkan arsip asli.

## Pengujian

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Pengujian integrasi memerlukan salinan game sendiri. Berikan lokasi melalui
`AIKAGI_GAME_DIRECTORY` dan `AIKAGI_PATCH_DIRECTORY`; tes tersebut dilewati jika
berkasnya tidak tersedia. Tes installer memerlukan `pwsh`.

## Cara kerja dan referensi

Builder membaca arsip PF8, menghasilkan tabel pembacaan Jepang, dan memasang
helper Lua pada renderer serta dispatcher tombol bawaan. Skenario dan backlog
tetap menyimpan teks asli. Repack memperbarui offset, ukuran, SHA-1 indeks, dan
enkripsi payload.

Investigasi awal memakai [REA](https://github.com/morluto/rea) untuk metadata PE.
Format PF8 diperiksa terhadap [implementasi GARbro](https://github.com/morkt/GARbro/blob/master/ArcFormats/Artemis/ArcPFS.cs),
dan sintaks ruby diperiksa terhadap [implementasi Artemis terbuka](https://github.com/Alphaly2K/art3m1s-core).
