# finance-agent — Günlük BIST100 Rapor Sistemi

Hafta içi her sabah ~10:30 TRT'de çalışan bir Claude Code cloud rutini, borsa-mcp üzerinden
canlı BIST verisi çekip günün yatırım komitesi raporunu üretir ve doğrudan `main`'e push eder.
Her rapor, önceki önerilerin gerçekleşen performansını **XU100'e göre rölatif (alfa)** olarak
deterministik biçimde ölçer ve tarihsel öğrenimleri günceller.

## Yapı

```
reports/               Günlük raporlar (YYYY-MM-DD-bist100.md) — anlatı katmanı
data/prices.csv        Kesinleşmiş gün-sonu kapanışlar (skorlamanın tek kaynağı)
data/positions.csv     Pozisyon defteri (giriş/stop/hedef/durum)
data/weights.csv       Günlük örnek portföy ağırlıkları + değişim tetikleri
data/triggers.csv      Aktif izleme tetikleri (rotasyon/overweight/kesim koşulları)
scripts/compute_perf.py  Deterministik getiri/alfa/maks-düşüş hesabı (markdown üretir)
METHODOLOGY.md         Tek otoriter metodoloji: fiyat çapası kuralları, alfa tanımı, veri limitleri
```

## Performans hesabı

```
python3 scripts/compute_perf.py
```

Alfa hesabının iki bacağı da (hisse + XU100) **kesinleşmiş kapanış** kullanır; seans içi
(intraday) değerler yalnızca raporun "bugünkü fiyat" gösteriminde yer alır. Ayrıntı ve
gerekçeler: [METHODOLOGY.md](METHODOLOGY.md).

## Veri kaynakları

borsa-mcp (yfinance + borsapy/TradingView + İş Yatırım), KAP/Mynet haber akışı,
TCMB makro verileri. Kaynak-tazelik haritası ve yapısal limitler METHODOLOGY.md §5'te.

> **Bu repo ve içerdiği raporlar yatırım tavsiyesi değildir.** Veriler kamuya açık
> kaynaklardan derlenmiştir ve hata içerebilir. Geçmiş performans gelecekteki getiriyi garanti etmez.
