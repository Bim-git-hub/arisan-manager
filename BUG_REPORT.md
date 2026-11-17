# Laporan Bug: Arisan Manager v1.0

Dokumen ini mencatat 4 bug yang ditemukan pada versi 1.0 dan cara masing-masing diperbaiki di versi 2.0.
Setiap bug punya uji otomatis di `test_bugs.py` (gagal di v1, lolos di v2).

| ID | Judul | Tingkat | Uji otomatis |
|----|-------|---------|--------------|
| BUG-01 | Pemenang yang sama bisa terpilih berkali-kali | Tinggi | `test_bug01_pemenang_tidak_berulang` |
| BUG-02 | Iuran nol atau negatif diterima | Sedang | `test_bug02_iuran_nol_atau_negatif_ditolak` |
| BUG-03 | Nama anggota bisa menyisipkan HTML atau skrip (XSS) | Tinggi | `test_bug03_nama_html_di_escape` |
| BUG-04 | Undian tanpa kandidat membuat server error 500 | Sedang | `test_bug04_undi_tanpa_anggota_tidak_crash` |

---

## BUG-01: Pemenang yang sama bisa terpilih berkali-kali

- **Tingkat:** Tinggi (aturan inti arisan tidak berlaku)
- **Lokasi:** `v1/app.py`, fungsi `undi()`
- **Langkah mereproduksi:**
  1. Tambahkan satu anggota, misalnya "Ani".
  2. Tekan **Undi pemenang** dua kali.
- **Hasil yang diharapkan:** Ani hanya menang sekali. Undian kedua ditolak karena tidak ada kandidat.
- **Hasil sebenarnya:** Ani menang di ronde 1 dan ronde 2.
- **Penyebab:** `kandidat = data["anggota"]` memakai seluruh anggota tanpa menyaring yang sudah menang.
- **Perbaikan v2:** `kandidat = [a for a in data["anggota"] if not a["menang"]]`

## BUG-02: Iuran nol atau negatif diterima

- **Tingkat:** Sedang (data keuangan menjadi tidak masuk akal)
- **Lokasi:** `v1/app.py`, fungsi `atur_iuran()`
- **Langkah mereproduksi:**
  1. Isi **Nominal baru** dengan `-50000`, tekan **Simpan iuran**.
  2. Tandai satu anggota sudah bayar, lihat **Kas ronde ini**.
- **Hasil yang diharapkan:** Ditolak dengan pesan bahwa nominal harus lebih dari 0.
- **Hasil sebenarnya:** Tersimpan, kas ronde menjadi negatif.
- **Penyebab:** Input hanya dikonversi ke `int`, tanda dan batas nilainya tidak diperiksa.
- **Perbaikan v2:** Ditambahkan pemeriksaan `if nominal <= 0` yang menolak input dengan pesan jelas.

## BUG-03: Nama anggota bisa menyisipkan HTML atau skrip (XSS)

- **Tingkat:** Tinggi (celah keamanan)
- **Lokasi:** `v1/templates/index.html`, dua tempat: daftar anggota dan riwayat pemenang
- **Langkah mereproduksi:**
  1. Tambahkan anggota bernama `<script>alert(1)</script>`.
  2. Buka kembali halaman beranda.
- **Hasil yang diharapkan:** Nama tampil sebagai teks apa adanya.
- **Hasil sebenarnya:** Skrip dieksekusi browser (kotak peringatan muncul).
- **Penyebab:** Template memakai filter `safe` pada nama, yang mematikan escape otomatis Jinja2.
- **Perbaikan v2:** Filter `safe` dihapus, sehingga `<` dan `>` ditampilkan sebagai `&lt;` dan `&gt;`.

## BUG-04: Undian tanpa kandidat membuat server error 500

- **Tingkat:** Sedang (aplikasi crash oleh aksi pengguna biasa)
- **Lokasi:** `v1/app.py`, fungsi `undi()`
- **Langkah mereproduksi:**
  1. Mulai dengan data kosong (hapus `data.json` bila ada).
  2. Tekan **Undi pemenang** tanpa menambah anggota.
- **Hasil yang diharapkan:** Pesan yang menjelaskan bahwa belum ada anggota.
- **Hasil sebenarnya:** Halaman "Internal Server Error" (HTTP 500).
- **Penyebab:** `random.choice([])` melempar `IndexError` dan tidak ada pemeriksaan sebelumnya.
- **Perbaikan v2:** Jika kandidat kosong, tampilkan pesan yang membedakan "belum ada anggota" dan "semua anggota sudah menang".

---

## Catatan batasan yang belum diperbaiki (bahan pengembangan)

Hal-hal ini sengaja tidak dihitung sebagai bug pada skenario, tapi bisa dikembangkan:

- Nama anggota ganda diperbolehkan.
- Tidak ada perlindungan CSRF pada formulir.
- Data disimpan di satu file JSON tanpa penguncian, jadi tidak aman untuk banyak pengguna bersamaan.
- Undian tidak mensyaratkan anggota sudah bayar.
