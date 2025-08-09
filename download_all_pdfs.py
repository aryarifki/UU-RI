#!/usr/bin/env python3
"""
Script untuk mendownload SEMUA file PDF dari peraturan.go.id
dalam sekali eksekusi dengan nama file asli
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from advanced_peraturan_scraper import CompletePeraturanScraper, download_by_regulation_type, download_recent_regulations

def print_banner():
    """Print welcome banner"""
    print("=" * 80)
    print("🏛️  COMPLETE PERATURAN.GO.ID PDF DOWNLOADER")
    print("=" * 80)
    print("📥 Download SEMUA file PDF dari website peraturan.go.id")
    print("🎯 Mempertahankan nama file asli dari server")
    print("📁 Struktur folder terorganisir otomatis")
    print("🔄 Retry mechanism untuk download yang gagal")
    print("📊 Progress monitoring dan logging lengkap")
    print("=" * 80)
    print()

def print_usage():
    """Print usage examples"""
    print("📖 CARA PENGGUNAAN:")
    print()
    print("1️⃣  Download SEMUA PDF (mode lengkap):")
    print("   python download_all_pdfs.py --all")
    print()
    print("2️⃣  Download berdasarkan jenis peraturan:")
    print("   python download_all_pdfs.py --types UU PP PERPRES")
    print()
    print("3️⃣  Download berdasarkan tahun:")
    print("   python download_all_pdfs.py --years 2023 2024 2025")
    print()
    print("4️⃣  Download berdasarkan jenis DAN tahun:")
    print("   python download_all_pdfs.py --types UU PERPPU --years 2023 2024")
    print()
    print("5️⃣  Download peraturan terbaru (30 hari terakhir):")
    print("   python download_all_pdfs.py --recent 30")
    print()
    print("6️⃣  Mode demo (tidak download aktual):")
    print("   python download_all_pdfs.py --demo --types UU --years 2024")
    print()
    print("🔧 OPSI LANJUTAN:")
    print("   --concurrent N    : Jumlah download simultan (default: 10)")
    print("   --delay N         : Delay antar request dalam detik (default: 1.0)")
    print("   --retry N         : Jumlah retry untuk download gagal (default: 3)")
    print("   --output DIR      : Direktori output (default: Peraturan-RI-Complete)")
    print()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Download semua file PDF dari peraturan.go.id",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--all', action='store_true', 
                           help='Download SEMUA PDF dari seluruh website')
    mode_group.add_argument('--types', nargs='+', 
                           choices=['UU', 'PERPPU', 'PP', 'PERPRES', 'PERMEN', 'PERDA', 
                                   'PERBAN', 'TAPMPR', 'PERMENKUMHAM', 'PERMENDAGRI',
                                   'PERMENKEU', 'PERMENKES', 'PERMENDIKBUD', 'PERMENAKER', 'PERMENAG'],
                           help='Jenis peraturan yang akan didownload')
    mode_group.add_argument('--recent', type=int, metavar='DAYS',
                           help='Download peraturan dari N hari terakhir')
    
    # Filter options
    parser.add_argument('--years', nargs='+', type=str,
                       help='Tahun peraturan yang akan didownload (contoh: 2023 2024 2025)')
    
    # Configuration options
    parser.add_argument('--concurrent', type=int, default=10,
                       help='Jumlah download simultan (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay antar request dalam detik (default: 1.0)')
    parser.add_argument('--retry', type=int, default=3,
                       help='Jumlah retry untuk download gagal (default: 3)')
    parser.add_argument('--output', type=str, default='Peraturan-RI-Complete',
                       help='Direktori output (default: Peraturan-RI-Complete)')
    
    # Special modes
    parser.add_argument('--demo', action='store_true',
                       help='Mode demo - tidak download file aktual')
    parser.add_argument('--usage', action='store_true',
                       help='Tampilkan contoh penggunaan')
    
    args = parser.parse_args()
    
    # Show usage examples
    if args.usage:
        print_banner()
        print_usage()
        return
    
    # Validate arguments
    if not any([args.all, args.types, args.recent]):
        print_banner()
        print("❌ ERROR: Pilih salah satu mode download!")
        print("💡 Gunakan --usage untuk melihat contoh penggunaan")
        print("💡 Atau gunakan --all untuk download semua PDF")
        return
    
    print_banner()
    
    # Create config
    config = {
        "base_dir": args.output,
        "demo_mode": args.demo,
        "max_concurrent": args.concurrent,
        "request_delay": args.delay,
        "retry_attempts": args.retry
    }
    
    # Save config to file
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"⚙️  Konfigurasi:")
    print(f"   📁 Output: {args.output}")
    print(f"   🔄 Concurrent: {args.concurrent}")
    print(f"   ⏱️  Delay: {args.delay}s")
    print(f"   🔁 Retry: {args.retry}")
    print(f"   🎭 Demo mode: {'Ya' if args.demo else 'Tidak'}")
    print()
    
    try:
        if args.all:
            print("🚀 Memulai download SEMUA PDF dari peraturan.go.id...")
            print("⚠️  PERINGATAN: Ini akan mendownload ribuan file PDF!")
            print("⚠️  Pastikan koneksi internet stabil dan storage cukup!")
            
            if not args.demo:
                response = input("🤔 Lanjutkan? (ketik 'LANJUTKAN' untuk konfirmasi): ")
                if response != 'LANJUTKAN':
                    print("❌ Download dibatalkan.")
                    return
            
            async with CompletePeraturanScraper(config_path='config.json') as scraper:
                result = await scraper.download_all_pdfs_from_website()
                
        elif args.types:
            print(f"🎯 Mendownload PDF untuk jenis: {', '.join(args.types)}")
            if args.years:
                print(f"📅 Tahun: {', '.join(args.years)}")
            
            result = await download_by_regulation_type(
                regulation_types=args.types,
                years=args.years
            )
            
        elif args.recent:
            print(f"📅 Mendownload peraturan dari {args.recent} hari terakhir...")
            result = await download_recent_regulations(days_back=args.recent)
        
        # Print results
        print("\n" + "=" * 80)
        print("✅ DOWNLOAD SELESAI!")
        print("=" * 80)
        print(f"📊 STATISTIK:")
        print(f"   📄 Halaman peraturan ditemukan: {result.get('total_pages_found', 0):,}")
        print(f"   🔗 Link PDF ditemukan: {result.get('total_pdfs_found', 0):,}")
        print(f"   ✅ PDF berhasil didownload: {result.get('total_downloaded', 0):,}")
        print(f"   ❌ Error: {result.get('total_errors', 0):,}")
        print(f"   ⏱️  Durasi: {result.get('duration_formatted', 'Unknown')}")
        print(f"   📁 Lokasi file: {args.output}")
        
        # Save detailed summary
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f"download_summary_{timestamp}.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"   📋 Summary lengkap: {summary_file}")
        print("=" * 80)
        
        if result.get('total_downloaded', 0) > 0:
            print("🎉 Selamat! Download berhasil diselesaikan.")
        else:
            print("⚠️  Tidak ada file yang berhasil didownload.")
            
    except KeyboardInterrupt:
        print("\n❌ Download dihentikan oleh user.")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        print("📋 Periksa file log untuk detail error.")
    
    print("\n👋 Terima kasih telah menggunakan PDF Downloader!")

if __name__ == "__main__":
    asyncio.run(main())
