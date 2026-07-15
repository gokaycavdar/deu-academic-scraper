# DEÜ Akademik Rapor

DEÜ Bilgisayar Mühendisliği akademisyenlerinin AVESİS ve YÖK Akademik kayıtlarını birleştirerek Excel raporu oluşturan web uygulamasıdır.

Uygulama; Makale, Bildiri, Kitap, Proje ve Patent kayıtlarını seçilen akademisyenler ve yıl filtresine göre toplar. Excel dosyasında her kayıt türü ayrı sekmede yer alır.

## Yerelde Çalıştırma

### Gereksinimler

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- İnternet bağlantısı

Python kurulumu gerekmez.

### 1. Projeyi klonlayın

PowerShell açın ve projeyi indirmek istediğiniz klasöre gidin:

```powershell
cd C:\Users\kullanici
```

Projeyi klonlayın:

```powershell
git clone https://github.com/gokaycavdar/deu-academic-scraper.git
```

Proje klasörüne girin:

```powershell
cd deu-academic-scraper
```

### 2. Docker Desktop'ı açın

Docker Desktop uygulamasını açın ve Docker Engine'in çalışır durumda olduğundan emin olun.

### 3. Uygulamayı başlatın

```powershell
docker compose up --build
```

İlk çalıştırmada Docker imajı ve Python paketleri indirileceği için işlem birkaç dakika sürebilir. Sonraki çalıştırmalar daha hızlıdır.

Tarayıcıdan aşağıdaki adresi açın:

```text
http://localhost:8000
```

### Sonraki çalıştırmalar

Kod değişmediyse yeniden derleme gerekmez:

```powershell
docker compose up
```

Kod değiştiyse yeniden derleyin:

```powershell
docker compose up --build
```

### Uygulamayı durdurma

Çalışan PowerShell penceresinde:

```text
Ctrl + C
```

Ardından container'ı kapatmak için:

```powershell
docker compose down
```

## Rapor Oluşturma

1. Bir veya daha fazla akademisyen seçin.
2. Zaman kapsamını belirleyin: tek yıl, yıl aralığı veya tüm yıllar.
3. İstenen kayıt türlerini seçin: Makale, Bildiri, Kitap, Proje ve Patent.
4. `Excel Raporunu Oluştur` düğmesine basın.
5. Rapor hazır olduğunda Excel dosyası otomatik olarak indirilir.

Seçilen tüm akademisyenlerin kayıtları tek Excel dosyasında bulunur. Her kayıt türü ayrı sekmede yer alır.

> Çok sayıda akademisyen, geniş yıl aralığı veya tüm kayıt türleri seçildiğinde raporun hazırlanması zaman alabilir. Uygulama ekranda ilerleme durumunu gösterir.

## Veri Kaynakları

Uygulama iki kaynaktan yararlanır:

- **AVESİS:** Ana kaynak. Sayfa sayıları, cilt, sayı, dergi, konferans, proje destek programı ve patent tarihleri gibi ana bibliyografik veriler buradan alınır.
- **YÖK Akademik:** Tamamlayıcı kaynak. Makale kapsamı, hakem durumu, ISSN, kitap ISBN'i, proje bütçesi/durumu/destekleyen kuruluş ve patent başvuru sahibi gibi ek alanları sağlar.

YÖK Akademik verisi, katalogda saklanan akademisyen kimlikleriyle alınır. İsim araması kullanılmaz.

## Excel İçeriği

Excel dosyasında ilk sekme özet sayfasıdır. Ardından seçilen kayıt türlerine göre sekmeler oluşturulur.

| Sekme | Alanlar |
|---|---|
| Makaleler | Akademisyen, Kayıt Kaynağı, Yıl, Makale Adı, Yazarlar, Dergi, Cilt, Sayı, Sayfalar, DOI, İndeksler, Kapsam, Hakem Durumu, ISSN |
| Bildiriler | Akademisyen, Kayıt Kaynağı, Yıl, Bildiri Adı, Yazarlar, Konferans, Tarih, Şehir, Ülke, Sayfalar, DOI, Kapsam |
| Kitaplar | Akademisyen, Kayıt Kaynağı, Yıl, Başlık, Yazarlar, Yayın Türü, Ana Kitap Adı, Yayınevi, Şehir, Sayfalar, Editörler, ISBN |
| Projeler | Akademisyen, Kayıt Kaynağı, Proje Adı, Proje Ekibi/Roller, Proje Türü, Destek Programı, Destekleyen Kuruluş, Proje Durumu, Bütçe, Başlangıç, Bitiş |
| Patentler | Akademisyen, Kayıt Kaynağı, Patent Adı, Mucitler, Fikri Mülkiyet, Patent Sınıfı, Tescil No, Tescil Tipi, Başvuru Ülkesi/Kuruluşu, Patent Başvuru Sahibi, Başvuru Tarihi, Tescil Tarihi, Durum |

`AVESİS'te Aç` kolonu olan kayıtlarda ilgili AVESİS detay sayfasına bağlantı bulunur. YÖK Akademik popup bağlantıları oturuma bağlı olduğu için Excel'e kalıcı `YÖK'te Aç` bağlantısı eklenmez.

## Kayıt Kaynağı ve Birleştirme

Her kayıtta `Kayıt Kaynağı` alanı bulunur:

- `AVESİS`
- `YÖK Akademik`
- `AVESİS + YÖK Akademik`

Aynı kayıt iki kaynakta da bulunduğunda AVESİS ana kaynak kabul edilir:

- AVESİS'teki dolu alanlar korunur.
- YÖK Akademik yalnızca AVESİS'te boş kalan alanları tamamlar.
- Örneğin AVESİS'teki sayfa bilgisi korunurken, YÖK'ten gelen kapsam, hakem durumu ve ISSN eklenir.

### Tekilleştirme

Kaynak içindeki kesin tekrarlar otomatik olarak elenir:

- AVESİS yayın/proje/patent kayıtları detay URL'sine göre tekilleştirilir.
- YÖK makale ve bildirileri popup URL'si ile DOI bilgisine göre tekilleştirilir.
- YÖK patentleri tescil numarasına göre tekilleştirilir.

AVESİS ve YÖK Akademik kayıtları arasında birleştirme yapılırken şu bilgiler kullanılır:

```text
Akademisyen + Kayıt Türü + Normalize Edilmiş Başlık
```

Başlık karşılaştırmasında büyük/küçük harf, Türkçe karakter, noktalama işareti ve fazla boşluk farkları yok sayılır.

Birden fazla aynı başlıklı aday varsa:

1. DOI eşitliği aranır.
2. DOI yoksa yıl ve yazar soyadı kümeleri karşılaştırılır.
3. Kesin eşleşme yoksa kayıtlar ayrı bırakılır.

Bu yaklaşım, yanlış kayıtların otomatik olarak birleştirilmesini önler.

## Yıl Filtresi

- Makale, bildiri, kitap ve patentlerde kayıt yılı kullanılır.
- Yılı bulunamayan kayıtlar filtre dışında bırakılmaz.
- Projelerde başlangıç-bitiş dönemi seçilen yıl aralığıyla kesişiyorsa kayıt rapora alınır.

Örnek: 2024-2025 arasında yürütülen bir proje, 2025 yılı raporunda görünür.

> Patentlerde AVESİS tescil/başvuru tarihini, YÖK Akademik ise çoğu zaman tescil numarasının başındaki yılı gösterebilir. Tüm yıllar raporunda bu durum sorun oluşturmaz; dar yıl filtrelerinde kaynaklar arasında yıl farkı görülebilir.

## Bilinçli Olarak Eklenmeyen Alanlar

Aşağıdaki bilgiler şu an rapora dahil değildir:

- Dergi çeyreklik dilimi: Q1, Q2, Q3, Q4
- Atıf sayıları: Web of Science, Scopus, Google Akademik vb.
- PlumX ve Mendeley metrikleri
- Yayın anahtar kelimeleri
- DEÜ adresli bilgisi
- Bildiri ISBN'i
- Kitap baskı sayısı ve toplam sayfa sayısı

Q bilgisi ve atıf metrikleri için ayrı, güvenilir ve güncel bir veri kaynağı gerekir. İleride ek modül olarak değerlendirilebilir.

## Akademisyen Listesini Güncelleme

Akademisyen listesi şu dosyada tutulur:

```text
data/faculty_catalog.csv
```

Önemli sütunlar:

| Sütun | Açıklama |
|---|---|
| `id` | Uygulama içi benzersiz akademisyen kimliği |
| `sort_order` | Listede gösterim sırası |
| `academic_title` | Unvan |
| `full_name` | Akademisyen adı |
| `unit` | Birim bilgisi |
| `profile_url` | AVESİS profil adresi |
| `yok_author_id` | YÖK Akademik kimliği |
| `yok_profile_sira` | YÖK Akademik profil oturum değeri |
| `is_active` | `true` ise arayüzde görünür |

Yeni akademisyen eklendikten sonra tarayıcı sayfasını yenilemek yeterlidir.

## Rapor Dosyaları

Üretilen Excel raporları şu klasörde tutulur:

```text
data/generated/web
```

`compose.yaml` içindeki veri klasörü eşlemesi nedeniyle bu dosyalar Docker container silinse bile bilgisayarda kalır.

## Sorun Giderme

### Docker komutları çalışmıyor

Docker Desktop'ın açık olduğundan ve Docker Engine'in çalıştığından emin olun.

### 8000 portu kullanımda

`compose.yaml` içindeki:

```yaml
- "8000:8000"
```

satırını örneğin şu şekilde değiştirin:

```yaml
- "8001:8000"
```

Ardından uygulamayı şu adresten açın:

```text
http://localhost:8001
```

### Raporun hazırlanması uzun sürüyor

Uygulama AVESİS ve YÖK Akademik'e güvenli istek aralıklarıyla erişir. Çok sayıda akademisyen veya tüm yıllar seçildiğinde rapor süresi uzayabilir.

### Container loglarını görmek

```powershell
docker compose logs -f web
```

### Uygulama güncel kodu çalıştırmıyor

Container'ı durdurup yeniden derleyin:

```powershell
docker compose down
docker compose up --build
```
