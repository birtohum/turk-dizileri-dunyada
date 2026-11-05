# Türk dizileri dünyada

Türk dizilerinin Vikipedi maddeleri hangi dillerde, ne zaman okunmaya başladı?

Site: https://birtohum.github.io/turk-dizileri-dunyada/

## Ne ölçüyor?

**Vikipedi okumasını**, yani bir dizinin Vikipedi sayfasının kaç kez açıldığını. Bu, merakın kaba
bir göstergesidir; reyting, izleyici sayısı ya da satış değildir. Dil de ülke değildir: İspanyolca
sayfa İspanya'dan da Latin Amerika'dan da okunur.

## Yöntem

1. **Dizi listesi (Wikidata):** `televizyon dizisi` (Q5398426) ya da alt sınıfı olan, menşe ülkesi
   Türkiye (P495 = Q43) olan ve Türkçe dışında en az iki Vikipedi'de maddesi bulunan öğeler.
2. **Okuma (Wikimedia Pageviews REST API):** her dizinin her dil sürümündeki maddesi için aylık
   okuma, 2015-07'den bugüne, `all-access`, `agent=user` (yalnız insan okuyucular).
3. **Sürüm büyüklüğü:** her dil Vikipedi'sinin aylık toplam insan okuması (`aggregate`).
4. **Keşif ayı:** okumanın o sürümdeki tüm okumaların milyonda 1'ini **ve** 100 okumayı art arda
   2 ay aştığı ilk dönemin ilk ayı.
5. **Sıçrama:** okumanın önceki 12 ayın ortancasının en az 5 katına (ve en az 500 okumaya)
   çıktığı ay. Madde en az 12 aydır okunuyor ve ortanca en az 30 olmalı.

## Sınırlar

- Okuma izlenme değildir; dil ülke değildir.
- Maddesi yazılmamış bir dildeki ilgi görünmez.
- Sayım maddenin bugünkü adıyla yapılır; ad değişmeden önceki okumalar ve yönlendirmeler sayılmaz.
- Veri 2015-07'de başlar; o aydaki "keşifler" daha eski olabilir.
- `agent=user` süzgeci otomatik programların çoğunu ayıklar, hepsini değil.

## Çalıştırma

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt pytest   # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m pytest -q testler
cd betikler && ../.venv/Scripts/python uret.py          # ilk çalıştırma ~30 dk
```

`veri/` ham aylık okumaları tutar; aylık iş akışı (`.github/workflows/aylik.yml`) yalnız eksik
ayları çeker ve `site/veri/` dosyalarını yeniden üretir. İstekler sırayla ve saniyede en fazla
~8 olacak biçimde yapılır; User-Agent proje adını ve bu deponun adresini taşır.

## Lisans

Kod Apache-2.0. Veri: Wikimedia Pageviews ve Wikidata (CC0).
