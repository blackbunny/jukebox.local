# Müzik Paylaştıkça Güzelleşir! Yerel Ağ Odaklı Kolektif Müzik Kutusu "Jukebox.Local" Duyuruldu

**Tarih:** 1 Temmuz 2026  
**Konum:** Açık Kaynak Topluluğu  
**Proje Bağlantısı:** [LocalRadio Proje Dizini](https://github.com/blackbunny/jukebox.local)

---

### Ortak Alanlarda Müzik Kargaşasına Son: Karşınızda Jukebox.Local!

Ev partilerinde, ofislerde, hacker alanlarında veya ortak yaşam alanlarında müzik kontrolü her zaman bir sorun olmuştur. "Aux kablosunu bana uzat", "Şu şarkıyı açar mısın?", "Kimin şarkısı çalıyor?" veya birinin sıradaki tüm şarkıları silip kendi listesini dayatması gibi tat kaçıran durumlar artık geride kalıyor. 

Geliştiriciler ve müzikseverler için tamamen açık kaynaklı olarak geliştirilen **Jukebox.Local**, aynı yerel ağa bağlı herkesin ortaklaşa müzik kuyruğu oluşturabildiği, modern, minimalist ve bağımsız bir kolektif müzik kutusudur (jukebox).

#### Jukebox.Local Nedir ve Nasıl Çalışır?

Jukebox.Local, sunucu rolünü üstlenen bir bilgisayarda (örneğin bir ev sunucusu, eski bir dizüstü bilgisayar veya bir Raspberry Pi) çalışır ve sesi doğrudan bu makinenin hoparlörlerinden verir. Aynı Wi-Fi/yerel ağa bağlı olan diğer kullanıcılar ise herhangi bir uygulama indirmeden, sadece tarayıcılarından sunucunun IP adresine bağlanarak müzik kuyruğuna şarkı ekleyebilir, çalan şarkıyı görebilir, şarkıyı geçebilir ve ses düzeyini kontrol edebilir.

---

### Öne Çıkan Teknolojik Özellikler

*   **Gerçek Zamanlı WebSocket Senkronizasyonu:** Tüm bağlı cihazlar, çalan şarkının durumunu, ilerleme çubuğunu ve yaklaşan şarkı sırasını gecikmesiz (real-time) olarak eş zamanlı görür.
*   **Adil ve Trollemesiz Kuyruk Yönetimi (Sahiplik Kontrolü):** Sisteme eklenen her şarkı, ekleyen kullanıcının yerel ağ IP'si ile etiketlenir. Kullanıcılar yalnızca kendi ekledikleri şarkıları listeden silebilirler. Başkalarının eklediği şarkıları silemez veya sırayı sabote edemezler.
*   **YouTube Entegrasyonu ve Kolay Arama:** YouTube linklerini doğrudan yapıştırarak veya arayüzdeki arama çubuğunu kullanarak anında şarkı aratıp sıraya ekleyebilirsiniz. Arka planda `yt-dlp` motoru sayesinde şarkıların ses akışları dinamik olarak çekilir.
*   **Kesintisiz Müzik Deneyimi (Seeding & Fallback):** Sıra boşaldığında müzik susmaz! Önceden tanımlanmış varsayılan bir çalma listesinden rastgele şarkılar seçilerek arka planda kesintisiz müzik çalınmaya devam eder. Birisi şarkı eklediğinde ise otomatik olarak kullanıcı kuyruğuna geçiş yapılır.
*   **Ortak Ses Kontrolü:** Ağdaki her kullanıcı müzik sesini tarayıcı üzerinden ayarlayabilir. Değişiklikler anlık olarak tüm dinleyicilere yansıtılır.
*   **Göz Alıcı Minimalist Tasarım (Japanese "Ma" Felsefesi):** Arayüz, Japon estetiğindeki boşluk ve sadelik odaklı "Ma" felsefesinden ilham alan minimalist, koyu tema (dark mode) ve yumuşak ambiyans geçişlerine sahip modern bir SPA (Single Page Application) olarak tasarlanmıştır.
*   **Geliştirici Dostu Altyapı ve Mock Modu:** Sunucu bilgisayarda fiziksel olarak VLC veya ses kartı bulunmasa bile, "Mock Player" modu sayesinde sistem oynatmayı simüle eder. Bu sayede kod geliştirme ve test süreçleri her ortamda sorunsuz yürütülebilir.

---

### Güçlü ve Modern Teknoloji Yığını

*   **Backend:** Python, FastAPI (Hızlı ve asenkron API altyapısı), Pydantic Settings (Kolay yapılandırma yönetimi)
*   **Ses Motoru:** VLC (`python-vlc` kütüphanesi) ve akış ayıklama için `yt-dlp`
*   **Frontend:** HTML5, Vanilla JavaScript, Tailwind CSS (Görsel şölen sunan minimalist arayüz), Lucide Icons
*   **Dağıtım:** Docker desteği (Ses cihazı yönlendirmesi `--device /dev/snd` ile konteyner içinde native çalıştırma kolaylığı)

---

### Kurulum ve Çalıştırma

Proje hem yerel olarak Python ortamında hem de Docker konteyneri olarak saniyeler içinde ayağa kaldırılabilir:

#### Yöntem 1: Yerel Kurulum (Linux/macOS)

1. Sistem bağımlılıklarını kurun:
   ```bash
   sudo apt update && sudo apt install -y vlc ffmpeg
   ```
2. Bağımlılıkları yükleyin ve çalıştırın:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```
3. Tarayıcınızdan `http://localhost:3030` adresine gidin!

#### Yöntem 2: Docker ile Hızlı Başlangıç

Sistem hoparlörlerine erişim yetkisiyle Docker üzerinde çalıştırmak için:
```bash
docker build -t jukebox-local .
docker run -d --name jukebox -p 3030:3030 --device /dev/snd --restart unless-stopped jukebox-local
```

---

### Projenin Geleceği ve Açık Kaynağa Davet

Jukebox.Local tamamen açık kaynak kodlu ve topluluk katkılarına açık bir projedir. Gelecek yol haritasında akıllı duraklatma mekanizmaları, gelişmiş çalma listesi yönetimleri ve farklı platform destekleri yer alıyor. 

Eğer siz de kendi evinizde, ofisinizde veya arkadaş ortamınızda demokratik ve keyifli bir müzik deneyimi yaşatmak istiyorsanız, projeyi inceleyebilir, yıldızlayabilir ve geliştirmelere katkı sunabilirsiniz!

**Proje Kaynak Kodları:** [LocalRadio Github](https://github.com/blackbunny/jukebox.local )
