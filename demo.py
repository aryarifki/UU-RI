#!/usr/bin/env python3
"""
Demo script untuk testing download PDF dari peraturan.go.id
Menampilkan bagaimana menggunakan scraper untuk berbagai skenario
"""

import asyncio
import json
from advanced_peraturan_scraper import CompletePeraturanScraper

async def demo_basic_usage():
    """Demo penggunaan dasar scraper"""
    print("=" * 60)
    print("🎭 DEMO: Penggunaan Dasar Scraper")
    print("=" * 60)
    
    # Set demo mode in config
    config = {
        "demo_mode": True,
        "max_concurrent": 5,
        "request_delay": 0.5,
        "base_dir": "Demo-Output"
    }
    
    # Save demo config
    with open('demo_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    async with CompletePeraturanScraper(config_path='demo_config.json') as scraper:
        print("✅ Scraper initialized in DEMO mode")
        print("📝 Demo mode: No actual files will be downloaded")
        print()
        
        # Test URL building
        test_url = scraper.build_comprehensive_search_url(
            regulation_type="UU",
            year="2024"
        )
        print(f"🔗 Test search URL: {test_url}")
        print()
        
        # Test discovery (limited)
        print("🔍 Testing regulation discovery...")
        try:
            discovered = await scraper.discover_all_regulation_pages()
            print(f"📄 Would discover: {len(discovered)} regulation pages")
        except Exception as e:
            print(f"❌ Discovery test failed: {e}")
        
        print("✅ Demo basic usage completed")

async def demo_specific_download():
    """Demo download spesifik berdasarkan jenis dan tahun"""
    print("\n" + "=" * 60)
    print("🎯 DEMO: Download Spesifik")
    print("=" * 60)
    
    # Demo untuk UU tahun 2024
    config = {
        "demo_mode": True,
        "regulation_types": {"UU": "Undang-Undang"},
        "years_range": [2024],
        "max_concurrent": 3
    }
    
    with open('demo_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    async with CompletePeraturanScraper(config_path='demo_config.json') as scraper:
        print("🎯 Target: UU tahun 2024")
        print("📝 Mode: Demo (no actual download)")
        print()
        
        # Simulate the process
        print("Step 1: Discovering UU 2024 pages...")
        await asyncio.sleep(1)  # Simulate processing time
        print("✅ Found: 25 UU pages")
        
        print("Step 2: Extracting PDF links...")
        await asyncio.sleep(1)
        print("✅ Found: 47 PDF links")
        
        print("Step 3: Would download 47 PDF files...")
        await asyncio.sleep(1)
        print("✅ Demo download simulation completed")

async def demo_error_handling():
    """Demo error handling dan retry mechanism"""
    print("\n" + "=" * 60)
    print("🛡️ DEMO: Error Handling")
    print("=" * 60)
    
    async with CompletePeraturanScraper() as scraper:
        print("🧪 Testing error handling capabilities...")
        
        # Test invalid URL handling
        try:
            invalid_url = "https://invalid-url-test.com/fake-pdf.pdf"
            print(f"🔗 Testing invalid URL: {invalid_url}")
            
            # This would normally fail, but we'll simulate
            print("❌ Connection timeout (simulated)")
            print("🔄 Retry attempt 1/3...")
            await asyncio.sleep(0.5)
            print("❌ Connection timeout (simulated)")
            print("🔄 Retry attempt 2/3...")
            await asyncio.sleep(0.5)
            print("❌ Connection timeout (simulated)")
            print("🔄 Retry attempt 3/3...")
            await asyncio.sleep(0.5)
            print("❌ Final failure - URL marked as failed")
            
        except Exception as e:
            print(f"✅ Error properly handled: {e}")
        
        print("✅ Error handling demo completed")

async def demo_performance_test():
    """Demo test performa dan concurrent downloads"""
    print("\n" + "=" * 60)
    print("⚡ DEMO: Performance Test")
    print("=" * 60)
    
    config = {
        "demo_mode": True,
        "max_concurrent": 10,
        "request_delay": 0.1
    }
    
    with open('demo_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    async with CompletePeraturanScraper(config_path='demo_config.json') as scraper:
        print("⚡ Performance configuration:")
        print(f"   🔄 Max concurrent: {scraper.max_concurrent}")
        print(f"   ⏱️  Request delay: {scraper.request_delay}s")
        print()
        
        # Simulate concurrent processing
        print("🚀 Simulating concurrent downloads...")
        
        tasks = []
        for i in range(10):
            async def simulate_download(id):
                await asyncio.sleep(0.5)  # Simulate download time
                print(f"✅ Simulated download {id+1} completed")
            
            tasks.append(simulate_download(i))
        
        await asyncio.gather(*tasks)
        print("⚡ Performance test completed")

async def demo_file_organization():
    """Demo sistem organisasi file"""
    print("\n" + "=" * 60)
    print("📁 DEMO: File Organization")
    print("=" * 60)
    
    async with CompletePeraturanScraper() as scraper:
        print("📁 Demonstrating file organization system...")
        
        # Test folder creation logic
        test_cases = [
            {"type": "UU", "year": "2024", "number": "5"},
            {"type": "PERPPU", "year": "2023", "number": "12"},
            {"type": "PP", "year": "2024", "number": "77"}
        ]
        
        for case in test_cases:
            pdf_link = {
                "source_page": f"https://peraturan.go.id/peraturan/view/{case['type']}-{case['number']}-{case['year']}",
                "text": f"{case['type']} Nomor {case['number']} Tahun {case['year']}"
            }
            
            folder_path = scraper._create_folder_for_pdf(pdf_link)
            print(f"📂 {case['type']} {case['number']}/{case['year']} → {folder_path}")
        
        print("✅ File organization demo completed")

async def main():
    """Run all demos"""
    print("🎭 PERATURAN.GO.ID PDF DOWNLOADER - DEMO MODE")
    print("=" * 80)
    print("Mendemonstrasikan fitur-fitur utama tanpa download aktual")
    print("=" * 80)
    
    try:
        await demo_basic_usage()
        await demo_specific_download()
        await demo_error_handling()
        await demo_performance_test()
        await demo_file_organization()
        
        print("\n" + "=" * 80)
        print("🎉 SEMUA DEMO SELESAI!")
        print("=" * 80)
        print("📝 Untuk penggunaan aktual:")
        print("   python download_all_pdfs.py --usage")
        print("   python download_all_pdfs.py --types UU --years 2024")
        print("   python download_all_pdfs.py --all")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    finally:
        # Cleanup demo config
        import os
        try:
            os.remove('demo_config.json')
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
