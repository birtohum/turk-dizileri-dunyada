"""Wikidata ve Wikimedia Pageviews REST API istemcisi (önbellekli, kibar hızda).

Hesap gerekmez. User-Agent'ta yalnız proje adı ve depo adresi var; e-posta yok.
"""
import gzip
import json
import os
import socket
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests
import urllib3.util.connection

# Bazı ağlarda IPv6 bağlantısı ~14 sn takılıp IPv4'e düşüyor; doğrudan IPv4 kullan.
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

UA = ("turk-dizileri-dunyada/1.0 "
      "(https://github.com/birtohum/turk-dizileri-dunyada; Wikimedia Pageviews + Wikidata)")
REST = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
SPARQL = "https://query.wikidata.org/sparql"
WD_API = "https://www.wikidata.org/w/api.php"
KOK = Path(__file__).resolve().parent.parent

_yerel = threading.local()
_hiz_kilit = threading.Lock()
_son_istek = [0.0]
ARALIK = 0.12  # tüm iş parçacıkları için istekler arası en az süre (≈8 istek/sn üst sınır)


def _oturum():
    if not hasattr(_yerel, "s"):
        _yerel.s = requests.Session()
        _yerel.s.headers["User-Agent"] = UA
    return _yerel.s


def _sira_bekle():
    with _hiz_kilit:
        simdi = time.monotonic()
        bekle = _son_istek[0] + ARALIK - simdi
        if bekle > 0:
            time.sleep(bekle)
        _son_istek[0] = time.monotonic()


def al(url, params=None, deneme=10, timeout=60):
    """GET → JSON; 404 için None; 429/5xx için bekleyip yeniden dener."""
    for i in range(deneme):
        _sira_bekle()
        try:
            r = _oturum().get(url, params=params, timeout=timeout)
        except requests.RequestException:
            time.sleep(2 ** i)
            continue
        if r.status_code == 404:
            return None
        if r.status_code == 429 or r.status_code >= 500:
            bekle = r.headers.get("retry-after")
            time.sleep(int(bekle) if bekle and bekle.isdigit() else min(60, 2 ** i * 2))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"İstek başarısız: {url}")


def oku_gz(yol):
    with gzip.open(yol, "rt", encoding="utf-8") as f:
        return json.load(f)


def yaz_gz(yol, veri):
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_name(f"{yol.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    # mtime=0 ve boş dosya adı: aynı içerik → aynı bayt (gereksiz commit olmasın)
    metin = json.dumps(veri, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with open(gecici, "wb") as ham, gzip.GzipFile(filename="", mode="wb", fileobj=ham, mtime=0) as f:
        f.write(metin.encode("utf-8"))
    gecici.replace(yol)


def sparql(sorgu):
    d = al(SPARQL, {"query": sorgu, "format": "json"}, timeout=180)
    return d["results"]["bindings"]


def varliklar(qidler):
    """wbgetentities: {qid: varlık} (50'lik gruplar)."""
    sonuc = {}
    qidler = list(qidler)
    for i in range(0, len(qidler), 50):
        d = al(WD_API, {"action": "wbgetentities", "format": "json",
                        "ids": "|".join(qidler[i:i + 50]),
                        "props": "labels|sitelinks|claims"})
        sonuc.update(d.get("entities", {}))
    return sonuc


def _ay(ts):
    return f"{ts[:4]}-{ts[4:6]}"


def madde_aylik(proje, baslik, bas, bit):
    """{'YYYY-MM': okuma} — yalnız insan okuyucular (agent=user), tüm erişimler.
    bas/bit: 'YYYY-MM'."""
    url = (f"{REST}/per-article/{proje}/all-access/user/{quote(baslik.replace(' ', '_'), safe='')}"
           f"/monthly/{bas.replace('-', '')}0100/{bit.replace('-', '')}2800")
    d = al(url)
    if d is None:
        return {}
    return {_ay(x["timestamp"]): x["views"] for x in d["items"]}


def proje_aylik(proje, bas, bit):
    url = (f"{REST}/aggregate/{proje}/all-access/user/monthly/"
           f"{bas.replace('-', '')}0100/{bit.replace('-', '')}2800")
    d = al(url) or {"items": []}
    return {_ay(x["timestamp"]): x["views"] for x in d["items"]}
