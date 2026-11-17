"""Arisan Manager v2.0

Semua bug dari versi 1.0 sudah diperbaiki. Ringkasan perubahan bisa dilihat di
halaman /changelog dan di BUG_REPORT.md.

Jalankan:  python app.py   lalu buka http://127.0.0.1:5002
"""
import json
import os
import random

from flask import Flask, abort, flash, redirect, render_template, request, url_for

VERSI = "2.0"

# Isi halaman /changelog. Potongan kode di bawah sama persis dengan kode di v1 dan v2.
PERUBAHAN = [
    {
        "kode": "BUG-01",
        "judul": "Pemenang yang sama bisa terpilih berkali-kali",
        "tingkat": "Tinggi",
        "gejala": "Setelah Ani menang di ronde 1, Ani masih bisa menang lagi di ronde berikutnya. "
                  "Aturan inti arisan (setiap anggota menang satu kali) tidak berlaku.",
        "penyebab": "Undian memilih dari seluruh daftar anggota tanpa menyaring yang sudah menang.",
        "perbaikan": "Kandidat undian hanya anggota yang belum pernah menang.",
        "sebelum": 'kandidat = data["anggota"]',
        "sesudah": 'kandidat = [a for a in data["anggota"] if not a["menang"]]',
        "uji": "test_bug01_pemenang_tidak_berulang",
    },
    {
        "kode": "BUG-02",
        "judul": "Iuran nol atau negatif diterima",
        "tingkat": "Sedang",
        "gejala": "Mengisi iuran dengan -50000 tersimpan begitu saja, sehingga kas ronde menjadi negatif.",
        "penyebab": "Input hanya diubah menjadi angka bulat, tanda dan batas nilainya tidak diperiksa.",
        "perbaikan": "Nominal harus lebih dari 0. Nilai lain ditolak dengan pesan yang menjelaskan alasannya.",
        "sebelum": 'data["iuran"] = nominal',
        "sesudah": 'if nominal <= 0:\n'
                   '    flash("Nominal iuran harus lebih dari 0.", "error")\n'
                   '    return redirect(url_for("beranda"))\n'
                   'data["iuran"] = nominal',
        "uji": "test_bug02_iuran_nol_atau_negatif_ditolak",
    },
    {
        "kode": "BUG-03",
        "judul": "Nama anggota bisa menyisipkan HTML atau skrip (XSS)",
        "tingkat": "Tinggi",
        "gejala": "Anggota bernama <script>alert(1)</script> membuat skrip berjalan di browser setiap "
                  "orang yang membuka halaman.",
        "penyebab": "Template menampilkan nama dengan filter safe, sehingga escape otomatis Jinja2 dimatikan.",
        "perbaikan": "Filter safe dihapus. Nama tampil sebagai teks biasa, tanda kurung sudut diubah menjadi entitas HTML.",
        "sebelum": "{{ a.nama|safe }}",
        "sesudah": "{{ a.nama }}",
        "uji": "test_bug03_nama_html_di_escape",
    },
    {
        "kode": "BUG-04",
        "judul": "Undian tanpa kandidat membuat server error 500",
        "tingkat": "Sedang",
        "gejala": "Menekan Undi pemenang saat daftar anggota masih kosong menampilkan halaman Internal Server Error.",
        "penyebab": "random.choice dipanggil pada daftar kosong dan melempar IndexError.",
        "perbaikan": "Kandidat diperiksa dulu. Jika kosong, pengguna mendapat pesan yang menjelaskan keadaannya "
                     "(belum ada anggota, atau semua sudah menang).",
        "sebelum": "pemenang = random.choice(kandidat)",
        "sesudah": 'if not kandidat:\n'
                   '    flash("...", "error")\n'
                   '    return redirect(url_for("beranda"))\n'
                   'pemenang = random.choice(kandidat)',
        "uji": "test_bug04_undi_tanpa_anggota_tidak_crash",
    },
]


def rupiah(angka):
    angka = int(angka)
    tanda = "-" if angka < 0 else ""
    return f"{tanda}Rp {abs(angka):,}".replace(",", ".")


def create_app(data_file=None):
    app = Flask(__name__)
    app.secret_key = "kunci-untuk-belajar-saja"
    app.config["DATA_FILE"] = data_file or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data.json"
    )
    app.add_template_filter(rupiah, "rupiah")
    app.jinja_env.globals.update(VERSI=VERSI, ADA_CHANGELOG=True)

    # ---------- penyimpanan sederhana (file JSON) ----------
    def muat():
        try:
            with open(app.config["DATA_FILE"], encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"iuran": None, "anggota": [], "riwayat": [], "next_id": 1}

    def simpan(data):
        with open(app.config["DATA_FILE"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def cari(data, anggota_id):
        anggota = next((a for a in data["anggota"] if a["id"] == anggota_id), None)
        if anggota is None:
            abort(404)
        return anggota

    def hitung_kas(data):
        sudah_bayar = sum(1 for a in data["anggota"] if a["bayar"])
        return (data["iuran"] or 0) * sudah_bayar

    # ---------- halaman ----------
    @app.get("/")
    def beranda():
        data = muat()
        return render_template("index.html", data=data, kas=hitung_kas(data))

    @app.get("/changelog")
    def changelog():
        return render_template("changelog.html", perubahan=PERUBAHAN)

    @app.post("/iuran")
    def atur_iuran():
        data = muat()
        try:
            nominal = int(request.form["iuran"])
        except (KeyError, ValueError):
            flash("Nominal iuran harus berupa angka bulat.", "error")
            return redirect(url_for("beranda"))
        # PERBAIKAN BUG-02: nominal harus positif
        if nominal <= 0:
            flash("Nominal iuran harus lebih dari 0.", "error")
            return redirect(url_for("beranda"))
        data["iuran"] = nominal
        simpan(data)
        flash(f"Iuran diatur menjadi {rupiah(nominal)} per anggota.", "ok")
        return redirect(url_for("beranda"))

    @app.post("/anggota")
    def tambah_anggota():
        data = muat()
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama anggota tidak boleh kosong.", "error")
            return redirect(url_for("beranda"))
        data["anggota"].append(
            {"id": data["next_id"], "nama": nama, "bayar": False, "menang": False}
        )
        data["next_id"] += 1
        simpan(data)
        flash(f"{nama} ditambahkan sebagai anggota.", "ok")
        return redirect(url_for("beranda"))

    @app.post("/anggota/<int:anggota_id>/bayar")
    def ubah_bayar(anggota_id):
        data = muat()
        anggota = cari(data, anggota_id)
        anggota["bayar"] = not anggota["bayar"]
        simpan(data)
        return redirect(url_for("beranda"))

    @app.post("/anggota/<int:anggota_id>/hapus")
    def hapus_anggota(anggota_id):
        data = muat()
        anggota = cari(data, anggota_id)
        data["anggota"].remove(anggota)
        simpan(data)
        flash(f"{anggota['nama']} dihapus dari daftar.", "ok")
        return redirect(url_for("beranda"))

    @app.post("/undi")
    def undi():
        data = muat()
        # PERBAIKAN BUG-01: hanya anggota yang belum pernah menang
        kandidat = [a for a in data["anggota"] if not a["menang"]]
        # PERBAIKAN BUG-04: tangani keadaan tanpa kandidat
        if not kandidat:
            if not data["anggota"]:
                flash("Belum ada anggota. Tambahkan anggota dulu sebelum mengundi.", "error")
            else:
                flash("Semua anggota sudah pernah menang. Putaran arisan ini selesai.", "error")
            return redirect(url_for("beranda"))
        pemenang = random.choice(kandidat)

        kas = hitung_kas(data)
        data["riwayat"].append(
            {"ronde": len(data["riwayat"]) + 1, "nama": pemenang["nama"], "kas": kas}
        )
        pemenang["menang"] = True
        for a in data["anggota"]:
            a["bayar"] = False  # ronde baru, iuran dihitung ulang
        simpan(data)
        flash(f"Pemenang ronde {len(data['riwayat'])}: {pemenang['nama']}.", "ok")
        return redirect(url_for("beranda"))

    return app


if __name__ == "__main__":
    create_app().run(port=5002, debug=True)
