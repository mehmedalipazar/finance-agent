#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finance-agent — deterministik performans/alfa hesabı (Phase 2).

Girdi:
  data/prices.csv     date,ticker,close  (yalnızca KESİNLEŞMİŞ gün-sonu kapanışlar; intraday girilmez)
  data/positions.csv  pozisyon defteri (giriş çıpası = entry_close, settled)
  data/weights.csv    günlük örnek portföy ağırlıkları (yalnızca son satırlar gösterilir)

Çıktı: stdout'a markdown — günlük raporun "Gerçekleşen Performans" bölümüne aynen yapıştırılır.

Metodoloji: METHODOLOGY.md. Alfa = hisse getirisi − aynı dönem XU100 getirisi;
iki bacak da kesinleşmiş kapanış. Bugünün intraday fiyatı bu hesaba GİRMEZ.

Kullanım: python3 scripts/compute_perf.py
"""
import csv
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = "XU100"
STALE_DAYS = 5  # as-of bundan eskiyse uyarı

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def tr_num(x, nd=2):
    """1234.5 -> '1.234,50' (Türkçe biçim)."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def tr_pct(x, nd=2):
    """+1.55 -> '+%1,55' ; -1.21 -> '−%1,21' (rapor stili)."""
    body = tr_num(abs(x), nd)
    return ("+%" if x >= 0 else "−%") + body


def load_prices():
    prices = {}  # ticker -> {date: close}
    with open(ROOT / "data" / "prices.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = row["date"].strip()
            t = row["ticker"].strip()
            prices.setdefault(t, {})[d] = float(row["close"])
    return prices


def load_positions():
    with open(ROOT / "data" / "positions.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_last_weights():
    rows = []
    path = ROOT / "data" / "weights.csv"
    if not path.exists():
        return None, rows
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None, []
    last_date = max(r["date"] for r in rows)
    return last_date, [r for r in rows if r["date"] == last_date]


def main():
    warnings = []
    prices = load_prices()
    positions = load_positions()

    if BENCH not in prices:
        print(f"HATA: prices.csv içinde {BENCH} yok.")
        sys.exit(1)

    bench = prices[BENCH]
    all_dates = sorted(bench.keys())
    as_of = all_dates[-1]

    age = (date.today() - datetime.strptime(as_of, "%Y-%m-%d").date()).days
    if age > STALE_DAYS:
        warnings.append(
            f"prices.csv bayat görünüyor: son satır {as_of} ({age} gün önce). "
            f"Dünün kesinleşmiş kapanışlarını ekleyin."
        )

    # --- pozisyon bazlı getiri/alfa ---
    rows = []
    for p in positions:
        t = p["ticker"]
        ed = p["entry_date"]
        if t not in prices or ed not in prices[t]:
            warnings.append(f"{t}: giriş tarihi {ed} için prices.csv satırı yok — atlandı.")
            continue
        entry = prices[t][ed]
        declared = float(p["entry_close"])
        if abs(entry - declared) / declared > 0.005:
            warnings.append(
                f"{t}: positions.csv entry_close={declared} ile prices.csv {ed} kapanışı "
                f"{entry} uyuşmuyor (>%0,5). prices.csv esas alındı."
            )
        if as_of not in prices[t]:
            warnings.append(f"{t}: {as_of} kapanışı yok — son mevcut kapanış kullanıldı.")
            last_d = max(d for d in prices[t] if d <= as_of)
        else:
            last_d = as_of
        last = prices[t][last_d]
        ret = (last / entry - 1) * 100
        xu_ret = (bench[as_of] / bench[ed] - 1) * 100
        rows.append({
            "ticker": t, "entry_date": ed, "entry": entry, "last": last,
            "ret": ret, "xu": xu_ret, "alpha": ret - xu_ret,
            "status": p["status"].strip(),
        })

    open_rows = [r for r in rows if r["status"] == "open"]
    open_rows.sort(key=lambda r: -r["alpha"])
    watch_rows = [r for r in rows if r["status"] != "open"]

    port_ret = sum(r["ret"] for r in open_rows) / len(open_rows)
    port_xu = sum(r["xu"] for r in open_rows) / len(open_rows)
    port_alpha = port_ret - port_xu
    hits = sum(1 for r in open_rows if r["alpha"] > 0)

    # --- günlük kümülatif seri (eşit-ağırlık, isim kendi girişinden itibaren) ---
    series = []  # (date, port_pct, xu_pct, alpha_pp)
    peak_rel, max_dd_rel, max_dd_date = -1e9, 0.0, None
    for d in all_dates:
        held = [r for r in open_rows if r["entry_date"] <= d]
        if not held:
            continue
        navs, xunavs = [], []
        for r in held:
            t = r["ticker"]
            if d in prices[t]:
                navs.append(prices[t][d] / r["entry"])
                xunavs.append(bench[d] / bench[r["entry_date"]])
        if not navs:
            continue
        nav = sum(navs) / len(navs)
        xunav = sum(xunavs) / len(xunavs)
        rel = nav / xunav
        if rel > peak_rel:
            peak_rel = rel
        dd = (rel / peak_rel - 1) * 100
        if dd < max_dd_rel:
            max_dd_rel, max_dd_date = dd, d
        series.append((d, (nav - 1) * 100, (xunav - 1) * 100, (nav - xunav) * 100))

    # --- çıktı ---
    print(f"### Gerçekleşen Performans — kesinleşmiş kapanışlarla (as-of: {as_of})")
    print()
    print("*(Kaynak: `data/prices.csv` + `scripts/compute_perf.py` — deterministik hesap. "
          "Giriş ve skorlama = kesinleşmiş kapanış; bugünün intraday fiyatı bu tabloya girmez.)*")
    print()
    print("| Hisse | Giriş (tarih) | Giriş kapanışı | Son kapanış | Getiri | XU100 (aynı dönem) | **ALFA** | Durum |")
    print("|-------|------|-------:|-------:|-------:|-------:|-------:|------|")
    for r in open_rows + watch_rows:
        durum = "çekirdek" if r["status"] == "open" else "izleme (portföyde değil)"
        print(f"| {r['ticker']} | {r['entry_date']} | {tr_num(r['entry'])} | {tr_num(r['last'])} "
              f"| {tr_pct(r['ret'])} | {tr_pct(r['xu'])} | **{tr_pct(r['alpha'])}** | {durum} |")
    print()
    print(f"**Eşit-ağırlık çekirdek portföy ({len(open_rows)} isim):** "
          f"getiri {tr_pct(port_ret)} · aynı dönem XU100 {tr_pct(port_xu)} · "
          f"**KÜMÜLATİF ALFA {tr_pct(port_alpha)}**")
    print(f"**İsabet (pozitif alfa):** {hits}/{len(open_rows)} · "
          f"**Maks. rölatif düşüş (XU100'e karşı, kapanıştan):** "
          f"{tr_pct(max_dd_rel)}" + (f" ({max_dd_date})" if max_dd_date else ""))
    print()
    print("<details><summary>Günlük kümülatif seri (kapanış bazlı)</summary>")
    print()
    print("| Tarih | Portföy | XU100 | ALFA (pp) |")
    print("|-------|-------:|-------:|-------:|")
    for d, pr, xr, al in series:
        print(f"| {d} | {tr_pct(pr)} | {tr_pct(xr)} | {tr_pct(al)} |")
    print()
    print("</details>")

    wd, wrows = load_last_weights()
    if wrows:
        active = [w for w in wrows if float(w["weight_pct"]) > 0]
        parts = " · ".join(f"{w['ticker']} %{w['weight_pct']}" for w in active)
        print()
        print(f"**Son kayıtlı ağırlıklar ({wd}):** {parts}")

    if warnings:
        print()
        print("**UYARILAR (ledger tutarlılığı):**")
        for w in warnings:
            print(f"- ⚠ {w}")


if __name__ == "__main__":
    main()
