import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "betikler"))

import wikidata as w  # noqa: E402


def _zaman(t):
    return [{"mainsnak": {"datavalue": {"value": {"time": t}}}}]


def _id(*q):
    return [{"mainsnak": {"datavalue": {"value": {"id": x}}}} for x in q]


VARLIK = {
    "id": "Q123",
    "labels": {"en": {"value": "What Is Fatmagül's Fault?"}, "tr": {"value": "Fatmagül'ün Suçu Ne?"}},
    "sitelinks": {
        "trwiki": {"site": "trwiki", "title": "Fatmagül'ün Suçu Ne? (dizi)"},
        "eswiki": {"site": "eswiki", "title": "Fatmagül'ün Suçu Ne?"},
        "arwiki": {"site": "arwiki", "title": "ما ذنب فاطمة غل"},
        "commonswiki": {"site": "commonswiki", "title": "Category:X"},
        "enwikiquote": {"site": "enwikiquote", "title": "X"},
        "simplewiki": {"site": "simplewiki", "title": "X"},
        "zh_min_nanwiki": {"site": "zh_min_nanwiki", "title": "X"},
        "be_x_oldwiki": {"site": "be_x_oldwiki", "title": "Y"},
    },
    "claims": {
        "P580": _zaman("+2010-09-16T00:00:00Z"),
        "P577": _zaman("+2011-01-01T00:00:00Z"),
        "P495": _id("Q43"),
    },
}


def test_qid_listesi_benzersiz_ve_sirali():
    b = [{"item": {"value": "http://www.wikidata.org/entity/Q20"}},
         {"item": {"value": "http://www.wikidata.org/entity/Q3"}},
         {"item": {"value": "http://www.wikidata.org/entity/Q20"}},
         {"item": {"value": "http://www.wikidata.org/entity/L5"}},
         {}]
    assert w.qid_listesi(b) == ["Q3", "Q20"]


def test_vikipedi_dili():
    assert w.vikipedi_dili("eswiki") == "es"
    assert w.vikipedi_dili("zh_min_nanwiki") == "zh-min-nan"
    assert w.vikipedi_dili("be_x_oldwiki") == "be-tarask"
    for site in ("commonswiki", "enwikiquote", "dewikisource", "wikidatawiki", "simplewiki",
                 "specieswiki", "metawiki"):
        assert w.vikipedi_dili(site) is None, site


def test_dizi_ayristir():
    d = w.dizi_ayristir(VARLIK)
    assert d["qid"] == "Q123"
    assert d["ad"] == "Fatmagül'ün Suçu Ne?"          # "(dizi)" eki atılır
    assert d["ad_en"] == "What Is Fatmagül's Fault?"
    assert d["yil"] == 2010                           # P580 öncelikli
    assert d["vikipedi"] == {"ar": "ما ذنب فاطمة غل", "be-tarask": "Y", "es": "Fatmagül'ün Suçu Ne?",
                             "tr": "Fatmagül'ün Suçu Ne? (dizi)", "zh-min-nan": "X"}
    assert list(d["vikipedi"]) == sorted(d["vikipedi"])


def test_dizi_ayristir_eksik_ve_yedek_ad():
    assert w.dizi_ayristir(None) is None
    assert w.dizi_ayristir({"id": "Q1", "missing": ""}) is None
    v = {"id": "Q9", "labels": {"en": {"value": "Only English"}},
         "sitelinks": {"enwiki": {"title": "Only English (TV series)"}},
         "claims": {"P577": _zaman("+2019-05-01T00:00:00Z")}}
    d = w.dizi_ayristir(v)
    assert d["ad"] == "Only English"
    assert d["yil"] == 2019
    v2 = {"id": "Q10", "labels": {}, "sitelinks": {}, "claims": {}}
    assert w.dizi_ayristir(v2)["ad"] == "Q10"
    assert w.dizi_ayristir(v2)["yil"] is None


def test_bozuk_zaman_atlanir():
    v = {"id": "Q11", "labels": {}, "sitelinks": {},
         "claims": {"P580": [{"mainsnak": {"snaktype": "somevalue"}}] + _zaman("+2014-01-01T00:00:00Z")}}
    assert w.dizi_ayristir(v)["yil"] == 2014


def test_yeterli_mi():
    d = w.dizi_ayristir(VARLIK)
    assert w.yeterli_mi(d)                       # es, ar, … ≥2 yabancı
    az = {**d, "vikipedi": {"tr": "x", "es": "y"}}
    assert not w.yeterli_mi(az)
    yabanci_ulke = {**d, "ulke": ["Q30"]}
    assert not w.yeterli_mi(yabanci_ulke)
    assert not w.yeterli_mi(None)
