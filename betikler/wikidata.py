"""Wikidata'dan Türk dizileri listesi ve Vikipedi bağlantılarının ayrıştırılması.

Saf işlevler (ağsız) testlerde doğrudan sınanır.
"""
import re

# Dizi: "televizyon dizisi" (Q5398426) ya da onun alt sınıfı; menşe ülkesi Türkiye (Q43).
SORGU = """
SELECT DISTINCT ?item WHERE {
  ?item wdt:P495 wd:Q43 ;
        wdt:P31/wdt:P279* wd:Q5398426 ;
        wikibase:sitelinks ?sl .
  FILTER(?sl >= 3)
}
"""

# Vikipedi olmayan "…wiki" siteleri
_VIKIPEDI_DEGIL = {
    "commonswiki", "specieswiki", "metawiki", "wikidatawiki", "mediawikiwiki",
    "sourceswiki", "outreachwiki", "wikimaniawiki", "foundationwiki", "incubatorwiki",
    "wikifunctionswiki", "testwiki", "test2wiki", "testwikidatawiki", "nostalgiawiki",
    "simplewiki",  # Basit İngilizce: ayrı bir dil değil
}
# Site kimliği ile alan adı arasında fark olanlar
_OZEL_ALAN = {
    "be_x_oldwiki": "be-tarask",
    "zh_min_nanwiki": "zh-min-nan",
    "zh_classicalwiki": "zh-classical",
    "zh_yuewiki": "zh-yue",
    "roa_rupwiki": "roa-rup",
    "map_bmswiki": "map-bms",
    "bat_smgwiki": "bat-smg",
    "fiu_vrowiki": "fiu-vro",
    "nds_nlwiki": "nds-nl",
    "roa_tarawiki": "roa-tara",
    "cbk_zamwiki": "cbk-zam",
}
_SITE = re.compile(r"^([a-z][a-z_]*)wiki$")


def qid_listesi(baglamlar):
    """SPARQL sonuç satırlarından benzersiz, sıralı QID listesi."""
    goruldu = []
    for b in baglamlar:
        uri = b.get("item", {}).get("value", "")
        q = uri.rsplit("/", 1)[-1]
        if re.fullmatch(r"Q\d+", q) and q not in goruldu:
            goruldu.append(q)
    return sorted(goruldu, key=lambda x: int(x[1:]))


def vikipedi_dili(site):
    """'eswiki' → 'es'; Vikipedi değilse (commonswiki, eswikiquote…) None."""
    if site in _VIKIPEDI_DEGIL:
        return None
    if site in _OZEL_ALAN:
        return _OZEL_ALAN[site]
    m = _SITE.match(site)
    if not m:
        return None
    return m.group(1).replace("_", "-")


def _yil(iddialar, ozellik):
    """P580 / P577 gibi zaman özelliğinden en erken yıl."""
    yillar = []
    for c in iddialar.get(ozellik, []):
        try:
            t = c["mainsnak"]["datavalue"]["value"]["time"]  # '+2011-01-05T00:00:00Z'
        except (KeyError, TypeError):
            continue
        m = re.match(r"^\+?(\d{4})-", t)
        if m:
            yillar.append(int(m.group(1)))
    return min(yillar) if yillar else None


def _degerler(iddialar, ozellik):
    out = []
    for c in iddialar.get(ozellik, []):
        try:
            out.append(c["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            continue
    return out


def dizi_ayristir(varlik):
    """wbgetentities varlığını sade bir kayda çevirir; yönlendirme/eksikse None.

    {'qid', 'ad', 'ad_en', 'yil', 'vikipedi': {dil: başlık}}
    """
    if not varlik or "missing" in varlik or "sitelinks" not in varlik:
        return None
    etiket = varlik.get("labels", {})
    vik = {}
    for site, bag in varlik["sitelinks"].items():
        dil = vikipedi_dili(site)
        if dil:
            vik[dil] = bag["title"]
    iddia = varlik.get("claims", {})
    ad_en = etiket.get("en", {}).get("value")
    ad = (vik.get("tr") or etiket.get("tr", {}).get("value") or ad_en or varlik["id"])
    ad = re.sub(r"\s*\((?:dizi|TV dizisi|televizyon dizisi|[^)]*dizi[^)]*)\)\s*$", "", ad)
    return {
        "qid": varlik["id"],
        "ad": ad,
        "ad_en": ad_en,
        "yil": _yil(iddia, "P580") or _yil(iddia, "P577"),
        "ulke": _degerler(iddia, "P495"),
        "vikipedi": dict(sorted(vik.items())),
    }


def yeterli_mi(dizi, en_az_yabanci=2):
    """Türkçe dışında en az `en_az_yabanci` Vikipedi'de maddesi olan Türk dizisi mi?"""
    if not dizi or "Q43" not in dizi.get("ulke", []):
        return False
    yabanci = [d for d in dizi["vikipedi"] if d != "tr"]
    return len(yabanci) >= en_az_yabanci
