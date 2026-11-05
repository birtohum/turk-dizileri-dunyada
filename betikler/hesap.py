"""Saf hesaplar: keşif ayı, sıçramalar, sıralamalar. Ağ yok; testlerde sınanır.

Okuma serileri {'YYYY-MM': okuma}, sürüm toplamları {'YYYY-MM': o dil Vikipedi'sinin
o ayki toplam insan okuması} biçimindedir.
"""
from statistics import median

# Keşif eşiği: o dil sürümündeki tüm okumaların milyonda 1'i ve en az 100 okuma,
# art arda en az 2 ay (tek aylık rastlantısal sıçramayı saymamak için).
ESIK_PPM = 1.0
EN_AZ = 100
ARDISIK = 2


def aylar(bas, bit):
    """'2015-07', '2015-09' → ['2015-07', '2015-08', '2015-09']"""
    y, a = map(int, bas.split("-"))
    by, ba = map(int, bit.split("-"))
    out = []
    while (y, a) <= (by, ba):
        out.append(f"{y:04d}-{a:02d}")
        a += 1
        if a == 13:
            y, a = y + 1, 1
    return out


def pay_ppm(okuma, toplam):
    """Milyonda pay; toplam yok/0 ise None."""
    if not toplam:
        return None
    return okuma / toplam * 1e6


def esik_ustu(okuma, toplam, esik_ppm=ESIK_PPM, en_az=EN_AZ):
    p = pay_ppm(okuma, toplam)
    return p is not None and okuma >= en_az and p >= esik_ppm


def kesif_ayi(seri, toplamlar, esik_ppm=ESIK_PPM, en_az=EN_AZ, ardisik=ARDISIK):
    """Okumanın eşiği art arda `ardisik` ay aştığı ilk dönemin ilk ayı; yoksa None.

    Verinin son ayı eşiği aşıyorsa ve sonrası henüz yoksa, eldeki ardışık aylar yeterli
    sayılmaz: keşif ancak ardışık koşul tamamen görüldüğünde ilan edilir.
    """
    if not seri:
        return None
    eksen = aylar(min(seri), max(seri))
    sayac, bas = 0, None
    for ay in eksen:
        if esik_ustu(seri.get(ay, 0), toplamlar.get(ay), esik_ppm, en_az):
            if sayac == 0:
                bas = ay
            sayac += 1
            if sayac >= ardisik:
                return bas
        else:
            sayac, bas = 0, None
    return None


def sicramalar(seri, toplamlar, kat=5.0, en_az=500, gecmis=12, taban_en_az=30):
    """Okumanın önceki `gecmis` ayın ortancasının en az `kat` katına çıktığı aylar.

    Yalnız madde en az `gecmis` aydır okunuyorsa (önceki ayların hepsinde veri varsa)
    ve ortanca en az `taban_en_az` ise bakılır; yeni açılan maddenin ilk ayı sıçrama
    sayılmaz. Dönüş: [{'ay', 'okuma', 'taban', 'kat', 'ppm'}]
    """
    if not seri:
        return []
    eksen = aylar(min(seri), max(seri))
    out = []
    for i in range(gecmis, len(eksen)):
        onceki = [seri.get(a) for a in eksen[i - gecmis:i]]
        if any(v is None for v in onceki):
            continue
        taban = median(onceki)
        if taban < taban_en_az:
            continue
        ay = eksen[i]
        v = seri.get(ay, 0)
        if v >= en_az and v >= kat * taban:
            out.append({"ay": ay, "okuma": v, "taban": taban, "kat": round(v / taban, 1),
                        "ppm": pay_ppm(v, toplamlar.get(ay))})
    return out


def en_guclu_sicrama(seri, toplamlar, **kw):
    """Bir (dizi, dil) için en yüksek katlı sıçrama; yoksa None."""
    s = sicramalar(seri, toplamlar, **kw)
    return max(s, key=lambda x: (x["kat"], x["okuma"])) if s else None


def toplam(seri, bas=None, bit=None):
    return sum(v for a, v in seri.items() if (bas is None or a >= bas) and (bit is None or a <= bit))


def siralama(diziler_okuma, n=10):
    """{qid: toplam} → en çok okunan n dizi [(qid, toplam)], eşitlikte QID sırası."""
    return sorted(((q, t) for q, t in diziler_okuma.items() if t > 0),
                  key=lambda x: (-x[1], int(x[0][1:])))[:n]
