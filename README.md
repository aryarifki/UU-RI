# 🏛️ Complete Peraturan Indonesia PDF Downloader

Downloader lengkap untuk mengunduh **SEMUA file PDF** dari peraturan.go.id dalam sekali eksekusi dengan mempertahankan nama file asli.

## ✨ Fitur Utama

### 🎯 Download Semua PDF
- **Crawling komprehensif**: Menjelajahi seluruh website untuk menemukan semua PDF
- **Multi-kategori**: Mendukung semua jenis peraturan (UU, PP, PERPRES, PERMEN, dll.)
- **Multi-tahun**: Download dari tahun 1945 hingga sekarang
- **Nama file asli**: Preservasi nama file dari Content-Disposition header server
- **Zero manual intervention**: Sekali klik untuk download ribuan PDF

### 📁 Struktur Folder Terorganisir Otomatis
```
/Peraturan-RI-Complete
├── UU
│   ├── 2025
│   │   ├── Nomor 1
│   │   │   └── UU_No_1_Tahun_2025_Tentang_....pdf
│   │   ├── Nomor 2
│   │   └── ...
│   └── 2024
│       ├── Nomor 1
│       ├── Nomor 2
│       └── ...
├── PERPPU
├── PP
├── PERPRES
├── PERMEN
└── [Semua jenis lainnya...]
```

### 🔍 Intelligent Discovery System
- **Website crawling**: Otomatis menemukan semua halaman peraturan
- **Pagination following**: Mengikuti semua halaman hasil pencarian
- **Multiple search strategies**: Pencarian berdasarkan kategori, tahun, dan alfabetis
- **Sitemap parsing**: Memanfaatkan sitemap untuk discovery URL
- **Deep link extraction**: Mencari semua link PDF di setiap halaman

### 🛡️ Robust Download System
- **Retry mechanism**: 3x retry otomatis untuk download yang gagal
- **Concurrent downloads**: Download multiple file secara bersamaan
- **Progress monitoring**: Real-time progress dan logging lengkap
- **Duplicate prevention**: Skip file yang sudah ada
- **Error handling**: Graceful handling untuk berbagai error

## 🚀 Cara Penggunaan

### 1. Quick Start - Download Semua PDF

```bash
# Setup environment
pip install -r requirements.txt

# Download SEMUA PDF dari peraturan.go.id
python download_all_pdfs.py --all
```

**PERINGATAN**: Ini akan mendownload ribuan file PDF dan membutuhkan waktu berjam-jam!

### 2. Download Selektif

#### Download berdasarkan jenis peraturan:
```bash
# Download semua UU, PP, dan PERPRES
python download_all_pdfs.py --types UU PP PERPRES

# Download hanya UU
python download_all_pdfs.py --types UU
```

#### Download berdasarkan tahun:
```bash
# Download semua PDF tahun 2023-2025
python download_all_pdfs.py --years 2023 2024 2025

# Download tahun tertentu saja
python download_all_pdfs.py --years 2024
```

#### Kombinasi jenis dan tahun:
```bash
# Download UU dan PERPPU untuk tahun 2023-2024
python download_all_pdfs.py --types UU PERPPU --years 2023 2024
```

### 3. Download Peraturan Terbaru
```bash
# Download peraturan dari 30 hari terakhir
python download_all_pdfs.py --recent 30

# Download peraturan dari 7 hari terakhir
python download_all_pdfs.py --recent 7
```

### 4. Mode Demo (Testing)
```bash
# Test tanpa download aktual
python download_all_pdfs.py --demo --types UU --years 2024
```

### 5. Konfigurasi Lanjutan
```bash
# Custom concurrent downloads dan delay
python download_all_pdfs.py --types UU \
    --concurrent 20 \
    --delay 0.5 \
    --retry 5 \
    --output "/path/to/custom/dir"
```

## 📊 Monitoring & Logging

### Real-time Progress
Script akan menampilkan progress real-time:
```
🚀 Memulai download SEMUA PDF dari peraturan.go.id...
Step 1: Discovering all regulation pages...
Discovered 15,847 regulation pages
Step 2: Extracting all PDF links...
Found total 23,456 PDF links
Step 3: Downloading all PDFs...
Downloaded batch 1/2346
```

### Log Files
- `peraturan_scraper.log`: Log detail semua aktivitas
- `download_summary_YYYYMMDD_HHMMSS.json`: Summary hasil download

### Statistics
Setelah selesai, akan ditampilkan statistik lengkap:
```
✅ DOWNLOAD SELESAI!
📊 STATISTIK:
   📄 Halaman peraturan ditemukan: 15,847
   🔗 Link PDF ditemukan: 23,456
   ✅ PDF berhasil didownload: 22,103
   ❌ Error: 1,353
   ⏱️  Durasi: 4h 32m 18.5s
   📁 Lokasi file: Peraturan-RI-Complete
```

## 🛠️ Instalasi & Setup

### 1. Clone Repository
```bash
git clone [repository-url]
cd UU-RI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi (Opsional)
Edit `config.json` untuk menyesuaikan:
- Folder output
- Jumlah concurrent downloads
- Delay antar request
- Retry attempts

### 4. Jalankan Downloader
```bash
python download_all_pdfs.py --usage  # Lihat semua opsi
python download_all_pdfs.py --all    # Start download
```

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
| PERMENDAGRI | Peraturan Menteri Dalam Negeri |
| PERMENKEU | Peraturan Menteri Keuangan |
| PERMENKES | Peraturan Menteri Kesehatan |
| PERMENDIKBUD | Peraturan Menteri Pendidikan dan Kebudayaan |
| PERMENAKER | Peraturan Menteri Ketenagakerjaan |
| PERMENAG | Peraturan Menteri Agama |

## 🔧 Konfigurasi Lanjutan

### Performance Tuning
```bash
# High-speed configuration (requires good connection)
--concurrent 25 --delay 0.3

# Conservative configuration (slow connection)
--concurrent 5 --delay 2.0

# Balanced configuration (default)
--concurrent 15 --delay 0.8
```

### Storage Considerations
- **Perkiraan ukuran**: 50GB - 200GB+ untuk semua PDF
- **Format file**: PDF, DOC, DOCX
- **Struktur**: Terorganisir dalam folder hierarki

## 💡 Tips & Best Practices

### 1. Storage Management
```bash
# Check available space before download
df -h

# Monitor space during download
watch -n 30 "du -sh Peraturan-RI-Complete"
```

### 2. Network Considerations
- Gunakan koneksi internet yang stabil
- Hindari jam sibuk untuk download besar
- Pertimbangkan bandwidth usage

### 3. System Resource
- RAM: Minimum 4GB, recommended 8GB+
- CPU: Multi-core recommended untuk concurrent downloads
- Storage: SSD recommended untuk performance optimal

### 4. Resuming Downloads
```bash
# Jika download terputus, jalankan kembali dengan opsi yang sama
# Script akan skip file yang sudah ada dan melanjutkan download
python download_all_pdfs.py --types UU PERPPU --years 2024
```

## 🛡️ Error Handling & Troubleshooting

### Common Issues

#### 1. Connection Timeout
```bash
# Gunakan delay yang lebih besar
python download_all_pdfs.py --all --delay 2.0 --concurrent 5
```

#### 2. Memory Issues
```bash
# Kurangi concurrent downloads
python download_all_pdfs.py --all --concurrent 3
```

#### 3. Storage Full
```bash
# Gunakan external storage
python download_all_pdfs.py --all --output "/external/drive/peraturan"
```

#### 4. Permission Issues
```bash
# Fix permissions
chmod 755 -R Peraturan-RI-Complete
```

### Log Analysis
```bash
# Check error patterns in log
grep "ERROR" peraturan_scraper.log

# Count successful downloads
grep "Successfully downloaded" peraturan_scraper.log | wc -l
```

## 📈 Performance Benchmarks

### Typical Performance
- **Discovery**: ~2,000 pages per menit
- **PDF extraction**: ~500 PDFs per menit  
- **Downloads**: ~50-200 files per menit (tergantung ukuran)
- **Total duration**: 2-8 jam untuk complete download

### Optimization
- **SSD vs HDD**: 2-3x faster dengan SSD
- **Fast internet**: Linear scaling dengan bandwidth
- **CPU cores**: Marginal improvement dengan >4 cores

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Test dengan mode demo
4. Submit pull request

## 📝 License

[Sesuai LICENSE file]

## 🆘 Support & Issues

- **Bug reports**: Create GitHub issue dengan log file
- **Feature requests**: Diskusi di GitHub discussions
- **Performance issues**: Include system specs dan config

## ⚠️ Disclaimer

- Gunakan dengan bijak dan hormati terms of service peraturan.go.id
- Download dalam jumlah besar dapat mempengaruhi server
- Pastikan memiliki storage dan bandwidth yang cukup
- Script ini untuk tujuan penelitian dan archival

---

**Happy downloading! 🎉**

> **Catatan**: Tool ini dibuat untuk membantu akses publik terhadap peraturan perundang-undangan Indonesia. Gunakan dengan bertanggung jawab.

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
