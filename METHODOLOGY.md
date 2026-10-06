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
- **Bilinen yanlılık (2026-10-06'da yazıldı, ÖNERİ — henüz uygulanmadı):** günlük kümülatif
  seri, geçmiş günleri **rapor günü açık olan** isimlerle yeniden hesaplar; bir pozisyon kapanınca
  serinin geçmişi değişir (10-05: BIMAS kapanınca 09-29 noktası +%13,90 → +%11,81). Bu bir
  hayatta-kalan yanlılığıdır. Önerilen düzeltme: seri, her gün **o gün açık olan** pozisyonlarla
  (realize edilenler çıkış tarihine kadar dahil) hesaplanır ve geçmiş noktalar dondurulur.
  Script değişikliği skorlamayı geriye dönük değiştireceği için **aylık derin incelemede (11-02)**
  karar verilir; o güne kadar çıktı aynen kullanılır ve resmi metrik başlıktaki son-gün değeridir.
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
| Çeyreklik YoY kâr büyümesi % temiz çekilemiyor (İş Yatırım bankalarda sınırlı) | **KAP-teyitli, AYNI ÇEYREK EPS beat** yeterli kanıttır — bkz. §5.4 (ör. GARAN 2026Q2: 7,21 vs 6,90 = +%4,5) |
| Net borç/FAVÖK tekil çekilemiyor | **EV/FAVÖK** ikamesi (get_financial_ratios) |
| `get_economic_calendar` sık boş | `get_macro_data` + `get_bond_yields` + son PPK kararı [kaynaklı] |
| `get_news` (KAP/mynet akışı) sistematik olarak **boş** dönüyor — araç hata vermiyor, `successful_count: 1` ile sıfır kalem döndürüyor (2026-09-09'da n=4 eşiğine ulaşıldı: 08-27, 09-04, 09-08, 09-09) | Katalizör bacağının **resmî** kanıtı `get_earnings`'in **KAP bilanço tarihi + EPS beat**'idir. **Sınırı:** bilanço-dışı katalizörler (ihale, kapasite, sözleşme, ortaklık yapısı) bu araç setiyle **tespit edilemez** — bu, açıklanamayan fiyat hareketlerinin kalıcı bir kör noktasıdır ve bir hareketi "tez teyidi" saymamak için gerekçedir |
| `get_evds_data` API anahtarı istiyor (hosted MCP'de yok) | Katalog dışı EVDS verisine güvenilmez |
| **RSI-14 iki araçta AYRIŞIYOR:** `get_technical_analysis` (Wilder) ile `scan_stocks` sistematik olarak farklı okuma döndürüyor; fark isme göre 0,1–17,1 puan (2026-09-11'de n=4 eşiğine ulaşıldı: 09-08, 09-09, 09-10, 09-11 — TUPRS'ta 14,0 / 14,0 / 17,1 / 14,0 puan). Hangisinin doğru olduğu bu araç setiyle çözülemiyor | **Kararda MUHAFAZAKÂR okuma bağlayıcıdır** (bir eşiği geçmemek lehimize ise yüksek okuma, geçmek lehimize ise düşük okuma); raporda **iki değer de** gösterilir. RSI zaten tek başına karar üretmez — §5.2 gereği yalnızca pozisyon boyutlandırmasında uyarı sinyalidir |
| **`borsamcp-new` oran/TA/tahvil/makro araçları kısmi arıza** — `get_financial_ratios` (çoklu sembolde 60 sn timeout; tekil çağrıda bazen "Invalid content from server"), `get_technical_analysis`, `get_bond_yields`, `get_macro_data` zaman aşımı (n=3 ölçülen seans: 09-30, 10-05, 10-06; 2026-10-06'da yazıldı). `get_historical_data` ve `scan_stocks` çalışıyor | **Resmî yedek yol (bu sırayla):** (1) `get_financial_ratios` **tekil** sembolle (kaynağı İş Yatırım; `current_price` alanı gün-içi fiyatın 2. bağımsız kaynağıdır); (2) F/K, EV/FAVÖK, RSI, EMA20, MACD için TradingView scanner doğrudan POST (`price_earnings_ttm`, `enterprise_value_ebitda_ttm`); emsal kümeleri borsapy endeks üyeliği ∩ XU100, yalnızca pozitif F/K; (3) tahvil/TÜFE için borsapy `bonds` / `Inflation`; (4) aynı-çeyrek EPS ve konsensüs dağılımı için yfinance `earnings_history` + borsapy `analyst_price_targets`. Emsal medyanı **tek kaynaktan** (TradingView) hesaplanır; İş Yatırım F/K'sı yalnızca çapraz kontrol olarak yanında gösterilir — kaynak, sonucu seçmek için gün içinde değiştirilmez |

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

### 5.3 Nakit tavanı ve dağıtım mekanizması (2026-09-21)

09-17'de bir **kural boşluğu** ölçüldü: iki zorunlu stop kesimi nakdi %45'e taşıdı, ama mevcut
kural seti nakit **tavanı** için hiçbir aksiyon tanımlamıyordu (yalnızca %35 eşiği için sayaç
vardı). Tetik açıldı ("tavan aşımı 3 ardışık seans sürerse dağıtım mekanizması yazılır"),
sayaç 09-17 → 09-18 → 09-21'de **3/3 doldu** ve bu bölüm o tetiğin **tanımlı aksiyonudur**.

Bölüm, nakit **%50'deyken ve piyasa verisine erişilemeyen bir kesinti gününde** yazılmıştır.
Bu kasıtlıdır: kuralı yazarken o günün fiyatları **görülemiyordu**, dolayısıyla kural sonuca
göre ayarlanamaz. Kuralı "uygun bir güne" ertelemek, tetiği yalnızca işe geldiğinde
uygulamak olurdu.

**1. Nakit asla tetiksiz dağıtılmaz.** Yüksek nakit seviyesi KURAL 9'u askıya **almaz**.
"Nakit yüksek olduğu için" alım yapmak **kalıcı olarak yasaktır**. Bu madde, aşağıdaki
maddelerin hiçbiri tarafından gevşetilemez.

**2. Tavanın tanımlı aksiyonu ÖLÇÜMDÜR, alım değildir.** Nakit 3 ardışık **ölçülen** seans
%40'ın üstünde kalırsa, rutin o günden itibaren her **ölçülen** seansta **BAĞLAYICI KISITI**
rapora kaydeder: o gün **en çok adayı eleyen bacak**, **sayıyla** (ör. "büyüme bacağı /
`eps_estimate` yok → 14 isim"). Böylece "liste dolmadı" pasif bir gözlem olmaktan çıkıp
**ölçülmüş bir teşhis** olur.

**3. Veri-boşluğu kısıtı ısrar ederse ikame ÖNCEDEN yazılır.** Bağlayıcı kısıt **5 ardışık
ölçülen seansta** aynı **veri-boşluğu** bacağıysa — yani bacağı düşüren şey bir değerleme/
büyüme **yargısı** değil, **beslemenin yokluğu** ise — huninin piyasa tarafından değil
**araç seti** tarafından sınırlandığı kabul edilir ve o bacak için kabul edilen bir **ikame**
METHODOLOGY'ye yazılır. **İkame, ilk uygulanacağı seanstan ÖNCEKİ bir raporda yazılır;**
bir ismi içeri alacağı seansta yazılan ikame geçersizdir. (§5.1'deki ex-target medyan ve
§5'teki EV/FAVÖK ikamesi bu sınıfın kabul edilmiş örnekleridir.)

**4. Tavan şunları ASLA yetkilendirmez:**
   - bir eleme bacağını, tam da bir ismi içeri alacağı gün gevşetmek;
   - SEÇİM KRİTERİ'nin üç bacağı geçmeden giriş yapmak;
   - mevcut bir pozisyonun ağırlığını, kendi tanımlı artış tetiği açılmadan artırmak;
   - §5.2'nin geri-alım kapısını nakit gerekçesiyle gevşetmek.

**5. Ölçüm birimi "ölçülen seans"tır.** Veri kesintisi günleri (§6.1) §5.3'ün 2. ve 3.
maddesindeki sayaçları **ilerletmez** — bağlayıcı kısıt o gün ölçülemez. Buna karşılık
1. maddedeki tavan sayacı **ilerler**, çünkü nakit oranı bir **ledger gerçeğidir**, piyasa
ölçümü değildir.

**Gerekçe (ölçülmüş):** 09-18'de liste 5 yerine **2 isimde** kaldı ve bağlayıcı kısıt
piyasa değil **besleme** idi — `eps_estimate` 14 isimde yoktu ve bunların arasında F/K 2,93
olan TSKB ile emsal medyanının %31,1 altındaki MPARK vardı. Nakit birikmesinin sebebi
"fırsat yok" değil, "**kanıt sınıfına ulaşamıyorum**"dur. Doğru düzeltme nakdi zorla
dağıtmak değil, kısıtı **ölçmek** ve ikamesini **önceden** yazmaktır.

### 5.4 Büyüme bacağı: EPS beat yalnızca AYNI ÇEYREK ile ölçülür (2026-10-05, aylık derin inceleme)

09-29'da ölçüldü: `get_earnings` (MCP) `eps_actual` alanı **TTM EPS**, `eps_estimate` alanı ise
**gelecek çeyrek tahmini**dir; raporlar 06-17'den 09-29'a kadar bu ikisini bölüp "3–4x beat"
yazdı (§5'teki eski "GARAN 28,07 vs 8,55" örneği bu hatanın ürünüdür ve **geçersizdir**).
Etki (geriye dönük): GARAN ve TUPRS kararları değişmezdi (gerçek beat +%4,5 / +%40,7);
ISCTR 09-04 (Q2 −%32,1 miss) ve VAKBN 09-02 (aynı-çeyrek veri yok) **girilmezdi**.

**Kural:** büyüme bacağı yalnızca **aynı çeyreğin** gerçekleşen EPS'i ile **aynı çeyreğin**
bilanço öncesi tahmini karşılaştırılarak ölçülür (dönem etiketi eşleşen yfinance
`earnings_history` satırı: `epsActual` vs `epsEstimate`). Her beat raporda **çeyrek etiketi
ve kaynağıyla** yazılır. Aynı-çeyrek satırı yoksa bacak **"ölçülemedi"** sayılır ve isim
alım listesine alınmaz (KURAL 2); TTM ya da nominal QoQ kıyası ikame **olamaz**.
Bu bir veri-boşluğu bacağıdır: §5.3/3 sayacı bu nedenle ilerleyebilir.

## 6. Günlük rutinin ledger görevleri (sırayla, rapor yazılmadan ÖNCE)

1. `get_historical_data` ile dünün kesinleşmiş kapanışlarını çek → `data/prices.csv`'ye ekle
   (open + watchlist tickerlar + XU100; hafta sonu/tatil ertesi son işlem günü).
2. `python3 scripts/compute_perf.py` çalıştır → çıktıyı raporun "Gerçekleşen Performans"
   bölümüne AYNEN yapıştır. UYARI satırı çıkarsa raporda belirt ve düzelt.
3. Bugünün ağırlıklarını (Δ + tetik gerekçesi) `data/weights.csv`'ye ekle (KURAL 9 anti-whipsaw).
4. `data/triggers.csv` durumlarını güncelle: tetiklenen → fired (+raporda aksiyon),
   geçersizleşen → expired, yeni tetik → yeni satır.
5. Pozisyon değişikliği varsa (giriş/çıkış/stop güncellemesi) `data/positions.csv`'yi güncelle.

## 6.1 VERİ KESİNTİSİ PROTOKOLÜ (2026-08-28'de resmileşti)

08-21, 08-26 ve 08-28'de rutin **hiçbir** piyasa verisine ulaşamadı. Bu üç günde davranış
yalnızca **presedanla** taşındı; aşağıdaki kural o presedanı bağlayıcı hâle getirir ve
Bölüm 6'nın "ZORUNLU KURAL"ıyla (prices.csv güncellenmeden rapor olusturulamaz) arasındaki
lafzî çelişkiyi kapatır.

**Kesinti tanımı (iki kanal birden kapalı):**
1. `borsamcp-new` araçları oturuma yüklenmedi (araç kaydı = 0) **veya** sunucu bağlanamadı; **ve**
2. doğrudan HTTP yedeği egress politikasınca reddedildi (proxy `connect_rejected` / 403).

**Kesinti günü davranışı — sırayla:**
1. **5 hisse listesi ÜRETİLMEZ.** KURAL 2 (fiyatı doğrulanamayan hisse listeye alınmaz)
   portföy ölçeğinde uygulanır: 100 ismin 100'ünün fiyatı doğrulanamıyorsa hiçbir isim giremez.
   Dünkü listeyi "bugünün önerisi" diye yeniden yazmak KURAL 3 ihlalidir.
2. **LEDGER DONDURULUR.** `prices.csv`'ye satır **eklenmez** (intraday yazmak §3.2 yasağıdır;
   web aramasından fiyat yazmak §6.1.1 yasağıdır). `positions.csv` değişmez.
   `weights.csv`'ye o günün satırları **ölçülemedi** tetiğiyle yazılır — KURAL 9 gereği
   tetik ölçülemiyorsa ağırlık oynatılmaz.
3. **`compute_perf.py` YİNE DE ÇALIŞTIRILIR** ve çıktısı rapora aynen girer. Çıktı mevcut
   en taze settled veriye kadar (as-of) geçerlidir; bu bir tekrar değil **devralmadır** ve
   raporda böyle etiketlenir.
4. **BACKFILL BORCU TETİK OLARAK KAYDEDİLİR** (`triggers.csv`, scope=ALTYAPI): kaç seansın
   kapanışı eksik ve hangi tickerlar. Araçlar döndüğü ilk gün bu borç, o rutinin
   **öncelikli** iş kalemidir.
5. **KESİNTİ RAPORU YAZILIR** (`reports/YYYY-MM-DD-bist100.md`, başlıkta rapor tipi
   ⛔ VERİ KESİNTİSİ olarak). Rapor kesintinin kanıtını (blokolanan hostlar + proxy
   damgası/saati), donmuş ledger'ın durumunu ve çözülemeyen tetikleri listeler.

**Bölüm 6 ZORUNLU KURAL'ının kapsamı:** o kural **öneri üreten** raporu bağlar. Kesinti
raporu öneri üretmediği için kuralın kapsamı dışındadır. Yani kesinti günü rapor yazmak
artık kuralın ihlali değil, **§6.1'in uygulanmasıdır.**

### 6.1.1 Web araması fiyat çapası DEĞİLDİR

08-21'de ölçüldü: "20 Ağustos 2026 XU100 kapanışı" araması **14.458,98** döndürdü; bu değer
08-20'nin değil, `prices.csv`'de zaten kayıtlı **08-19 kapanışının** kopyasıydı — haber akışı
bir günlük gecikmeyle yayınlanan seans özetini "bugün" diye sunuyor. Ledger'a yazılsaydı alfa
serisi sessizce bozulacaktı. **Web araması ne settled kapanış ne intraday çapa olarak kullanılır**;
kesinti günlerinde de kullanılmaz.

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
- 2026-10-01 ve 10-02'de rutin hiç çalışmadı (rapor/commit yok — §6.1 kesintisinden farklı sınıf).
  10-01'e planlanan aylık derin inceleme 10-05'te (ayın ilk ölçülen seansı) yapıldı; backfill ve
  bu günlerde ateşlenen ön-kayıtlı tetikler (BIMAS) geriye dönük, kesinleşmiş kapanışla işlendi.
