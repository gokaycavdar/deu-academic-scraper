# AVESİS Akademik Çıktı Projesi — Plan ve Domain Notları

Bu belge, AVESİS profillerinden Makale, Bildiri, Kitap, Proje ve Patent
kayıtlarının alınarak yıl bazlı Excel raporu üretilmesi için ortak referanstır.
Kod yazımına başlamadan önce doğrulanan kaynak yapısını, veri sözleşmesini ve
kararları kaydeder.

## 1. Amaç ve kapsam

- Girdi: Sistem yöneticisinin önceden tanımladığı hoca kataloğundan seçilen
  hocalar, hedef yıl ve kayıt türü filtreleri.
- Çıktı: Tür bazında ayrılmış, filtrelenebilir bir Excel çalışma kitabı.
- Kapsam: Makale, Bildiri, Kitap, Proje, Patent.
- Varsayım: Bir hocada bir veya daha fazla türün hiç kaydı olmayabilir. Bu
  normal bir sonuçtur; hata değildir.

## 2. Doğrulanan AVESİS kaynak yapısı

Gökhan Dalkılıç profili üzerinden incelendi.

| Kaynak | Liste rotası | Detay rotası | Gözlem |
|---|---|---|---|
| Makale/Bildiri/Kitap | `/{profil}/yayinlar` | `/yayin/{uuid}/{slug}` | Üç tür aynı liste sayfasında, ayrı accordion bölümlerinde yer alır. |
| Proje | `/{profil}/projeler` | `/proje/{uuid}/{slug}` | "Desteklenen Projeler" bölümünde yer alır. |
| Patent | `/{profil}/projeler` | `/fikrimulkiyet/{uuid}/{slug}` | Aynı liste sayfasındaki "Patent" bölümünde yer alır. |

İncelenen yayın listesinde içerik sunucu tarafında HTML içinde hazırdır; açık
bir sayfalama elemanı görülmemiştir. Bölüm rozetleri ile detay bağlantı sayıları
eşleşmiştir: 41 makale, 75 bildiri, 4 kitap. Uygulamada yine de her profil için
liste bağlantı sayısı ile bölüm rozeti karşılaştırılarak doğrulama yapılmalıdır.

### Ortak detay sayfası deseni

- Başlık: `h1.mb-none`
- Görünen kişi listesi: `a.authorsRichText` içeren paragraf
- Kaynakça özeti: `p.mb-xlg`
- Yapılandırılmış alanlar: `li.list-group-item` içindeki `strong` etiket–değer
  çiftleri
- Yayın detaylarında ayrıca `DC.creator`, `DC.date`, `DC.identifier` ve
  bibliyografik meta alanları bulunur. Proje/patent örneklerinde bu meta
  alanları gözlenmediği için HTML görünümüne geri düşen bir yaklaşım gerekir.

## 3. Veri çıkarma yaklaşımı

1. Liste sayfasında bölüm başlığını, her kaydın UUID'sini, başlığını ve detay
   URL'sini topla.
2. Kayıt türünü URL'den değil, liste bölümü ve detaydaki tür alanından doğrula.
3. Tüm detay sayfalarını al; liste satırındaki özet bilgi nihai veri kaynağı
   değildir.
4. Her detay sayfasından ortak alanları ve bütün etiket–değer çiftlerini ham
   olarak kaydet.
5. Kayıt türüne özgü normalleştirici ile Excel satırını üret.

Etiket–değer yaklaşımı sabit alan sırasına bağımlı olmamalıdır. Örneğin
`Cilt numarası:` ve `Sayı:` tek bir liste öğesinde birlikte yer alabilir;
opsiyonel alanlar ise boş değerle değil, HTML'den tamamen çıkarılmış olarak
gelir.

## 4. Excel çalışma kitabı

Bir çalıştırma için tek, kullanıcı odaklı Excel dosyası üretilir. Sayfalar:

- `00_Ozet`
- Seçilmişse `01_Makaleler`
- Seçilmişse `02_Bildiriler`
- Seçilmişse `03_Kitaplar`
- Seçilmişse `04_Projeler`
- Seçilmişse `05_Patentler`

Her ana sayfada ortak, kullanıcıya yarayan kolonlar bulunur:

`Hoca`, `Başlık`, `Kişiler/Yazarlar`, `Yıl`, `AVESİS'te Aç`.

`AVESİS'te Aç`, uzun URL yerine hücrede görünen tıklanabilir bağlantıdır. UUID,
ham kaynak URL'si, çekim zamanı ve ayrıştırma hataları kullanıcı Excel'ine
değil, uygulamanın iç ham kayıtlarına ve loglarına yazılır. Ayrı `Kaynaklar`
veya `Eksikler` sayfası ilk kullanıcı sürümünde yoktur.

`00_Ozet` bir kontrol panelidir ve aşağıdakileri içerir:

- Rapor oluşturma zamanı, zaman filtresi, seçili hoca sayısı ve seçili kayıt
  türleri.
- `Hoca`, `Birim`, her seçili türün kayıt adedi, `Toplam` ve `Tarihi Belirsiz`
  kolonlarından oluşan hoca bazlı özet tablo.
- Kayıt türü bazında toplam adet tablosu.
- Seçilen hocaların ad/birim listesi.

Adetler hoca bazlı rapor satırlarını sayar: seçili iki hoca aynı makalenin
yazarıysa, kayıt her iki hocanın sayısında görünür. Bu, hoca performansını
raporlamak için amaçlanan davranıştır.

Ana sayfalar Excel tablosu biçiminde; filtreli, sabit başlıklı, satır
kaydırmalı ve yıl azalan sıralı olmalıdır. Seçilen türde kayıt bulunmazsa ilgili
sayfa başlık kolonlarıyla boş oluşturulur; seçilmeyen tür için sayfa üretilmez.

Kullanıcı görünümü için kolon sırası:

- Makaleler: `Hoca`, `Yıl`, `Makale Adı`, `Yazarlar`, `Dergi`, `Cilt`, `Sayı`,
  `Sayfalar`, `DOI`, `İndeksler`, `AVESİS'te Aç`.
- Bildiriler: `Hoca`, `Yıl`, `Bildiri Adı`, `Yazarlar`, `Konferans`, `Tarih`,
  `Şehir`, `Ülke`, `Sayfalar`, `DOI`, `AVESİS'te Aç`.
- Kitaplar: `Hoca`, `Yıl`, `Başlık`, `Yazarlar`, `Yayın Türü`, `Yayınevi`,
  `Şehir`, `Sayfalar`, `Editörler`, `AVESİS'te Aç`.
- Projeler: `Hoca`, `Proje Adı`, `Proje Ekibi/Roller`, `Proje Türü`,
  `Destek Programı`, `Destekleyen Kuruluş`, `Başlangıç`, `Bitiş`,
  `AVESİS'te Aç`.
- Patentler: `Hoca`, `Patent Adı`, `Mucitler`, `Tescil No`, `Başvuru Ülkesi`,
  `Başvuru Tarihi`, `Tescil Tarihi`, `Durum`, `AVESİS'te Aç`.

Bir eserin talep edilen birden fazla hocada yer alması mümkündür. İç veri
modelinde eser kaydı ile hoca–eser ilişkisi ayrı tutulur; rapor satırında
`Hoca` kolonu sayesinde ilgili kişinin çıktısında görünür.

## 5. Tür bazlı alan eşlemesi

### Makaleler

| AVESİS kaynağı | Excel kolonu |
|---|---|
| Başlık ve yazarlar | Başlık, Yazarlar |
| `Yayın Türü` | Yayın Türü, Alt Tür |
| `Basım Tarihi` | Basım Tarihi, Yıl |
| `Dergi Adı` | Dergi Adı |
| `Cilt numarası`, `Sayı` | Cilt, Sayı |
| `Sayfa Sayıları` | Sayfa Aralığı, İlk Sayfa, Son Sayfa |
| `Doi Numarası` | DOI |
| `Derginin Tarandığı İndeksler` | Dergi İndeksleri, türetilmiş WoS İndeksi |
| `Anahtar Kelimeler` | Anahtar Kelimeler |
| `Dokuz Eylül Üniversitesi Adresli` | DEÜ Adresli |

Q1–Q4 AVESİS'ten gelmediği için ilk sürümde Q ile ilgili kolonlar Excel'e
eklenmez. Harici kaynakla zenginleştirme bu projenin ilk kapsamı dışındadır.

### Bildiriler

| AVESİS kaynağı | Excel kolonu |
|---|---|
| Başlık ve yazarlar | Başlık, Yazarlar |
| Kaynakça özeti | Konferans Adı, Etkinlik Başlangıç/Bitiş Tarihi, Yıl, Bildiri Türü |
| `Yayın Türü` | Yayın Türü, Alt Tür |
| `Doi Numarası` | DOI |
| `Basıldığı Şehir`, `Basıldığı Ülke` | Şehir, Ülke |
| `Sayfa Sayıları` | Sayfa Aralığı, İlk Sayfa, Son Sayfa |
| `Anahtar Kelimeler` | Anahtar Kelimeler |
| `Dokuz Eylül Üniversitesi Adresli` | DEÜ Adresli |

Konferans adı ve tarihi incelenen detay örneğinde yapılandırılmış alan olarak
değil, kaynakça özetinde bulunur. Bu özet önce ham biçimde korunacak, sonra
Türkçe tarih desteğiyle ayrıştırılacaktır.

### Kitaplar

| AVESİS kaynağı | Excel kolonu |
|---|---|
| Başlık ve yazarlar | Başlık, Yazarlar |
| `Yayın Türü` | Yayın Türü, Alt Tür |
| Kaynakça özeti | Ana Kitap Adı (varsa) |
| `Basım Tarihi` | Basım Tarihi, Yıl |
| `Yayınevi` | Yayınevi |
| `Basıldığı Şehir` | Basım Şehri |
| `Sayfa Sayıları` | Sayfa Aralığı, İlk Sayfa, Son Sayfa |
| `Editörler` | Editörler |
| `Dokuz Eylül Üniversitesi Adresli` | DEÜ Adresli |

Kitap bölümü örneğinde bölüm başlığı doğrudan başlıktır; ana kitap adı yalnızca
kaynakça özetinde geçer. `ISBN` alanı bu örneklerde yoktur, fakat gelecekte
gözlenirse ham alan sözlüğünden Excel'e eklenebilir.

### Projeler

| AVESİS kaynağı | Excel kolonu |
|---|---|
| Başlık ve kişi/rol satırı | Proje Adı, Proje Ekibi/Roller |
| `Proje Türü` | Proje Türü |
| `Destek Programı` | Destek Programı |
| `Başlama Tarihi`, `Bitiş Tarihi` | Başlama Tarihi, Bitiş Tarihi, Başlangıç/Bitiş Yılı |
| Kaynakça özeti | Proje Özet Bilgisi |

İncelenen örnekte doğrudan `Destekleyen Kuruluş` alanı yoktur. Bu nedenle
kolon mevcut olur, ancak kaynakta açıkça yazmıyorsa boş kalır. Örneğin
`TÜBİTAK Projesi` ifadesinden `TÜBİTAK` türetilecekse, bu ayrı ve belgelenmiş
bir normalleştirme kuralı olmalıdır; kaynak alanı gibi sunulmamalıdır.

### Patentler

| AVESİS kaynağı | Excel kolonu |
|---|---|
| Başlık ve kişi listesi | Patent Başlığı, Mucitler |
| Kaynakça özeti | Patent Sınıfı, Tescil No, Tescil Tipi, Özet Yılı |
| `Fikri Mülkiyet` | Fikri Mülkiyet Türü |
| `Başvuru Yapılan Ülke/Kuruluş` | Başvuru Ülkesi/Kuruluşu |
| `Buluşun Durumu` | Buluş Durumu |
| `Başvuru Tarihi` | Başvuru Tarihi |
| `Tescil Tarihi` | Tescil Tarihi, Tescil Yılı |

Patent numarası ve sınıfı incelenen örnekte yapılandırılmış alanlarda değil,
kaynakça özetinde bulunur. Özet metin korunmalı ve bu alanlar ayrıştırılırken
başarısızlık isteğe bağlı `99_Islem_Logu` sayfasına yazılmalıdır.

## 6. Eksik veri ve veri kalitesi kuralları

- Kaynakta bulunmayan opsiyonel alan ana Excel sayfasında boş kalır; `-` metni
  yazılmaz.
- Opsiyonel alanın kaynakta olmaması hata değildir ve işlem günlüğüne yazılmaz.
- Erişilemeyen sayfa, beklenmeyen sayfa yapısı ve ayrıştırılamayan zorunlu alan
  varsa, bunlar isteğe bağlı `99_Islem_Logu` sayfasına yazılır.
- Sayfa aralığı hem kaynak metniyle hem de mümkünse `İlk Sayfa`/`Son Sayfa`
  olarak saklanır.
- DOI, UUID ve tarih gibi değerler normalleştirilir; orijinal değerler ham
  kayıtta korunur.
- Her kayıt için kaynak URL ve çekim zamanı zorunlu denetim bilgisidir.

## 7. Zaman filtresi ve kayıt dahil etme kuralı

Web arayüzünde üç zaman kapsamı bulunur:

- `Tek yıl`: varsayılan seçim; örneğin `2026`.
- `Yıl aralığı`: başlangıç ve bitiş yılı seçilir; iki sınır da dahildir.
- `Tüm yıllar`: tarih filtresi uygulanmaz.

Kayıt türlerine göre tarih seçimi:

- Makale ve kitap: `Basım Tarihi` yılını kullan.
- Bildiri: konferans başlangıç tarihinin yılını kullan.
- Proje: hedef yıl, başlangıç–bitiş tarih aralığıyla kesişirse projeyi dahil et.
- Patent: öncelikle `Tescil Tarihi` yılı; tescil tarihi yoksa başvuru tarihini
  kullan.
- Tek yıl veya yıl aralığı seçildiğinde tarih hiç bulunamazsa kayıt kendi türünün
  ana sayfasına yine eklenir; `Yıl` hücresi boş kalır. Özet sayfasında tarih
  bilgisi olmayan kayıt sayısı ayrı gösterilir.

## 8. Kodlama öncesi ve pilot planı

1. Bu belgeyi gereksinim değiştikçe güncelle.
2. Hoca kataloğunu ad, birim ve doğrulanmış AVESİS profil URL'siyle oluştur.
3. Tek profil için liste toplayıcıyı geliştir ve kayıt sayısını rozetlerle
   karşılaştır.
4. Birer makale, bildiri, kitap, proje ve patent üzerinde detay ayrıştırıcıları
   geliştir.
5. Ham kayıt + normalleştirilmiş kayıt + Excel çıktısını birlikte doğrula.
6. 2026 filtreli tek-hoca pilotu onaylandıktan sonra hoca listesine yay.

## 9. Açık kararlar

- `Destekleyen Kuruluş` için yalnızca açık AVESİS alanı mı kullanılacak, yoksa
  proje türünden türetme kuralı kabul edilecek mi?
- Excel'de yayıncı/yazar/mucit adları AVESİS ekranda nasıl görünüyorsa o
  kısaltmalı biçimde yazılır. Yayın HTML'inde bulunan `DC.creator` meta alanı
  tam ad sağlayabilse de ilk sürümde kullanılmayacaktır.

## 10. Web uygulaması ve dağıtım yaklaşımı

Uygulama tek sayfalı bir rapor oluşturma ekranı olarak çalışır. Hocalar uygulama yöneticisinin
önceden tanımladığı katalogda tutulur; her kayıtta ad, birim ve AVESİS profil
URL'si bulunur. Kullanıcı bu katalogdan arayarak veya filtreleyerek bir ya da
birden fazla hoca seçer, zaman kapsamını ve kayıt türlerini belirler, ardından
Excel raporunu indirir.

Önerilen kullanıcı akışı:

1. Hoca katalogunda ad/birim ile ara; bir veya daha fazla hocayı seç.
2. `Tek yıl`, `Yıl aralığı` veya `Tüm yıllar` zaman kapsamını seç.
3. Makale, Bildiri, Kitap, Proje ve Patent türlerini onay kutularıyla seç;
   `Tümü` varsayılan olarak işaretlidir.
4. "Rapor Oluştur" ile işi başlat; ilerleme ve hata özeti ekranda görünür.
5. İş tamamlanınca, seçilen türleri sayfalar halinde içeren tek Excel dosyasını
   indir.

İlk sürümde filtreler hoca, yıl ve kayıt türüyle sınırlıdır. Dergi indeksi,
proje türü veya yayın alt türü gibi ek filtreler ihtiyaç oluştuğunda eklenir.
Tür başına ayrı Excel dosyası seçeneği ilk sürümde eklenmez; tek indirme ve
özet sayfası kullanıcı için daha anlaşılırdır.

Önerilen ekran yerleşimi:

```text
DEÜ AVESİS Akademik Rapor

[ Hoca ara / birim filtrele ]       Seçilen hocalar (3)
[ çoklu hoca listesi        ]       [ Hoca A ] [ Hoca B ] [ Hoca C ]

Zaman kapsamı:  (•) Tek yıl [2026]  ( ) Yıl aralığı [2024] - [2026]
                ( ) Tüm yıllar

Kayıt türleri:  [✓] Makale  [✓] Bildiri  [✓] Kitap  [✓] Proje  [✓] Patent

                         [ Rapor Oluştur ]

İş durumu / ilerleme                                  [ Excel'i indir ]
```

### Teknoloji seçimi

İlk sürüm için Python önerilir. AVESİS'in HTML ayrıştırması ve Excel üretimi
için Python ekosistemi (`httpx`/`requests`, BeautifulSoup, `openpyxl`) daha
olgun, daha kısa ve doğrulaması daha kolaydır. Web katmanı için FastAPI;
başlangıç arayüzü için Jinja2 + HTMX yeterlidir. React gibi ayrı bir ön yüz
uygulaması ancak daha zengin etkileşim gerektirdiğinde eklenmelidir.

Go teknik olarak kullanılabilir (`goquery`, `excelize`), fakat bu proje için
daha az geliştirme kazancı sağlar. Go, yüksek eşzamanlılık ihtiyacı oluşursa
işçi katmanında yeniden değerlendirilebilir; başlangıç seçimi Python'dır.

### Yerel ve sunucu çalışma biçimi

Kod; profil çözümleme, liste toplama, detay ayrıştırma, normalleştirme, Excel
üretimi ve web katmanı olarak ayrılmalıdır. Böylece aynı çekirdek hem yerelde
hem sunucuda kullanılabilir.

- Yerel geliştirme: FastAPI uygulaması ve SQLite ile çalışır.
- Dağıtım: Docker Compose ile web uygulaması, arka plan işçisi ve Redis iş
  kuyruğu çalışır; kalıcı veriler için PostgreSQL ve çıktı depolaması eklenir.
- Tarama işi HTTP isteği içinde yapılmaz; kuyruktaki işçi tarafından yürütülür.
  Bu, uzun süren raporlarda zaman aşımını önler ve ilerleme bilgisini mümkün
  kılar.
