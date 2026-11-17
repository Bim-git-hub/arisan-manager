"""Arisan Manager v1.0

VERSI UJI COBA: kode ini sengaja mengandung 4 bug untuk simulasi pengujian.
Daftar lengkap bug ada di BUG_REPORT.md. Jangan dipakai untuk arisan sungguhan.

Jalankan:  python app.py   lalu buka http://127.0.0.1:5001
"""
import json
import os
import random

from flask import Flask, abort, flash, redirect, render_template, request, url_for

VERSI = "1.0"


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
    app.jinja_env.globals.update(VERSI=VERSI, ADA_CHANGELOG=False)

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

    @app.post("/iuran")
    def atur_iuran():
        data = muat()
        try:
            nominal = int(request.form["iuran"])
        except (KeyError, ValueError):
            flash("Nominal iuran harus berupa angka bulat.", "error")
            return redirect(url_for("beranda"))
        # BUG #2: nominal nol atau negatif tidak diperiksa
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
        # BUG #1: kandidat adalah SEMUA anggota, termasuk yang sudah pernah menang
        kandidat = data["anggota"]
        # BUG #4: kandidat tidak diperiksa kosong, random.choice([]) -> IndexError (HTTP 500)
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
    create_app().run(port=5001, debug=True)
