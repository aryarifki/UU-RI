#!/usr/bin/env python3
"""
Test script for direct PDF URL functionality in advanced_peraturan_scraper.py
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_peraturan_scraper import AdvancedPeraturanScraper, download_direct_pdfs


def test_url_validation():
    """Test URL validation methods"""
    print("=== Testing URL Validation ===")
    
    scraper = AdvancedPeraturanScraper()
    
    # Test valid direct URLs
    valid_urls = [
        "https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf",
        "https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf",
        "https://peraturan.go.id/files/pp-no-15-tahun-2024.pdf",
        "https://peraturan.go.id/files/perpres-no-10-tahun-2023.pdf"
    ]
    
    # Test invalid URLs
    invalid_urls = [
        "https://example.com/file.pdf",
        "https://peraturan.go.id/search?q=test",
        "https://peraturan.go.id/files/document.doc", 
        "not-a-url",
        ""
    ]
    
    print("Valid URLs:")
    for url in valid_urls:
        is_valid = scraper.is_direct_pdf_url(url)
        print(f"  {'✓' if is_valid else '✗'} {url}")
        if not is_valid:
            print(f"    ERROR: Should be valid!")
    
    print("\nInvalid URLs:")
    for url in invalid_urls:
        is_valid = scraper.is_direct_pdf_url(url)
        print(f"  {'✗' if not is_valid else '✓'} {url}")
        if is_valid:
            print(f"    ERROR: Should be invalid!")
    
    print()


def test_filename_extraction():
    """Test filename extraction from URLs"""
    print("=== Testing Filename Extraction ===")
    
    scraper = AdvancedPeraturanScraper()
    
    test_cases = [
        ("https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf", "UUD No. 1 Tahun 2025.pdf"),
        ("https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf", "UU No. 2 Tahun 2024.pdf"),
        ("https://peraturan.go.id/files/pp-no-15-tahun-2024.pdf", "PP No. 15 Tahun 2024.pdf"),
        ("https://peraturan.go.id/files/perpres-no-10-tahun-2023.pdf", "Perpres No. 10 Tahun 2023.pdf"),
        ("https://peraturan.go.id/files/bad-url", "document.pdf")
    ]
    
    for url, expected in test_cases:
        result = scraper.extract_filename_from_url(url)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {url}")
        print(f"    Expected: {expected}")
        print(f"    Got:      {result}")
        if result != expected:
            print(f"    ERROR: Filename extraction mismatch!")
        print()


def test_regulation_info_parsing():
    """Test regulation information parsing from URLs"""
    print("=== Testing Regulation Info Parsing ===")
    
    scraper = AdvancedPeraturanScraper()
    
    test_cases = [
        ("https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf", {"type": "UUD", "year": "2025", "number": "1"}),
        ("https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf", {"type": "UU", "year": "2024", "number": "2"}),
        ("https://peraturan.go.id/files/pp-no-15-tahun-2024.pdf", {"type": "PP", "year": "2024", "number": "15"}),
        ("https://peraturan.go.id/files/perpres-no-10-tahun-2023.pdf", {"type": "PERPRES", "year": "2023", "number": "10"})
    ]
    
    for url, expected in test_cases:
        result = scraper.parse_regulation_info_from_url(url)
        print(f"  URL: {url}")
        print(f"    Type: {result['type']} (expected: {expected['type']})")
        print(f"    Year: {result['year']} (expected: {expected['year']})")
        print(f"    Number: {result['number']} (expected: {expected['number']})")
        
        success = (result['type'] == expected['type'] and 
                  result['year'] == expected['year'] and 
                  result['number'] == expected['number'])
        print(f"    Status: {'✓' if success else '✗'}")
        print()


async def test_download_demo():
    """Test download functionality in demo mode"""
    print("=== Testing Download in Demo Mode ===")
    
    test_urls = [
        "https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf",
        "https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf"
    ]
    
    async with AdvancedPeraturanScraper() as scraper:
        print("Testing individual download...")
        result = await scraper.download_direct_pdf(test_urls[0])
        print(f"Single download result: {result}")
        print()
        
        print("Testing multiple downloads...")
        result = await scraper.download_from_direct_urls(test_urls)
        print(f"Multiple download result:")
        print(f"  Total provided: {result.get('total_provided', 0)}")
        print(f"  Valid URLs: {result.get('valid_urls', 0)}")
        print(f"  Successful: {result.get('successful_downloads', 0)}")
        print(f"  Failed: {result.get('failed_downloads', 0)}")
        print(f"  Skipped: {result.get('skipped_files', 0)}")
        print()
        
        print("Testing via scrape_regulations method...")
        result = await scraper.scrape_regulations(direct_urls=test_urls)
        print(f"Scrape regulations with direct URLs:")
        print(f"  Mode: {result.get('mode', 'unknown')}")
        print(f"  Downloaded: {result.get('downloaded', 0)}")
        print(f"  Errors: {result.get('errors', 0)}")
        print()


async def test_standalone_function():
    """Test standalone download function"""
    print("=== Testing Standalone Function ===")
    
    test_urls = [
        "https://peraturan.go.id/files/uud-no-1-tahun-2025.pdf",
        "https://peraturan.go.id/files/uu-no-2-tahun-2024.pdf"
    ]
    
    result = await download_direct_pdfs(test_urls)
    print(f"Standalone function result:")
    print(f"  Total provided: {result.get('total_provided', 0)}")
    print(f"  Valid URLs: {result.get('valid_urls', 0)}")
    print(f"  Successful: {result.get('successful_downloads', 0)}")
    print(f"  Failed: {result.get('failed_downloads', 0)}")
    print()


async def main():
    """Run all tests"""
    print("🧪 Testing Direct PDF URL Functionality")
    print("=" * 50)
    
    # Test synchronous functions
    test_url_validation()
    test_filename_extraction()
    test_regulation_info_parsing()
    
    # Test asynchronous functions 
    await test_download_demo()
    await test_standalone_function()
    
    print("✅ All tests completed!")
    print("\nNote: Downloads are in demo mode, so no actual files are downloaded.")
    print("To enable real downloads, set 'demo_mode': false in config.json")


if __name__ == "__main__":
    asyncio.run(main())