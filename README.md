# 🏛️ Scraper Peraturan Indonesia Advanced

Scraper canggih untuk mengunduh dokumen peraturan perundang-undangan Indonesia dari peraturan.go.id dengan fitur-fitur terbaru:

## ✨ Fitur Utama

### 🆕 **BARU: Dukungan Direct PDF URL** 
- **Download langsung dari URL PDF**: Mendukung link direct seperti `https://peraturan.go.id/files/uu-no-1-tahun-2025.pdf`
- **Deteksi URL otomatis**: Validasi dan parsing URL direct PDF
- **Multiple download methods**: Single, batch, atau via scraper utama
- **Retry mechanism**: Mechanism percobaan ulang dengan exponential backoff
- **Contoh URL yang didukung**:
  - `https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf`
  - `https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf`
  - `https://peraturan.go.id/files/pp-no-15-tahun-2024.pdf`

### 🎯 Nama File Asli
- **Ekstraksi dari Content-Disposition header**: Mendapatkan nama file asli dari server
- **Prioritas nama asli**: Menggunakan nama dari server dibanding judul HTML  
- **Sanitasi minimal**: Mempertahankan karakter khusus sebanyak mungkin
- **Contoh output**: `PEMBENTUKAN PENGADILAN TINGGI PAPUA BARAT, PENGADILAN TINGGI KEPULAUAN RIAU.pdf`

### 📁 Struktur Folder Terorganisir
```
/Peraturan-RI
├── UU
│   ├── 2025
│   │   ├── Nomor 1
│   │   ├── Nomor 2
│   │   └── ...
│   └── 2024
│       ├── Nomor 1
│       ├── Nomor 2
│       └── ...
├── PERPPU
│   ├── 2025
│   │   ├── Nomor 1
│   │   └── ...
│   └── 2024
│       └── ...
└── [Jenis lainnya...]
```

### 🔍 Filter Pencarian Canggih
- **Jenis peraturan**: UU, PERPPU, PP, PERPRES, dll.
- **Tahun**: Filter berdasarkan tahun terbit
- **Nomor**: Filter berdasarkan nomor peraturan
- **Status**: Berlaku, dicabut, atau semua

### 🎯 Hanya Peraturan Berlaku
Secara default hanya mengunduh peraturan yang masih berlaku (aktif).

## 📋 Jenis Peraturan Yang Didukung

| Kode | Nama Lengkap |
|------|--------------|
| UU | Undang-Undang |
| PERPPU | Peraturan Pemerintah Pengganti Undang-Undang |
| PP | Peraturan Pemerintah |
| PERPRES | Peraturan Presiden |
| PERMEN | Peraturan Menteri |
| PERDA | Peraturan Daerah |
| PERBAN | Peraturan Bank Indonesia |
| TAPMPR | Ketetapan MPR |
| PERMENKUMHAM | Peraturan Menteri Hukum dan HAM |

## 🚀 Cara Penggunaan

### 🆕 **BARU: Download Direct PDF URL**

#### Download Single URL
```python
from advanced_peraturan_scraper import AdvancedPeraturanScraper

async with AdvancedPeraturanScraper() as scraper:
    result = await scraper.download_direct_pdf(
        "https://peraturan.go.id/files/uu-no-1-tahun-2025.pdf"
    )
```

#### Download Multiple URLs
```python
urls = [
    "https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf",
    "https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf",
    "https://peraturan.go.id/files/pp-no-15-tahun-2024.pdf"
]

async with AdvancedPeraturanScraper() as scraper:
    result = await scraper.download_from_direct_urls(urls)
```

#### Via Main Scraper Method
```python
async with AdvancedPeraturanScraper() as scraper:
    result = await scraper.scrape_regulations(direct_urls=urls)
```

#### Standalone Function
```python
from advanced_peraturan_scraper import download_direct_pdfs

result = await download_direct_pdfs(urls)
```

### 1. Mode Interaktif (Rekomendasi untuk Pemula)
```bash
python quick_start_advanced.py
```
Program akan memandu Anda step-by-step untuk memilih:
- Jenis peraturan
- Filter tahun
- Filter nomor
- Status peraturan

### 2. Command Line (Untuk Pengguna Lanjut)

#### Download semua UU
```bash
python quick_start_advanced.py UU
```

#### Download UU tahun 2024
```bash
python quick_start_advanced.py UU 2024
```

#### Download UU No. 5 Tahun 2024
```bash
python quick_start_advanced.py UU 2024 5
```

#### Download semua UU 2024 yang berlaku
```bash
python quick_start_advanced.py UU 2024 all berlaku
```

### 3. Mode Comprehensive (Semua Jenis)

#### Download semua jenis peraturan
```bash
python run_all_advanced.py
```

#### Download semua jenis tahun 2024
```bash
python run_all_advanced.py 2024
```

#### Download jenis tertentu
```bash
python run_all_advanced.py UU PERPPU PP
```

### 4. Mode Demo (Testing)
```bash
python quick_start_advanced.py demo
python run_all_advanced.py demo
```

## 🛠️ Setup dan Instalasi

### 1. Clone Repository
```bash
git clone [repository-url]
cd UU-RI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Scraper
```bash
python quick_start_advanced.py
```

## 📖 Contoh Penggunaan

### Contoh 1: Download UU Terbaru
```bash
# Mode interaktif
python quick_start_advanced.py

# Pilih: 1 (UU)
# Tahun: 2024
# Nomor: [Enter untuk semua]
# Status: 1 (Berlaku)
```

### Contoh 2: Download Perpres Spesifik
```bash
python quick_start_advanced.py PERPRES 2024 15
```

### Contoh 3: Download Batch Multiple Jenis
```bash
python quick_start_advanced.py batch
# Input tahun: 2024
```

### Contoh 4: Download Comprehensive
```bash
python run_all_advanced.py 2024 berlaku
```

## 🔧 Fitur Lanjutan

### 🆕 Direct PDF URL Support
```python
from advanced_peraturan_scraper import AdvancedPeraturanScraper

async with AdvancedPeraturanScraper() as scraper:
    # Validasi URL
    is_valid = scraper.is_direct_pdf_url("https://peraturan.go.id/files/uu-no-1-tahun-2025.pdf")
    
    # Ekstrak info peraturan dari URL
    info = scraper.parse_regulation_info_from_url(url)
    # Returns: {'type': 'UU', 'year': '2025', 'number': '1', 'filename': '...'}
    
    # Ekstrak nama file yang bersih
    filename = scraper.extract_filename_from_url(url)
    # Returns: "UU No. 1 Tahun 2025.pdf"
```

### Penggunaan Langsung dalam Kode Python
```python
from advanced_peraturan_scraper import run_advanced_scraper

# Download UU tahun 2024
await run_advanced_scraper(
    regulation_type="UU",
    year_filter="2024",
    status_filter="berlaku"
)
```

### Filter Status
- `berlaku`: Hanya peraturan yang masih aktif (default)
- `dicabut`: Hanya peraturan yang telah dicabut
- `all`: Semua peraturan tanpa filter status

## 📊 Log dan Monitoring

Setiap scraper menghasilkan file log:
- `uu_advanced_scraper.log`
- `perppu_advanced_scraper.log`
- dll.

Log mencakup:
- Progress download
- Error handling
- Statistik akhir
- URL yang bermasalah

## 🛡️ Error Handling

### Retry Mechanism
- 3x retry untuk setiap download
- Progressive backoff delay
- Graceful error handling

### File Handling
- Skip file yang sudah ada
- Validasi nama file
- Penanganan karakter khusus

### Network Issues
- Timeout handling
- Connection pooling
- Rate limiting

## 💡 Tips dan Best Practices

### 1. Download Efisien
- Gunakan filter tahun untuk mengurangi volume
- Download satu jenis dulu untuk testing
- Gunakan mode demo untuk testing konfigurasi

### 2. Pengelolaan Storage
- Monitor space disk (file PDF bisa besar)
- Backup folder hasil secara berkala
- Gunakan external storage untuk archive

### 3. Network Considerations
- Gunakan koneksi internet yang stabil
- Avoid peak hours untuk download besar
- Consider bandwidth usage

## 🔍 Troubleshooting

### 🆕 **Direct PDF URL Issues**
```bash
# Test URL validation
python test_direct_urls.py

# Run usage examples  
python direct_url_examples.py

# Check if URL is valid direct PDF
python -c "
from advanced_peraturan_scraper import AdvancedPeraturanScraper
scraper = AdvancedPeraturanScraper()
print(scraper.is_direct_pdf_url('https://peraturan.go.id/files/uu-no-1-tahun-2025.pdf'))
"
```

### Issue: "Connection timeout"
```bash
# Coba mode demo dulu
python quick_start_advanced.py demo

# Atau kurangi concurrent downloads
# Edit max_concurrent di advanced_peraturan_scraper.py
```

### Issue: "File permission error"
```bash
# Pastikan permission folder
chmod 755 ./Peraturan-RI

# Atau ganti base directory di kode
```

### Issue: "Too many requests"
```bash
# Tunggu beberapa menit lalu coba lagi
# Atau gunakan delay yang lebih besar
```

## 📈 Performance

### Benchmarks
- ~50-100 files per menit (tergantung ukuran file)
- Concurrent downloads: 5 (default)
- Memory usage: ~100-200MB

### Optimization
- Adjust `max_concurrent` untuk koneksi lebih cepat
- Gunakan SSD untuk storage yang lebih cepat
- Filter spesifik untuk mengurangi volume

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Create pull request

## 📝 License

[Sesuai LICENSE file]

## 🆘 Support

- Create issue di GitHub
- Check existing issues dulu
- Sertakan log file untuk debugging

---

**Happy scraping! 🎉**

> **Catatan**: Gunakan scraper ini dengan bijak dan hormati terms of service dari peraturan.go.id
