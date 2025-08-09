# Advanced Indonesian Legal Documents Scraper - Implementation Summary

## Fitur-Fitur Utama yang Diimplementasikan

### 1. **Preservasi Nama File Asli** ✅
- **Prioritas ekstraksi nama file:**
  1. **Content-Disposition header** (prioritas tertinggi)
  2. **Nama file dari URL** 
  3. **Generate dari judul peraturan** (fallback)

- **Sanitasi minimal** untuk menjaga format nama asli
- **Dukungan encoding UTF-8** untuk nama file berbahasa Indonesia
- **Contoh output:** `(PEMBENTUKAN PENGADILAN TINGGI PAPUA BARAT, PENGADILAN TINGGI KEPULAUAN RIAU, PENGADILAN TINGGI SULAWESI BARAT, DAN PENGADILAN TINGGI KALIMANTAN UTARA.pdf)`

### 2. **Struktur Folder Terorganisir** ✅
```
/Peraturan-RI
├── UU
│   ├── 2025
│   │   ├── Nomor 1/
│   │   ├── Nomor 2/
│   │   └── ...
│   ├── 2024
│   │   ├── Nomor 1/
│   │   ├── Nomor 2/
│   │   └── ...
│   └── ...
├── PERPPU
│   ├── 2025/
│   ├── 2024/
│   └── ...
├── PP
├── PERPRES
├── PERMEN
└── ...
```

### 3. **Pencarian Spesifik dengan URL yang Tepat** ✅
- **URL format:** `https://peraturan.go.id/cari?PeraturanSearch%5Btentang%5D=&PeraturanSearch%5Bnomor%5D={nomor}&PeraturanSearch%5Btahun%5D={tahun}&PeraturanSearch%5Bjenis_peraturan_id%5D={jenis}&PeraturanSearch%5Bpemrakarsa_id%5D=&PeraturanSearch%5Bstatus%5D=Berlaku`

- **Parameter pencarian:**
  - `jenis_peraturan_id`: Mapping jenis peraturan ke ID
  - `tahun`: Tahun peraturan
  - `nomor`: Nomor peraturan
  - `status`: **"Berlaku"** (hanya peraturan aktif)

### 4. **Filter Peraturan Berlaku** ✅
- **Hanya mengunduh peraturan dengan status "Berlaku"**
- **Mapping jenis peraturan:**
  - UU = ID "1"
  - PERPPU = ID "2" 
  - PP = ID "3"
  - PERPRES = ID "4"
  - PERMEN = ID "5"
  - PERDA = ID "6"

## Cara Penggunaan

### 1. Script Utama (advanced_peraturan_scraper.py)
```python
async with AdvancedPeraturanScraper() as scraper:
    # Scrape UU tahun 2024
    result = await scraper.scrape_regulations(
        regulation_type="UU",
        year="2024", 
        status="Berlaku",
        max_results=10
    )
```

### 2. Script Praktis (scrape_active_regulations.py)
```bash
# Scrape semua UU tahun 2024
python scrape_active_regulations.py --type UU --year 2024

# Scrape UU nomor 1 tahun 2024
python scrape_active_regulations.py --type UU --year 2024 --number 1

# Scrape komprehensif untuk semua jenis dan tahun terbaru
python scrape_active_regulations.py --comprehensive
```

### 3. Scraping Batch untuk Semua Jenis
```python
result = await scraper.scrape_all_active_regulations(
    years=["2022", "2023", "2024", "2025"],
    regulation_types=["UU", "PERPPU", "PP", "PERPRES", "PERMEN"],
    max_results_per_search=20
)
```

## Konfigurasi (config.json)

### Fitur Baru:
- `"demo_mode": false` - Mengaktifkan download sebenarnya
- `"prioritize_content_disposition": true` - Prioritaskan nama dari server
- `"minimal_filename_cleaning": true` - Sanitasi minimal
- `"active_regulations_only": true` - Hanya peraturan berlaku
- `"skip_existing_files": true` - Skip file yang sudah ada

## Contoh Output

### Nama File yang Dipertahankan:
- ✅ `(PEMBENTUKAN PENGADILAN TINGGI PAPUA BARAT, PENGADILAN TINGGI KEPULAUAN RIAU, PENGADILAN TINGGI SULAWESI BARAT, DAN PENGADILAN TINGGI KALIMANTAN UTARA.pdf)`
- ✅ `UU Nomor 1 Tahun 2024 tentang Perubahan Kedua atas UU Nomor 2 Tahun 2002.pdf`

### Struktur Folder:
```
Peraturan-RI/UU/2024/Nomor 1/
├── (PEMBENTUKAN PENGADILAN TINGGI...).pdf
└── dokumen_pendukung.pdf
```

## Keunggulan Implementasi

1. **Nama file autentik** - Sesuai dengan yang ada di website
2. **Organisasi rapi** - Folder terstruktur berdasarkan jenis/tahun/nomor
3. **Filter akurat** - Hanya peraturan yang masih berlaku
4. **URL pencarian tepat** - Menggunakan endpoint yang benar
5. **Error handling** - Robust dengan retry mechanism
6. **Async/await** - Performa tinggi dengan concurrent downloads
7. **Logging detail** - Monitoring proses yang jelas

## Testing

Jalankan dengan demo mode terlebih dahulu:
```bash
python advanced_peraturan_scraper.py
```

Untuk download sebenarnya, ubah `"demo_mode": false` di config.json
