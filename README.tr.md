<div align="center">

# EFPSE Köprü

**Easy FPS Editor CE projelerini komut satırından yönet.**
Editör penceresini açmadan her proje ayarını editörün kendi koduyla oku ve yaz, haritaları yazı olarak düzenle, varlık içe aktar, denetle, ekran görüntüsü al, paketle.

[![CI](https://github.com/blgymtr/gz-bridge-app/actions/workflows/ci.yml/badge.svg)](https://github.com/blgymtr/gz-bridge-app/actions/workflows/ci.yml)
[![Lisans: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English](README.md) · [Deutsch](README.de.md) · **Türkçe**

</div>

## Neden

Easy FPS Editor'de birçok seçenek onay kutularının ve panellerin arkasında durur: model bayrakları, silah ve düşman alanları, harita özellikleri. Bunlar elle okunması ve değiştirilmesi zor, betikle hiç yönetilemeyen ikili proje dosyalarında saklanır. EFPSE Köprü arka planda **senin kurulu editörünü** yükler, projeyi onun kendi sınıflarıyla açıp kaydeder ve her şeyi düz JSON ve yazı olarak verir. Böylece ayarlar görünür, karşılaştırılabilir ve betiklenebilir olur; hem insanlar hem yapay zekâ asistanları için.

## Özellikler

- **Her alan, okuma ve yazma.** `al` bir silahın, düşmanın, dekorun, haritanın, dokunun, modelin, animasyonun, canın, zırhın ya da karonun tüm alanlarını, ayrıca `game`, `player` ve `hud` ayarlarını gösterir. `ayarla` dizi öğeleri dahil (`frames[2]=5`) her alanı değiştirir.
- **Ekle, sil, sırala.** Yeni kayıt, silme ve silah tuş sırası.
- **Yazı olarak harita.** `harita` bir katı ASCII ızgara olarak çizer (duvar, oyuncu, düşman, silah, ışık, anahtar). `kare`, `varlik` ve `degistirici` 9 katın herhangi birine doku, varlık (oyuncu, düşman, silah, dekor, mermi, anahtar, can, zırh, ışık) ve değiştirici (kapı, çıkış, basamak, tehlike, engel, tetik, terminal) koyar. `harita-yeni` boş 64x64 harita açar.
- **İçe aktarma.** Klasörden silah, düşman ve dekor (sprite, ses, durumlar), doku, MD3 model ve dokuları.
- **MD3 araçları.** Kare, yüzey, üçgen ve köşe sayıları; oyunu açmadan istenen karelerin önizleme sayfası.
- **Denetim.** `kontrol` eksik dosyaları, kırık bağlantıları, el kitabında olmayan FSM komutlarını ve diğer hataları arar; hata varsa sıfırdan farklı çıkış verir (CI'a uygun).
- **Çalıştır ve yakala.** Editörü aç, oyunu bir haritada başlat ya da tuş senaryosu oynatıp (`W:200,LMB:40,WAIT:500,SHOT`) ekran görüntüsü al.
- **Paketle.** Oyunun dağıtılabilir klasörünü hazırlar.
- **Varsayılan olarak güvenli.** Her yazma önce `kopru_yedek/` altına zaman damgalı yedek alır. Editör açıkken yazma reddedilir, ikisi aynı dosyalar için çekişmez.
- **Komut satırında iki dil.** Komutlar ve seçenekler Türkçe ve İngilizce çalışır (`al`/`get`, `--proje`/`--project`).

## Gerekenler

- Windows 10 veya 11
- Easy FPS Editor CE **v1.10.5** (kendi kurulumun; depoda yok)
- Python 3.9 veya üstü. MD3 komutları için `numpy`, `onizle` için `opencv-python`. Gerisi standart kütüphane
- Windows PowerShell 5.1 (Windows ile gelir). Köprü editörü yüklemek için 32 bit sürümünü başlatır

## Hızlı başlangıç

```powershell
git clone https://github.com/blgymtr/gz-bridge-app.git
cd gz-bridge-app
$env:EFPSE_MOTOR = 'C:\Oyunlar\EasyFPSEditor_CE_V1.10.5'   # EasyFPSEditor_CE.exe'nin klasörü
$env:EFPSE_PROJE = 'Oyunum'                               # Projects\ altındaki klasör adı
python kopru.py projeler
python kopru.py bilgi
python kopru.py kontrol
```

Seçenekler doğrudan da verilir: `python kopru.py --motor <klasör> --proje <ad> <komut> ...`

## Komutlar

| Komut | Ne yapar |
|---|---|
| `projeler` | Motor klasöründeki projeler |
| `bilgi` | Silahlar, düşmanlar, dekorlar, haritalar, doku ve model sayısı, oyun adı |
| `liste <koleksiyon>` | Koleksiyondaki adlar: `enemies decorations weapons maps textures models animations hps armours tiles` |
| `al <koleksiyon> [ad\|sıra]` | Tüm alanlar JSON olarak. `game`, `player`, `hud` da olur |
| `ayarla <koleksiyon> <ad> alan=değer ...` | Alan değiştir. `game`, `player`, `hud` için ad yazılmaz |
| `ekle <koleksiyon> alan=değer ...` | Yeni kayıt |
| `sil <koleksiyon> <ad>` | Kayıt sil |
| `sirala <koleksiyon> <ad> <ad> ...` | Bu adları başa dizer (silah tuş sırası) |
| `kaydet` | Editörün kendi biçiminde yeniden kaydet |
| `harita <ad> [--kat N]` | Katı yazı olarak çiz |
| `kare <harita> <doku\|boş> x y [x2 y2] [--kat N]` | Kare ya da dikdörtgen boya |
| `varlik <harita> <tür> x y [--sira N] [--kat N]` | Varlık koy: `player enemy weapon deco ammo key1-3 hp1-4 arm1-4 light1-6 yok` |
| `degistirici <harita> <tür> x y [--kat N]` | Değiştirici koy: `door door1-3 exit step1-3 hazard invisible barrier trigger1-10 terminal1-10 yok` |
| `harita-yeni <ad>` | Boş harita, projeye eklenir |
| `silah-al <ad> <klasör>` | Silah içe aktar (sprite, ses, durumlar) |
| `dusman-al <ad> <klasör>` | Düşman içe aktar |
| `dekor-al <ad> <klasör>` | Dekor içe aktar |
| `doku-al <png> [tür]` | Doku içe aktar (tür 2 = duvar) |
| `model-al <ad> <klasör> [tür]` | MD3 ve dokuları (tür 1 dekor, 2 düşman) |
| `md3 <ad>` | Kare, yüzey, üçgen, köşe sayıları |
| `onizle <ad> <çıktı.png> [kare ...]` | Model karelerini oyunu açmadan PNG'ye çiz |
| `kontrol` | Tüm denetimler, hatada sıfırdan farklı çıkış |
| `yedek` | Şimdi yedekle |
| `editor` | Editörü aç |
| `oyna [--map N]` | Oyunu bir haritada başlat |
| `foto <çıktı.png> [--bekle sn] [--tus "..."]` | Oyunu aç, tuş senaryosunu oynat, ekran görüntüsü al |
| `paket` | Oyunu paketle |

`foto` için tuş senaryosu: virgülle ayrılmış adımlar. `TUŞ:ms` tuşu basılı tutar, `LMB:ms` / `RMB:ms` tıklar, `WAIT:ms` bekler, `SHOT` görüntü alır.

### Örnekler

```powershell
python kopru.py al weapons Shotgun
python kopru.py ayarla enemies Imp health=120 speed=3.5
python kopru.py ayarla game name="Gece Vardiyası"
python kopru.py harita E1M1 --kat 0
python kopru.py kare E1M1 brick.png 10 10 20 10
python kopru.py varlik E1M1 enemy 15 12 --sira 2
python kopru.py degistirici E1M1 door 15 9
python kopru.py model-al Varil .\modeller\varil 1
python kopru.py onizle Varil varil.png 0 4 8
python kopru.py foto test.png --bekle 6 --tus "W:400,LMB:60,WAIT:300,SHOT"
```

## Dosyalar

| Dosya | Görevi |
|---|---|
| `kopru.py` | Komutlar, harita okuma ve yazma, içe aktarma, denetim, MD3, paket |
| `host.ps1` | Editörün sınıflarını 32 bit PowerShell'de yükler, okur ya da değişiklikleri uygular |
| `foto.ps1` | Oyunu açar, tuş senaryosunu oynatır, pencereyi yakalar |
| `test_kopru.py` | Yazma komutlarını projenin geçici kopyasında dener |

## Test

```powershell
python test_kopru.py <motor klasörü> <proje>
```

Test projeyi `Projects\KopruTest` altına kopyalar, yazma komutlarını orada çalıştırır ve sonuçları denetler. Senin projene dokunulmaz.

## Nasıl çalışır

`host.ps1` 32 bit Windows PowerShell'de başlar, `EasyFPSEditor_CE.exe`'yi .NET derlemesi olarak yükler ve projeyi editörün kendi kaynak sınıflarıyla açar. Açık alanlar JSON'a çevrilir. `kopru.py`'den gelen değişiklikler küçük bir işlem listesi olarak (`set`, `add`, `del`, `order`) aynı sınıflarla kaydedilir; dosyalar editörün beklediği biçimde kalır. Haritalar doğrudan okunup yazılır (64x64 ızgara, 9 kat, beş katman).

## Sınırlar

- Yalnız Easy FPS Editor CE v1.10.5 ile denendi. Başka sürümlerde alan adları değişebilir.
- `foto` oyun penceresinin ekrandaki alanını yakalar; pencere kısa süre en üstte kalır.
- Easy FPS Editor'ün yapımcılarıyla bağlantısı ya da onayı yoktur. Editörün hiçbir parçası depoda yoktur; köprü senin kurulu kopyanı kullanır.

## Güvenlik

[SECURITY.md](SECURITY.md) dosyasına bak. Köprü hiçbir ağ bağlantısı kurmaz.

## Lisans

[MIT](LICENSE)
