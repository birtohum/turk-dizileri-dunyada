"""Veri adımı: Wikidata → dizi listesi; Pageviews → aylık okumalar; site/veri/*.json.

Kullanım:
  python uret.py            # listeyi tazele, eksik ayları çek, siteyi üret
  python uret.py --hesap    # ağa çıkmadan yalnız site verisini yeniden üret
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diller  # noqa: E402
import hesap  # noqa: E402
import kaynak  # noqa: E402
import wikidata  # noqa: E402

KOK = kaynak.KOK
VERI = KOK / "veri"
SITE = KOK / "site" / "veri"
ILK = "2015-07"


def son_tam_ay(bugun=None):
    b = bugun or date.today()
    y, a = b.year, b.month - 1
    if a == 0:
        y, a = y - 1, 12
    return f"{y:04d}-{a:02d}"


def sonraki_ay(ay):
    y, a = map(int, ay.split("-"))
    return f"{y + (a == 12):04d}-{a % 12 + 1:02d}"


def yaz_json(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(yol.suffix + ".tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    gecici.replace(yol)


# ---------------------------------------------------------------- çekme

def dizileri_tazele():
    qidler = wikidata.qid_listesi(kaynak.sparql(wikidata.SORGU))
    print(f"Wikidata: {len(qidler)} aday", flush=True)
    varlik = kaynak.varliklar(qidler)
    diz = [wikidata.dizi_ayristir(varlik.get(q)) for q in qidler]
    diz = [d for d in diz if wikidata.yeterli_mi(d)]
    print(f"Türkçe dışında ≥2 Vikipedi'de maddesi olan: {len(diz)}", flush=True)
    yaz_json(VERI / "diziler.json", diz)
    return diz


def okumalari_cek(diz, bit, is_sayisi=4):
    tyol = VERI / "toplam.json.gz"
    top = kaynak.oku_gz(tyol) if tyol.exists() else {}
    dil_kume = sorted({dil for d in diz for dil in d["vikipedi"]})
    for dil in dil_kume:
        kayit = top.get(dil)
        bas = sonraki_ay(kayit["son"]) if kayit and kayit["son"] else ILK
        if bas > bit:
            continue
        yeni = kaynak.proje_aylik(f"{dil}.wikipedia", bas, bit)
        kayit = top.setdefault(dil, {"son": None, "a": {}})
        kayit["a"].update(yeni)
        kayit["son"] = max(yeni) if yeni else (kayit["son"] or None)
    kaynak.yaz_gz(tyol, top)
    # Wikimedia ayı henüz yayımlamadıysa o ayı "çekildi" saymamak için gerçek son ay
    hazir = top.get("en", {}).get("son")
    if hazir and hazir < bit:
        print(f"Wikimedia son ayı henüz yok; son ay {hazir}", flush=True)
        bit = hazir
    yol = VERI / "okuma.json.gz"
    depo = kaynak.oku_gz(yol) if yol.exists() else {}
    gerekli = {f"{dil}|{b}" for d in diz for dil, b in d["vikipedi"].items()}
    for k in list(depo):
        if k not in gerekli:
            del depo[k]
    isler = []
    for k in sorted(gerekli):
        kayit = depo.get(k)
        bas = sonraki_ay(kayit["son"]) if kayit else ILK
        if bas <= bit:
            isler.append((k, bas))
    print(f"Okuma: {len(isler)} madde çekilecek ({len(gerekli)} toplam)", flush=True)

    def is_(k, bas):
        dil, baslik = k.split("|", 1)
        return k, kaynak.madde_aylik(f"{dil}.wikipedia", baslik, bas, bit)

    with ThreadPoolExecutor(is_sayisi) as ex:
        fut = [ex.submit(is_, k, b) for k, b in isler]
        for i, f in enumerate(as_completed(fut), 1):
            k, yeni = f.result()
            kayit = depo.setdefault(k, {"son": None, "a": {}})
            kayit["a"].update({a: v for a, v in yeni.items() if a <= bit})
            kayit["son"] = bit
            if i % 250 == 0:
                print(f"  {i}/{len(isler)}", flush=True)
                kaynak.yaz_gz(yol, depo)
    kaynak.yaz_gz(yol, depo)
    return bit



# ---------------------------------------------------------------- hesap

def site_uret(bit):
    diz = json.loads((VERI / "diziler.json").read_text(encoding="utf-8"))
    okuma = kaynak.oku_gz(VERI / "okuma.json.gz")
    top = {d: k["a"] for d, k in kaynak.oku_gz(VERI / "toplam.json.gz").items()}
    eksen = hesap.aylar(ILK, bit)
    son12 = eksen[-12:]

    dil_dizi = {}      # dil -> {qid: toplam}
    dil_dizi12 = {}
    sicr = []
    dizi_kayit = []
    for d in diz:
        q = d["qid"]
        diller_ = {}
        kesifler = {}
        yabanci_top = 0
        for dil, b in d["vikipedi"].items():
            seri = okuma.get(f"{dil}|{b}", {}).get("a", {})
            t_all = hesap.toplam(seri)
            t_12 = hesap.toplam(seri, son12[0], son12[-1])
            dil_dizi.setdefault(dil, {})[q] = t_all
            dil_dizi12.setdefault(dil, {})[q] = t_12
            kes = hesap.kesif_ayi(seri, top.get(dil, {}))
            if kes:
                kesifler[dil] = kes
            if dil != "tr":
                yabanci_top += t_all
                s = hesap.en_guclu_sicrama(seri, top.get(dil, {}))
                if s:
                    sicr.append({"qid": q, "dil": dil, **s})
            diller_[dil] = {"b": b, "s": [seri.get(a, 0) for a in eksen], "k": kes,
                            "t": t_all}
        yaz_json(SITE / "dizi" / f"{q}.json", {"qid": q, "diller": diller_})
        dizi_kayit.append({"qid": q, "ad": d["ad"], "en": d["ad_en"], "yil": d["yil"],
                           "dil": len([x for x in d["vikipedi"] if x != "tr"]),
                           "yt": yabanci_top, "tr": diller_.get("tr", {}).get("t", 0),
                           "kes": kesifler})

    dil_ozet = []
    for dil, tablo in dil_dizi.items():
        t12 = sum(dil_dizi12[dil].values())
        sur12 = sum(top.get(dil, {}).get(a, 0) for a in son12)
        tall = sum(tablo.values())
        surall = sum(top.get(dil, {}).values())
        dil_ozet.append({
            "kod": dil, "ad": diller.ad(dil), "bolge": diller.bolge(dil),
            "dizi": sum(1 for v in tablo.values() if v > 0),
            "t": tall, "t12": t12,
            "ppm": round(hesap.pay_ppm(tall, surall) or 0, 2),
            "ppm12": round(hesap.pay_ppm(t12, sur12) or 0, 2),
            "ilk": hesap.siralama(tablo, 10),
            "ilk12": hesap.siralama(dil_dizi12[dil], 10),
        })
    dil_ozet.sort(key=lambda x: -x["t"])

    sicr.sort(key=lambda x: (-x["okuma"], x["ay"]))
    ozet = {
        "guncel": bit, "ilk": ILK, "son12": [son12[0], son12[-1]],
        "esik": {"ppm": hesap.ESIK_PPM, "en_az": hesap.EN_AZ, "ardisik": hesap.ARDISIK},
        "bolgeler": diller.BOLGE_SIRASI,
        "diller": dil_ozet,
        "diziler": sorted(dizi_kayit, key=lambda x: -x["yt"]),
        "sicramalar": [{**s, "taban": round(s["taban"]),
                        "ppm": round(s["ppm"], 2) if s["ppm"] else None} for s in sicr[:60]],
    }
    yaz_json(SITE / "ozet.json", ozet)
    print(f"Site verisi: {len(dizi_kayit)} dizi, {len(dil_ozet)} dil, {len(sicr)} sıçrama", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hesap", action="store_true", help="ağa çıkmadan yalnız site verisi")
    p.add_argument("--bit", help="son ay (YYYY-MM); varsayılan: son tamamlanmış ay")
    a = p.parse_args()
    bit = a.bit or son_tam_ay()
    if not a.hesap:
        diz = dizileri_tazele()
        bit = okumalari_cek(diz, bit)
    site_uret(bit)


if __name__ == "__main__":
    main()
