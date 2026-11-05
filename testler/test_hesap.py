import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "betikler"))

import hesap as h  # noqa: E402

# Milyon okumalık küçük bir sürüm: eşik = milyonda 1 → 1 okuma, ama en az 100 okuma şartı var.
KUCUK = {a: 1_000_000 for a in h.aylar("2015-07", "2026-10")}
# 500 milyonluk büyük sürüm: eşik = 500 okuma.
BUYUK = {a: 500_000_000 for a in h.aylar("2015-07", "2026-10")}


def test_aylar():
    assert h.aylar("2015-11", "2016-02") == ["2015-11", "2015-12", "2016-01", "2016-02"]
    assert h.aylar("2020-05", "2020-05") == ["2020-05"]
    assert h.aylar("2020-06", "2020-05") == []


def test_pay_ppm():
    assert h.pay_ppm(5, 1_000_000) == 5
    assert h.pay_ppm(5, 0) is None
    assert h.pay_ppm(5, None) is None


def test_kesif_ardisik_iki_ay():
    seri = {"2016-01": 600, "2016-02": 50, "2016-03": 700, "2016-04": 800, "2016-05": 900}
    # Ocak tek başına eşiği aşıyor, Şubat düşüyor → Mart–Nisan ilk ardışık dönem.
    assert h.kesif_ayi(seri, BUYUK) == "2016-03"


def test_kesif_surum_buyuklugune_gore():
    seri = {"2016-01": 300, "2016-02": 300}
    assert h.kesif_ayi(seri, BUYUK) is None          # 300 < 500 (milyonda 0,6)
    assert h.kesif_ayi(seri, KUCUK) == "2016-01"     # milyonda 300


def test_kesif_en_az_okuma_tabani():
    seri = {"2016-01": 99, "2016-02": 99}
    assert h.kesif_ayi(seri, KUCUK) is None          # milyonda 99 ama 100'ün altında


def test_kesif_eksik_ay_sifir_sayilir():
    # API sıfır okumalı ayı döndürmez; araya giren eksik ay diziyi böler.
    seri = {"2016-01": 900, "2016-03": 900, "2016-04": 900}
    assert h.kesif_ayi(seri, BUYUK) == "2016-03"


def test_kesif_toplam_yoksa_sayilmaz():
    seri = {"2016-01": 9000, "2016-02": 9000}
    assert h.kesif_ayi(seri, {}) is None
    assert h.kesif_ayi({}, BUYUK) is None


def test_kesif_son_ay_tek_basina_yetmez():
    seri = {"2026-09": 10, "2026-10": 9000}
    assert h.kesif_ayi(seri, BUYUK) is None
    assert h.kesif_ayi(seri, BUYUK, ardisik=1) == "2026-10"


def test_sicrama():
    seri = {a: 100 for a in h.aylar("2018-01", "2018-12")}
    seri["2019-01"] = 900      # 9 kat
    seri["2019-02"] = 120
    s = h.sicramalar(seri, BUYUK)
    assert [x["ay"] for x in s] == ["2019-01"]
    assert s[0]["kat"] == 9.0 and s[0]["taban"] == 100
    assert h.en_guclu_sicrama(seri, BUYUK)["ay"] == "2019-01"


def test_yeni_madde_sicrama_sayilmaz():
    # Madde 12 aydan kısa süredir varsa (önceki aylarda veri yok) sıçrama aranmaz.
    seri = {"2019-01": 50, "2019-02": 5000}
    assert h.sicramalar(seri, BUYUK) == []
    assert h.en_guclu_sicrama(seri, BUYUK) is None


def test_dusuk_tabanda_sicrama_sayilmaz():
    seri = {a: 5 for a in h.aylar("2018-01", "2018-12")}
    seri["2019-01"] = 5000
    assert h.sicramalar(seri, BUYUK) == []


def test_toplam_ve_siralama():
    seri = {"2020-01": 1, "2020-02": 2, "2021-01": 4}
    assert h.toplam(seri) == 7
    assert h.toplam(seri, "2020-02", "2020-12") == 2
    assert h.siralama({"Q5": 10, "Q2": 10, "Q9": 30, "Q1": 0}, n=2) == [("Q9", 30), ("Q2", 10)]
