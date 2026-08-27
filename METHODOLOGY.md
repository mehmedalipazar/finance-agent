# Metodoloji — BIST100 Günlük Rapor Sistemi

Bu belge, günlük raporların ve performans defterinin (ledger) tek otoriter metodoloji kaynağıdır.
Günlük raporlar buradaki kurallara uyar; kurallar değişecekse ÖNCE bu dosya güncellenir.

## 1. Sistem özeti

Hafta içi her sabah ~10:30 TRT'de (seans içi) bir Claude Code cloud rutini çalışır:
borsa-mcp'den canlı veri çeker, ledger'ı günceller, `scripts/compute_perf.py` ile performansı
deterministik hesaplar, günün raporunu `reports/YYYY-MM-DD-bist100.md` olarak yazar ve
doğrudan `main`'e push eder.

## 2. Dosyalar

| Dosya | İçerik | Kim günceller |
|-------|--------|---------------|
| `data/prices.csv` | Yalnızca **kesinleşmiş** gün-sonu kapanışlar (`date,ticker,close`). Intraday değer GİRİLMEZ. | Rutin, her sabah **dünün** kapanışlarını ekler |
| `data/positions.csv` | Pozisyon defteri: giriş tarihi/kapanışı, stop (initial + current), hedef, durum (open / watchlist / closed) | Rutin, yalnızca giriş/çıkış/stop-değişikliğinde |
| `data/weights.csv` | Günlük örnek portföy ağırlıkları + Δ + değişim tetiği | Rutin, her rapor günü 5 satır ekler |
| `data/triggers.csv` | Aktif izleme tetikleri (rotasyon, overweight, kesim koşulları) | Rutin, her gün durumları günceller (active/fired/expired) |
| `scripts/compute_perf.py` | Deterministik getiri/alfa/maks-düşüş hesabı; markdown üretir | Elle (metodoloji değişirse) |
| `reports/` | Günlük raporlar (insan-okur anlatı katmanı) | Rutin |

## 3. Fiyat çapası kuralları (KRİTİK)

1. **Skorlama = kesinleşmiş kapanış.** Tüm getiri/alfa hesapları `data/prices.csv`'deki
   settled kapanışlarla yapılır (giriş çıpası dahil: `positions.csv.entry_close`).
2. **Intraday yalnızca gösterimdir.** Rutin 10:30'da çalıştığı için o günün oturmuş kapanışı
   henüz yoktur; raporda "bugünün fiyatı" (~15 dk gecikmeli TradingView/borsapy + İş Yatırım
   çapraz teyitli) yalnızca güncel durum, giriş bölgesi ve stop/hedef demirlemesi için kullanılır.
   **Intraday değer alfa hesabına ve prices.csv'ye girmez.**
   Gerekçe: 30 Haz'da XU100 10:32 intraday 14.270 yazılmışken kesin kapanış 14.121 geldi;
   1 Tem'de 10:32 intraday 14.086 iken kesin kapanış 14.350 geldi — intraday çapa alfayı
   ±1-2 puan oynatabiliyor (endeks-print artefaktı).
3. **Her sabah backfill:** rutin, `get_historical_data` ile bir önceki işlem gününün
   kapanışlarını (tüm open + watchlist tickerlar + XU100) `prices.csv`'ye ekler.
4. **XU100 kaynağı `get_historical_data`'dır.** (`get_index_data` XU100 için yalnızca
   metadata döndürüyor — bilinen yapısal limit, her gün yeniden raporlanmaz.)
5. `get_quick_info` BIST'te güvenilmez → kullanılmaz.

## 4. Performans ölçümü

- **Alfa = hisse getirisi − aynı dönem XU100 getirisi** (iki bacak da settled close).
  Mutlak getiri tek başına asla sunulmaz (KURAL 6).
- **Resmi portföy metriği:** açık pozisyonların **eşit-ağırlık** ortalaması; XU100 bacağı
  isim bazında kendi giriş tarihinden bileşiklenir. (`weights.csv`'deki örnek ağırlıklar
  anlatı katmanıdır; resmi seri eşit-ağırlıktır.)
- **Kapanmış pozisyonlarda İKİ bacak da `exit_date`'te dondurulur** (2026-08-27'de
  düzeltildi; 08-24 METODOLOJİ tetiği). Hisse bacağı `exit_close`'ta durur, XU100 bacağı da
  aynı tarihteki kapanışta durur — böylece realize alfa aynı dönemi ölçer. Eski davranış
  (XU100 bacağının bugüne uzaması) TUPRS'ta 8,4 puanlık sahte sapma üretiyordu.
  `exit_date` prices.csv'de yoksa o tarihten önceki son kapanış kullanılır.
- **Watchlist** isimleri (ör. THYAO) portföye dahil edilmez; karşılaştırma için ayrı satırda izlenir.
- Rapordaki geçmiş performans bölümü `compute_perf.py` çıktısından AYNEN alınır;
  model elle getiri/alfa hesaplamaz.
- Tarihsel not: 16-17 Haz girişleri rapor anında intraday fiyatla yazılmıştı
  (`positions.csv.report_price`); resmi seri giriş gününün kesinleşmiş kapanışını
  (`entry_close`) kullanır. Eski raporlardaki alfalarla ±0,5 puan fark bundandır.

## 5. Yapısal veri limitleri (bir kez burada; günlük DÜRÜSTLÜK bölümünde TEKRARLANMAZ)

| Limit | Kabul edilen ikame |
|-------|--------------------|
| Analist hedefi tek besleme (yfinance konsensüsü; ikinci bağımsız feed yok) | Konsensüs dağılımı (düşük/ort/medyan/yüksek + analist sayısı) + hedefin ima ettiği F/K kıyası |
| Çeyreklik YoY kâr büyümesi % temiz çekilemiyor (İş Yatırım bankalarda sınırlı) | **KAP-teyitli EPS beat** yeterli kanıttır (ör. GARAN 28,07 vs 8,55) |
| Net borç/FAVÖK tekil çekilemiyor | **EV/FAVÖK** ikamesi (get_financial_ratios) |
| `get_economic_calendar` sık boş | `get_macro_data` + `get_bond_yields` + son PPK kararı [kaynaklı] |
| `get_evds_data` API anahtarı istiyor (hosted MCP'de yok) | Katalog dışı EVDS verisine güvenilmez |

Günlük DÜRÜSTLÜK bölümü yalnızca **o güne özgü** gerçek veri boşluklarını yazar.

### 5.1 Değer bacağı: sektör medyanı HEDEF HARİÇ hesaplanır (2026-08-27)

`get_sector_comparison`'un döndürdüğü `sector_median_pe` **hedef hisseyi de içerir**. Hedef,
emsal kümesinin ortanca ismiyse "F/K < sektör medyanı" testi matematiksel olarak dejenere olur
ve hisse ne kadar ucuz olursa olsun testi **asla geçemez**. Bu üç kez gerçekleşti:
BIMAS 16,75 vs 16,75 (08-25), ENJSA 19,09 vs 19,09 (08-25), BIMAS 17,00 vs 17,00 (08-27).

**Kural:** değer bacağı **`F/K < hedef HARİÇ emsal medyanı`** ile ölçülür. Ex-target medyan,
emsal listesinden hedef satırı çıkarılıp kalan F/K'ların ortancası alınarak hesaplanır ve
rapora **açıkça yazılır** (hem dahil hem hariç medyan gösterilir).

### 5.2 Kesim sonrası GERİ ALIM kapısı (2026-08-27)

08-24'te ölçüldü: TUPRS'ta geri alım kapısı "yeni katalizör + **RSI<60 pullback** + settled >291"
diye yazılmıştı; `settled >291` 07-31'de sağlandı ama **RSI<60 bir kez bile gelmedi** çünkü hisse
kesintisiz yükseldi. Kapı fiilen ulaşılamazdı ve 44 puan alfa maliyeti üretti. Güçlü trendde
"RSI düşsün de girelim" kapısı yapısal olarak açılmaz.

**Kural — kesilen bir isme geri giriş yalnızca şu ÜÇ şart birlikte sağlanırsa yapılır:**
1. **SEÇİM KRİTERİ'nin üç bacağı da TAZE veriyle geçer** (reel kâr büyümesi, ex-target medyan
   altı F/K veya EV/FAVÖK, son 3 ayda KAP-teyitli katalizör);
2. **Son kesinleşmiş kapanış ema20'nin ÜSTÜNDE** (trend onarımı — RSI eşiği DEĞİL);
3. **Çıkış tarihinden SONRA gelen, tarihli ve KAP-teyitli YENİ bir katalizör** vardır.

RSI artık geri alım kapısında **eşik değil**; yalnızca pozisyon boyutlandırmasında uyarı
sinyali olarak raporlanır (RSI yüksekse giriş **starter** boyutta yapılır).
Bu kural her isme simetrik uygulanır: 08-27 itibarıyla CCOLA'yı (settled 79,00 < ema20 81,44)
**açmaz**, AEFES'i (büyüme bacağı başarısız) **açmaz**.

## 6. Günlük rutinin ledger görevleri (sırayla, rapor yazılmadan ÖNCE)

1. `get_historical_data` ile dünün kesinleşmiş kapanışlarını çek → `data/prices.csv`'ye ekle
   (open + watchlist tickerlar + XU100; hafta sonu/tatil ertesi son işlem günü).
2. `python3 scripts/compute_perf.py` çalıştır → çıktıyı raporun "Gerçekleşen Performans"
   bölümüne AYNEN yapıştır. UYARI satırı çıkarsa raporda belirt ve düzelt.
3. Bugünün ağırlıklarını (Δ + tetik gerekçesi) `data/weights.csv`'ye ekle (KURAL 9 anti-whipsaw).
4. `data/triggers.csv` durumlarını güncelle: tetiklenen → fired (+raporda aksiyon),
   geçersizleşen → expired, yeni tetik → yeni satır.
5. Pozisyon değişikliği varsa (giriş/çıkış/stop güncellemesi) `data/positions.csv`'yi güncelle.

## 7. Geçmiş analiz derinliği

- **Her gün:** ledger (4 CSV) + **yalnızca dünkü rapor** okunur. Tarihsel Öğrenimler bölümü
  dünkü rapordan devralınır ve günün kanıtıyla güncellenir.
- **Ayın ilk iş günü:** tüm `reports/` arşivi baştan okunur (derin örüntü çıkarımı,
  öğrenimlerin sıfırdan doğrulanması). Diğer günler arşiv taraması yapılmaz (maliyet O(n²) büyüyordu).
- Örneklem küçükken (≲30 seans) örüntüler "kanıt" değil "HİPOTEZ" olarak işaretlenir.

## 8. Tarihçe notları

- 2026-06-20 ve 2026-06-21 raporları eski günlük-cron döneminden kalmadır (Cmt/Paz, seans yok);
  `prices.csv`'de bu tarihler yoktur. 25 Haz'dan beri cron yalnızca hafta içi çalışır.
- 2026-06-16 → 07-01 raporlarındaki performans tabloları intraday çapalıydı; 2026-07-02
  itibarıyla resmi seri bu ledger'dır (Bölüm 4'teki tarihsel not geçerli).
