"use strict";
(function () {
  const AY = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  const nf = new Intl.NumberFormat("tr-TR");
  const $ = (s) => document.querySelector(s);
  const el = (etiket, sinif, metin) => {
    const e = document.createElement(etiket);
    if (sinif) e.className = sinif;
    if (metin != null) e.textContent = metin;
    return e;
  };
  const SVG = "http://www.w3.org/2000/svg";
  const svgEl = (ad, oz) => {
    const e = document.createElementNS(SVG, ad);
    for (const k in oz) e.setAttribute(k, oz[k]);
    return e;
  };

  function kisa(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(".", ",") + " milyon";
    if (n >= 1e4) return Math.round(n / 1e3) + " bin";
    return nf.format(Math.round(n));
  }
  function ppmYaz(p) {
    if (p >= 10) return nf.format(Math.round(p));
    return p.toFixed(1).replace(".", ",");
  }
  function ayYaz(a) {
    if (!a) return "";
    const [y, m] = a.split("-");
    return AY[+m - 1] + " " + y;
  }

  let O = null;          // özet
  let DIZI = {};         // qid -> kayıt
  let DIL = {};          // kod -> kayıt
  let eksen = [];
  let donem = "12", sdonem = "12";
  const ipucu = $("#ipucu");

  function ipucuGoster(e, metin) {
    ipucu.textContent = metin;
    ipucu.hidden = false;
    const x = Math.min(e.clientX + 12, window.innerWidth - ipucu.offsetWidth - 8);
    const y = e.clientY - ipucu.offsetHeight - 10;
    ipucu.style.left = x + "px";
    ipucu.style.top = (y < 4 ? e.clientY + 16 : y) + "px";
  }
  function ipucuGizle() { ipucu.hidden = true; }

  function aylar(bas, bit) {
    const out = [];
    let [y, m] = bas.split("-").map(Number);
    const [by, bm] = bit.split("-").map(Number);
    while (y < by || (y === by && m <= bm)) {
      out.push(`${y}-${String(m).padStart(2, "0")}`);
      if (++m === 13) { y++; m = 1; }
    }
    return out;
  }

  // ---------------------------------------------------------------- üst rakamlar
  function rakamlar() {
    const yabanci = O.diller.filter((d) => d.kod !== "tr");
    const t12 = yabanci.reduce((s, d) => s + d.t12, 0);
    const kut = $("#rakamlar");
    const ekle = (b, s) => { const r = el("div", "rakam"); r.append(el("b", null, b), el("span", null, s)); kut.append(r); };
    ekle(nf.format(O.diziler.length), "Türk dizisi");
    ekle(nf.format(yabanci.filter((d) => d.t12 > 0).length), "Türkçe dışında dil");
    ekle(kisa(t12), `Türkçe dışı okuma, son 12 ay (${ayYaz(O.son12[0])} – ${ayYaz(O.son12[1])})`);
    const enIlgili = yabanci.filter((d) => d.t12 >= 100000).sort((a, b) => b.ppm12 - a.ppm12)[0];
    if (enIlgili) {
      const bir = Math.round(1e6 / enIlgili.ppm12);
      const p = el("p", "ana-bulgu");
      p.append("Son 12 ayda ", el("strong", null, `${enIlgili.ad} Vikipedi'de okunan her ${nf.format(bir)} sayfadan biri`),
        " bir Türk dizisinin sayfasıydı. İngilizce Vikipedi'de ise " +
        `${nf.format(Math.round(1e6 / DIL.en.ppm12))} sayfada bir.`);
      kut.after(p);
    }
  }

  // ---------------------------------------------------------------- diller
  function dillerCiz() {
    const kut = $("#diller");
    kut.textContent = "";
    const anahtar = donem === "12" ? "ppm12" : "ppm";
    const tAnahtar = donem === "12" ? "t12" : "t";
    const ilkAnahtar = donem === "12" ? "ilk12" : "ilk";
    const alt = donem === "12" ? 1000 : 10000;
    const goster = O.diller.filter((d) => d.kod !== "tr" && d[tAnahtar] >= alt);
    const enCok = Math.max(...goster.map((d) => d[anahtar]));
    for (const b of O.bolgeler) {
      const grup = goster.filter((d) => d.bolge === b).sort((x, y) => y[anahtar] - x[anahtar]);
      if (!grup.length) continue;
      kut.append(el("div", "bolge", b));
      for (const d of grup) {
        const s = el("button", "dil");
        s.type = "button";
        s.append(el("span", "dil-ad", d.ad));
        const yer = el("span", "cubuk-yer");
        const c = el("span", "cubuk");
        c.style.width = (d[anahtar] / enCok * 100).toFixed(2) + "%";
        yer.append(c);
        s.append(yer);
        const a = el("span", "dil-alt");
        const ilk = d[ilkAnahtar][0];
        a.append("Milyonda ", el("b", null, ppmYaz(d[anahtar])), ` · ${kisa(d[tAnahtar])} okuma`);
        if (ilk) a.append(` · en çok: ${DIZI[ilk[0]].ad}`);
        s.append(a);
        s.addEventListener("click", () => { dilSec(d.kod); $("#sira-bolum").scrollIntoView({ behavior: "smooth" }); });
        kut.append(s);
      }
    }
    const tr = DIL.tr;
    const gizli = O.diller.filter((d) => d.kod !== "tr" && d[tAnahtar] > 0 && d[tAnahtar] < alt).length;
    $("#diller-not").textContent =
      `Karşılaştırma için: Türkçe Vikipedi'de bu oran milyonda ${ppmYaz(tr[anahtar])}. ` +
      (gizli ? `Bu dönemde ${nf.format(alt)} okumanın altında kalan ${gizli} dil listede yok.` : "");
  }

  // ---------------------------------------------------------------- dizi zaman çizelgesi
  const onbellek = {};
  async function diziYukle(q) {
    if (!onbellek[q]) onbellek[q] = fetch(`veri/dizi/${q}.json`).then((r) => r.json());
    return onbellek[q];
  }

  function serit(seri, kesif) {
    const n = seri.length;
    const svg = svgEl("svg", { class: "z-serit", viewBox: `0 0 ${n} 18`, preserveAspectRatio: "none", role: "img" });
    const enCok = Math.max(1, ...seri);
    svg.append(svgEl("rect", { x: 0, y: 2, width: n, height: 14, fill: "var(--isi0)" }));
    for (let i = 0; i < n; i++) {
      if (!seri[i]) continue;
      const o = Math.sqrt(seri[i] / enCok);
      svg.append(svgEl("rect", { x: i, y: 2, width: 1.02, height: 14, fill: "var(--isi1)", "fill-opacity": o.toFixed(3) }));
    }
    if (kesif) {
      const i = eksen.indexOf(kesif);
      if (i >= 0) svg.append(svgEl("rect", { x: i, y: 0, width: Math.max(1, n / 180), height: 18, fill: "var(--yazi)" }));
    }
    svg.addEventListener("mousemove", (e) => {
      const r = svg.getBoundingClientRect();
      const i = Math.min(n - 1, Math.max(0, Math.floor((e.clientX - r.left) / r.width * n)));
      ipucuGoster(e, `${ayYaz(eksen[i])}: ${nf.format(seri[i])} okuma`);
    });
    svg.addEventListener("mouseleave", ipucuGizle);
    return svg;
  }

  function eksenCiz() {
    const s = el("div", "z-eksen");
    s.append(el("span"));
    const n = eksen.length;
    const svg = svgEl("svg", { viewBox: `0 0 ${n} 16`, preserveAspectRatio: "none" });
    const dar = window.innerWidth < 520;
    eksen.forEach((a, i) => {
      if (!a.endsWith("-01")) return;
      const y = +a.slice(0, 4);
      if (dar && y % 2) return;
      svg.append(svgEl("rect", { x: i, y: 11, width: n / 400, height: 5, fill: "var(--cizgi)" }));
    });
    s.append(svg);
    // yıl yazıları: SVG ölçeklenmesin diye HTML ile
    const yazilar = el("div");
    yazilar.style.cssText = "position:relative;height:14px;grid-column:2";
    eksen.forEach((a, i) => {
      if (!a.endsWith("-01")) return;
      const y = +a.slice(0, 4);
      if (dar ? y % 4 : y % 2) return;
      const t = el("span", null, String(y));
      t.style.cssText = `position:absolute;left:${(i / n * 100).toFixed(2)}%;transform:translateX(-50%)`;
      yazilar.append(t);
    });
    s.append(el("span"), yazilar);
    return s;
  }

  let acik = false;
  async function diziGoster(q) {
    const d = DIZI[q];
    if (!d) return;
    $("#dizi-sec").value = q;
    history.replaceState(null, "", "#" + q);
    const v = await diziYukle(q);
    const oz = $("#dizi-ozet");
    oz.textContent = "";
    oz.append(el("h3", null, d.ad));
    const yabanci = Object.entries(v.diller).filter(([k]) => k !== "tr");
    const kesifli = yabanci.filter(([, x]) => x.k).sort((a, b) => a[1].k.localeCompare(b[1].k) || b[1].t - a[1].t);
    let cumle = (d.yil ? `${d.yil} · ` : "") + `Türkçe dışında ${yabanci.length} Vikipedi'de maddesi var. ` +
      `2015'ten beri Türkçe dışında ${kisa(d.yt)}, Türkçe'de ${kisa(d.tr)} okuma.`;
    if (kesifli.length) {
      const [k0, x0] = kesifli[0];
      cumle += x0.k === O.ilk
        ? ` Veri başladığında (${ayYaz(O.ilk)}) ${kesifli.filter(([, x]) => x.k === O.ilk).length} dilde zaten çok okunuyordu.`
        : ` İlk keşfeden dil: ${DIL[k0] ? DIL[k0].ad : k0} (${ayYaz(x0.k)}).`;
    }
    oz.append(el("p", null, cumle));

    const zaman = $("#zaman");
    zaman.textContent = "";
    zaman.append(eksenCiz());
    const digerleri = yabanci.filter(([, x]) => !x.k).sort((a, b) => b[1].t - a[1].t);
    const satirlar = [];
    if (v.diller.tr) satirlar.push(["tr", v.diller.tr, true]);
    for (const [k, x] of kesifli.concat(digerleri)) satirlar.push([k, x, false]);
    const SINIR = 14;
    satirlar.forEach(([k, x, tr], i) => {
      const s = el("div", "z-satir");
      if (!acik && i > SINIR) s.hidden = true;
      const ad = el("span", "z-ad");
      const adMetin = DIL[k] ? DIL[k].ad : k;
      ad.append(tr ? el("b", null, adMetin) : adMetin);
      ad.title = `${adMetin}: ${x.b}`;
      s.append(ad, serit(x.s, x.k));
      const alt = el("span", "z-kesif",
        (tr ? "karşılaştırma · " : "") + (x.k ? `keşif: ${ayYaz(x.k)}${x.k === O.ilk ? " ya da daha önce" : ""}` : "eşik aşılmadı") + ` · toplam ${kisa(x.t)}`);
      s.append(alt);
      zaman.append(s);
    });
    if (!acik && satirlar.length > SINIR + 1) {
      const b = el("button", "daha", `Tüm ${satirlar.length} dili göster`);
      b.type = "button";
      b.addEventListener("click", () => { acik = true; diziGoster(q); });
      zaman.append(b);
    }
  }

  // ---------------------------------------------------------------- sıralama
  function dilSec(kod) {
    $("#dil-sec").value = kod;
    siraCiz();
  }
  function siraCiz() {
    const d = DIL[$("#dil-sec").value];
    const liste = sdonem === "12" ? d.ilk12 : d.ilk;
    const ol = $("#sira");
    ol.textContent = "";
    if (!liste.length) { ol.append(el("li", null, "Bu dönemde okuma yok.")); return; }
    const enCok = liste[0][1];
    for (const [q, t] of liste) {
      const li = el("li");
      const ad = el("div", "ad");
      const b = el("button", null, DIZI[q].ad);
      b.type = "button";
      b.addEventListener("click", () => { diziGoster(q); $("#dizi-bolum").scrollIntoView({ behavior: "smooth" }); });
      ad.append(b);
      const olcu = el("div", "olcu");
      const yer = el("span", "cubuk-yer");
      const c = el("span", "cubuk");
      c.style.width = (t / enCok * 100).toFixed(2) + "%";
      yer.append(c);
      olcu.append(yer, el("span", null, kisa(t) + " okuma"));
      li.append(ad, olcu);
      ol.append(li);
    }
  }

  // ---------------------------------------------------------------- sıçramalar
  function sicramalarCiz() {
    const ol = $("#sicramalar");
    for (const s of O.sicramalar.slice(0, 25)) {
      const d = DIZI[s.qid];
      const li = el("li");
      const b = el("button");
      b.type = "button";
      b.append(el("div", "ust-satir", `${ayYaz(s.ay)} · ${DIL[s.dil] ? DIL[s.dil].ad : s.dil}`));
      b.append(el("div", "baslik", d.ad));
      b.append(el("div", "alt",
        `${nf.format(s.okuma)} okuma. Önceki 12 ayda ayda yaklaşık ${nf.format(s.taban)} okunuyordu (${s.kat >= 10 ? nf.format(Math.round(s.kat)) : String(s.kat).replace(".", ",")} kat).`));
      b.addEventListener("click", () => { diziGoster(s.qid); $("#dizi-bolum").scrollIntoView({ behavior: "smooth" }); });
      li.append(b);
      ol.append(li);
    }
  }

  // ---------------------------------------------------------------- başlat
  async function basla() {
    O = await fetch("veri/ozet.json").then((r) => r.json());
    eksen = aylar(O.ilk, O.guncel);
    O.diziler.forEach((d) => { DIZI[d.qid] = d; });
    O.diller.forEach((d) => { DIL[d.kod] = d; });

    rakamlar();
    dillerCiz();
    document.querySelectorAll("[data-donem]").forEach((b) => b.addEventListener("click", () => {
      donem = b.dataset.donem;
      document.querySelectorAll("[data-donem]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      dillerCiz();
    }));

    const ds = $("#dizi-sec");
    for (const d of O.diziler) {
      const o = el("option", null, d.ad + (d.yil ? ` (${d.yil})` : ""));
      o.value = d.qid;
      ds.append(o);
    }
    ds.addEventListener("change", () => { acik = false; diziGoster(ds.value); });
    const e = O.esik;
    $("#kesif-tanim").textContent =
      `Keşif ayı: o dilin Vikipedi'sinde okunan her 1 milyon sayfanın en az ${e.ppm}'i bu dizinin sayfası olduğunda ` +
      `(ve en az ${e.en_az} okuma), üstelik bu durum art arda ${e.ardisik} ay sürdüğünde, bunun ilk ayı. ` +
      `Renk koyuluğu her satırda o dilin en yüksek ayına göredir. Veri ${ayYaz(O.ilk)}'da başlar; o ay görünen keşifler daha eski olabilir. ` +
      `Son ay: ${ayYaz(O.guncel)}.`;

    const sel = $("#dil-sec");
    O.diller.filter((d) => d.t > 0).slice().sort((a, b) => a.ad.localeCompare(b.ad, "tr")).forEach((d) => {
      const o = el("option", null, d.ad);
      o.value = d.kod;
      sel.append(o);
    });
    sel.addEventListener("change", siraCiz);
    document.querySelectorAll("[data-sdonem]").forEach((b) => b.addEventListener("click", () => {
      sdonem = b.dataset.sdonem;
      document.querySelectorAll("[data-sdonem]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      siraCiz();
    }));
    const varsayilan = O.diller.find((d) => d.kod !== "tr" && d.t12 > 0) || O.diller[0];
    dilSec(DIL.es && DIL.es.t > 0 ? "es" : varsayilan.kod);

    sicramalarCiz();
    const h = location.hash.slice(1);
    diziGoster(DIZI[h] ? h : O.diziler[0].qid);
  }
  basla().catch((err) => {
    $("#rakamlar").textContent = "Veri yüklenemedi.";
    console.error(err);
  });
})();
