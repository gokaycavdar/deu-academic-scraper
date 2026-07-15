# DEÜ AVESİS Akademik Rapor

DEÜ Bilgisayar Mühendisliği akademisyenlerinin AVESİS kayıtlarından Excel raporu oluşturmak için hazırlanmış web uygulamasıdır.

## Gereksinimler

- Windows bilgisayar
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- İnternet bağlantısı

Python kurulumu gerekmez.

## Uygulamayı Başlatma

1. Docker Desktop uygulamasını açın ve Docker Engine'in çalıştığından emin olun.
2. PowerShell'i proje klasöründe açın:

   ```powershell
   cd C:\Users\kullanici\deu-academic-scraper
   ```

3. Uygulamayı başlatın:

   ```powershell
   docker compose up --build
   ```

   İlk çalıştırmada Docker imajı ve Python paketleri indirileceği için işlem birkaç dakika sürebilir. Sonraki çalıştırmalar daha hızlıdır.

4. Tarayıcıdan aşağıdaki adresi açın:

   ```text
   http://localhost:8000
   ```

## Rapor Oluşturma

1. Bir veya daha fazla akademisyen seçin.
2. Zaman kapsamını belirleyin: tek yıl, yıl aralığı veya tüm yıllar.
3. İstenen kayıt türlerini seçin: Makale, Bildiri, Kitap, Proje ve Patent.
4. `Excel Raporunu Oluştur` düğmesine basın.
5. Rapor hazırlandığında Excel dosyası otomatik olarak indirilir.

Her kayıt türü Excel dosyasında ayrı bir sekmede yer alır.

> Tüm yıllar ve çok sayıda akademisyen seçildiğinde raporun hazırlanması uzun sürebilir. Uygulama ilerleme durumunu ekranda gösterir.

## Uygulamayı Durdurma

PowerShell penceresinde `Ctrl + C` tuşlarına basın. Ardından container'ı kapatmak için:

```powershell
docker compose down
```

## Sonraki Çalıştırmalar

Kod değişmediyse tekrar derleme gerekmez:

```powershell
docker compose up
```

Kod değiştiyse yeniden derleyin:

```powershell
docker compose up --build
```

## Akademisyen Listesini Güncelleme

Akademisyen listesi şu dosyada tutulur:

```text
data/faculty_catalog.csv
```

Yeni akademisyen eklemek veya bir akademisyeni pasifleştirmek için bu dosya düzenlenebilir.

- `is_active` değeri `true` olan akademisyenler web arayüzünde görünür.
- Liste `sort_order` değerine göre sıralanır.
- Değişiklikten sonra tarayıcı sayfasını yenilemek yeterlidir.

## Rapor Dosyaları

Uygulamanın ürettiği Excel dosyaları şu klasörde tutulur:

```text
data/generated/web
```

Bu klasör Docker container'ı kapatılsa veya silinse bile bilgisayarda kalır.

## Sorun Giderme

### Docker bağlantı hatası

Docker komutları hata veriyorsa Docker Desktop'ın açık olduğundan ve Docker Engine'in çalıştığından emin olun.

### 8000 portu kullanımda

`compose.yaml` dosyasındaki şu satırı:

```yaml
- "8000:8000"
```

şu şekilde değiştirin:

```yaml
- "8001:8000"
```

Ardından uygulamayı şu adresten açın:

```text
http://localhost:8001
```

### Raporun hazırlanması uzun sürüyor

AVESİS'ten kayıt detayları güvenli aralıklarla indirildiği için, çok fazla akademisyen veya geniş yıl aralığı seçildiğinde rapor daha uzun sürede hazırlanabilir.
